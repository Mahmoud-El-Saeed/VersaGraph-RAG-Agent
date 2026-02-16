import os
from fastapi import APIRouter , UploadFile , status , Request
from fastapi.responses import JSONResponse
from src.app.utilities.process_file import FileProcessor , FILES_DIR_PATH
from src.app.utilities.ProcessEnum import ProcessSignal
from src.app.utilities.loader import Loader
from src.app.utilities.splitter import TextSplitter
import logging


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/data",
    tags=["data"]
)

@router.get("/")
async def hello_world():
    return JSONResponse(content={"message": "Hello World!"}, status_code=status.HTTP_200_OK)

@router.post("/upload")
async def upload_file(file: UploadFile):
    
    file_processor = FileProcessor(file)
    
    is_valid , signal = file_processor.validate_uploaded_file()
    
    if not is_valid:
        return JSONResponse(content={"message": signal}, status_code=status.HTTP_400_BAD_REQUEST)
    
    
    file_path, file_id = file_processor.generate_unique_filepath()
    
    try:
        file_path = await file_processor.save_uploaded_file(file_path)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return JSONResponse(content={"message": ProcessSignal.FILE_UPDLOAD_FAILED.value}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
    return JSONResponse(content={"message": ProcessSignal.FILE_UPLOAD_SUCCESS.value,
                                "file id": file_id}, status_code=status.HTTP_200_OK)

@router.post("/process")
async def process_file(request: Request,file_id: str):
    
    if not FileProcessor.is_file_exists(file_id):
        return JSONResponse(content={"message": ProcessSignal.NO_FILE_FOUND.value}, status_code=status.HTTP_404_NOT_FOUND)
    
    file_extension = file_id.split(".")[-1].lower()
    file_path = os.path.join(FILES_DIR_PATH, file_id)
    loader = Loader(file_extension=file_extension)
    try:
        documents = loader.load(file_path)
        page_contents, metadatas = FileProcessor.return_metadatas_and_page_content(documents)
    except Exception as e:
        logger.error(f"Error loading file: {str(e)}")
        return JSONResponse(content={"message": ProcessSignal.FILE_PROCESSING_FAILED.value}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    splitter = TextSplitter()
    
    chunked_documents = splitter.split_texts(page_contents, metadatas)
    
    
    return JSONResponse(content={
        "message": ProcessSignal.FILE_PROCESSING_SUCCESS.value,
        "chunks length": len(chunked_documents),
        "Chunks": chunked_documents[0].page_content,
        'Metadatas': chunked_documents[0].metadata
    }, status_code=status.HTTP_200_OK)