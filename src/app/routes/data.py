from fastapi import APIRouter , Depends , UploadFile , status , Request
from fastapi.responses import JSONResponse
from src.app.utilities import FileProcessor
from src.app.utilities.ProcessEnum import ProcessSignal

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
    
    
    file_path, unique_filename = file_processor.generate_unique_filepath()
    
    try:
        file_path = await file_processor.save_uploaded_file(file_path)
    except Exception as e:
        return JSONResponse(content={"message": f"Error saving file: {str(e)}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
    return JSONResponse(content={"message": ProcessSignal.FILE_UPLOAD_SUCCESS.value}, status_code=status.HTTP_200_OK)