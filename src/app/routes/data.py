import os
import uuid
from fastapi import APIRouter, UploadFile, status, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import logging
from src.app.utilities.process_file import FileProcessor, FILES_DIR_PATH
from src.app.utilities.ProcessEnum import ProcessSignal
from src.app.utilities.loader import Loader
from src.app.utilities.splitter import TextSplitter
from src.app.database.mongo_db import FileModel, ChatModel
from src.app.database.mongo_db.schema import File, Chat
from src.app.database.mongo_db.DataBaseEnum import FileStatus
from src.app.routes.schema import ProcessRequest
from src.app.database.qdrantdb.QdrantdbModel import QdrantdbModel
from src.app.utilities.embeder import Embeder
from src.helper.config import get_settings , Settings

logger = logging.getLogger('uvicorn.error')

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/")
async def hello_world():
    return JSONResponse(
        content={"message": "Hello World!"}, status_code=status.HTTP_200_OK
    )


@router.post("/upload")
async def upload_file(request: Request, file: UploadFile, chat_id: str):

    mongo_client = request.app.db_client
    chat_model: ChatModel = await ChatModel.create_instance(mongo_client)
    file_model: FileModel = await FileModel.create_instance(mongo_client)

    file_processor = FileProcessor(file)

    is_valid, signal = file_processor.validate_uploaded_file()

    if not is_valid:
        return JSONResponse(
            content={"message": signal}, status_code=status.HTTP_400_BAD_REQUEST
        )

    file_path, file_id = file_processor.generate_unique_filepath()

    try:
        file_path = await file_processor.save_uploaded_file(file_path)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return JSONResponse(
            content={"message": ProcessSignal.FILE_UPDLOAD_FAILED.value},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not await chat_model.is_chat_exists(chat_id):
        _ = await chat_model.insert_chat(
            Chat(chat_id=chat_id, created_at=datetime.now(timezone.utc))
        )
    file_doc = File(
        file_id=file_id,
        chat_id=chat_id,
        original_filename=file.filename,
        file_path=file_path,
        status=FileStatus.UPLOADED.value,
        uploaded_at=datetime.now(timezone.utc),
    )

    try:
        file_doc = await file_model.insert_file(file_doc)
    except Exception as e:
        logger.error(f"Error inserting file document: {str(e)}")
        return JSONResponse(
            content={"message": ProcessSignal.FILE_UPDLOAD_FAILED.value},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return JSONResponse(
        content={
            "message": ProcessSignal.FILE_UPLOAD_SUCCESS.value,
            "file id": file_doc.file_id,
        },
        status_code=status.HTTP_200_OK,
    )


@router.post("/process")
async def process_file(request: Request, process_request: ProcessRequest):

    mongo_client = request.app.db_client
    file_model: FileModel = await FileModel.create_instance(mongo_client)
    
    qdrant_client = request.app.qdrant_client
    qdrant_model = QdrantdbModel(qdrant_client=qdrant_client)
    settings: Settings = get_settings()
    embeder = Embeder()
    
    chat_id = process_request.chat_id
    file_id = process_request.file_id
    
    file_doc = await file_model.find_file_by_id(file_id)
    if not FileProcessor.is_file_exists(file_id) or not file_doc:
        return JSONResponse(
            content={"message": ProcessSignal.NO_FILE_FOUND.value},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if file_doc.status == FileStatus.INDEXED.value and file_doc.chat_id == chat_id:
        return JSONResponse(
            content={"message": ProcessSignal.FILE_ALREADY_PROCESSED.value},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    file_extension = file_id.split(".")[-1].lower()
    file_path = os.path.join(FILES_DIR_PATH, file_id)
    loader = Loader(file_extension=file_extension)
    await file_model.update_file_status_by_id(file_id, FileStatus.PROCESSING.value)
    
    try:
        documents = loader.load(file_path)
        page_contents, metadatas = FileProcessor.return_metadatas_and_page_content(
            documents=documents
        )
        splitter = TextSplitter()
        chunked_documents = splitter.split_texts(page_contents, metadatas)
        embeddings = embeder.embed_chunks([doc.page_content for doc in chunked_documents])
        payloads = [
            {
                "chat_id": chat_id,
                "metadata": doc.metadata,
                "chunk_content": doc.page_content
            }
            for doc in chunked_documents
        ]
        await qdrant_model.create_collection_if_not_exists(
            collection_name=settings.COLLECTION_APP_NAME,
            vector_size=settings.EMBED_MODEL_SIZE 
        )
        await qdrant_model.upsert_points(
            collection_name=settings.COLLECTION_APP_NAME,
            vectors=embeddings,
            payloads=payloads,
            ids=[str(uuid.uuid4()) for _ in range(len(chunked_documents))]
            
        )
        
        
        await file_model.update_file_status_by_id(file_id, FileStatus.INDEXED.value)
        

        
    except Exception as e:
        await file_model.update_file_status_by_id(file_id, FileStatus.FAILED.value)
        logger.error(f"Error processing file: {str(e)}")
        return JSONResponse(
            content={"message": ProcessSignal.FILE_PROCESSING_FAILED.value},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )




    return JSONResponse(
        content={
            "message": ProcessSignal.FILE_PROCESSING_SUCCESS.value,
            "file_id": file_id
        },
        status_code=status.HTTP_200_OK,
    )
