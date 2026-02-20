import os
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, status, Request, Form
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import logging
from src.app.utilities.process_file import FileProcessor, FILES_DIR_PATH
from src.app.utilities.ProcessEnum import ProcessSignal
from src.app.utilities.loader import Loader
from src.app.utilities.splitter import TextSplitter
from src.app.database.mongo_db import FileModel, ChatModel
from src.app.database.mongo_db.schema import File
from src.app.database.mongo_db.DataBaseEnum import FileStatus
from src.app.routes.schema import ProcessRequest
from src.app.database.qdrantdb.QdrantdbModel import QdrantdbModel
from src.app.utilities.embeder import Embeder
from src.helper.config import get_settings, Settings

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/")
async def hello_world():
    return JSONResponse(
        content={"message": "Hello World!"}, status_code=status.HTTP_200_OK
    )


@router.post("/upload")
async def upload_files(
    request: Request,
    files: List[UploadFile],
    chat_id: str = Form(...),
    persona_name: str = Form("General Assistant"),
    persona_instructions: str = Form("You are a helpful assistant."),
):
    """
    Handles multiple file uploads and initializes the chat if it's new.
    """
    mongo_client = request.app.db_client
    chat_model: ChatModel = await ChatModel.create_instance(mongo_client)
    file_model: FileModel = await FileModel.create_instance(mongo_client)

    await chat_model.initialize_chat(
        chat_id=chat_id,
        persona_name=persona_name,
        persona_instructions=persona_instructions,
    )

    uploaded_files_info = []
    failed_files = []

    for file in files:
        file_processor = FileProcessor(file)
        is_valid, signal = file_processor.validate_uploaded_file()

        if not is_valid:
            failed_files.append({"filename": file.filename, "reason": signal})
            continue

        file_path, file_id = file_processor.generate_unique_filepath()

        try:
            file_path = await file_processor.save_uploaded_file(file_path)

            file_doc = File(
                file_id=file_id,
                chat_id=chat_id,
                original_filename=file.filename,
                file_path=file_path,
                status=FileStatus.UPLOADED.value,
                uploaded_at=datetime.now(timezone.utc),
            )
            await file_model.insert_file(file_doc)

            await chat_model.add_file_to_chat(chat_id, file_id, file.filename)

            uploaded_files_info.append({"filename": file.filename, "file_id": file_id})

        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            failed_files.append({"filename": file.filename, "reason": "Server Error"})

    if not uploaded_files_info:
        return JSONResponse(
            content={"message": "All uploads failed.", "errors": failed_files},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return JSONResponse(
        content={
            "message": f"Successfully uploaded {len(uploaded_files_info)} files.",
            "uploaded": uploaded_files_info,
            "failed": failed_files,
        },
        status_code=status.HTTP_200_OK,
    )


@router.post("/process")
async def process_chat_files(request: Request, process_request: ProcessRequest):
    """
    Finds all 'pending' files for a given chat_id and processes them.
    Skips files that are already indexed.
    """
    chat_id = process_request.chat_id

    mongo_client = request.app.db_client
    chat_model: ChatModel = await ChatModel.create_instance(mongo_client)
    file_model: FileModel = await FileModel.create_instance(mongo_client)

    qdrant_client = request.app.qdrant_client
    qdrant_model = QdrantdbModel(qdrant_client=qdrant_client)
    settings: Settings = get_settings()
    embeder = Embeder()

    pending_files = await chat_model.get_pending_files(chat_id)

    if not pending_files:
        return JSONResponse(
            content={"message": "No new files to process for this chat."},
            status_code=status.HTTP_200_OK,
        )

    processed_ids = []
    failed_ids = []

    # 2. Process each pending file
    for chat_file in pending_files:
        file_id = chat_file.file_id

        # Verify file exists globally
        file_doc = await file_model.find_file_by_id(file_id)
        if not FileProcessor.is_file_exists(file_id) or not file_doc:
            failed_ids.append(
                {"file_id": file_id, "reason": ProcessSignal.NO_FILE_FOUND.value}
            )
            continue

        file_extension = file_id.split(".")[-1].lower()
        file_path = os.path.join(FILES_DIR_PATH, file_id)
        loader = Loader(file_extension=file_extension)

        # Update status to PROCESSING in both collections
        await chat_model.update_chat_file_status(
            chat_id, file_id, FileStatus.PROCESSING.value
        )
        await file_model.update_file_status_by_id(file_id, FileStatus.PROCESSING.value)

        try:
            # Extract and chunk
            documents = loader.load(file_path)
            page_contents, metadatas = FileProcessor.return_metadatas_and_page_content(
                documents
            )
            splitter = TextSplitter()
            chunked_documents = splitter.split_texts(page_contents, metadatas)

            # Embed
            embeddings = embeder.embed_chunks(
                [doc.page_content for doc in chunked_documents]
            )

            # Prepare payloads for Qdrant
            payloads = [
                {
                    "chat_id": chat_id,
                    "metadata": doc.metadata,
                    "chunk_content": doc.page_content,
                    "original_filename": file_doc.original_filename,
                    "page_number": doc.metadata.get("page", None),
                }
                for doc in chunked_documents
            ]

            # Upsert to Vector DB
            await qdrant_model.upsert_points(
                collection_name=settings.COLLECTION_APP_NAME,
                vectors=embeddings,
                payloads=payloads,
                ids=[str(uuid.uuid4()) for _ in range(len(chunked_documents))],
            )

            # Update status to INDEXED
            await chat_model.update_chat_file_status(
                chat_id, file_id, FileStatus.INDEXED.value
            )
            await file_model.update_file_status_by_id(file_id, FileStatus.INDEXED.value)

            processed_ids.append(file_id)

        except Exception as e:
            logger.error(f"Error processing file {file_id}: {str(e)}")
            # Mark as FAILED
            await chat_model.update_chat_file_status(
                chat_id, file_id, FileStatus.FAILED.value
            )
            await file_model.update_file_status_by_id(file_id, FileStatus.FAILED.value)
            failed_ids.append({"file_id": file_id, "reason": str(e)})

    return JSONResponse(
        content={
            "message": f"Processing complete. Success: {len(processed_ids)}, Failed: {len(failed_ids)}",
            "processed": processed_ids,
            "failed": failed_ids,
        },
        status_code=status.HTTP_200_OK,
    )
