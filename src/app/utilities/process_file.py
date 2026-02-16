import os
import re
from fastapi import UploadFile
import aiofiles
from .ProcessEnum import ProcessSignal
from src.helper.config import get_settings, Settings
import string
import random

SRC_DIR_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) 
FILES_DIR_PATH = os.path.join(SRC_DIR_PATH, "data", "files")

class FileProcessor:
    
    def __init__(self,file: UploadFile):
        self.file = file
        self.setttings: Settings = get_settings()
        self.file_extension = self.file.filename.split(".")[-1].lower()
        self.src_dir = SRC_DIR_PATH
        self.files_dir = FILES_DIR_PATH
        os.makedirs(self.files_dir, exist_ok=True)
        
    def validate_uploaded_file(self) -> tuple[bool, str]:
        """Validate the uploaded file based on its presence and allowed content types."""
        
        if self.file.content_type not in self.setttings.FILE_ALLOWED_TYPES:
            return False, ProcessSignal.FILE_TYPE_NOT_SUPPORTED.value
        if self.file.size > self.setttings.FILE_MAX_SIZE_MB * 1024 * 1024:
            return False, ProcessSignal.FILE_SIZE_EXCEEDED.value
        
        return True, ProcessSignal.FILE_VALIDATE_SUCCESS.value
    
    def generate_random_string(self,length:int = 12):
        return ''.join(random.choices(string.ascii_lowercase+string.digits,k=length))
    def get_clean_filename(self,orignal_filename:str):
        cleaned_filename = re.sub(r'[^\w.]','',orignal_filename.strip()).replace(' ','_')
        
        return cleaned_filename

    def generate_unique_filepath(self) -> tuple[str, str]:
        """Generates a unique file path for the uploaded file to prevent overwriting existing files."""
        random_key = self.generate_random_string() 
        cleaned_filename = self.get_clean_filename(self.file.filename)
        new_file_path = os.path.join(
            self.files_dir,
            random_key+"_"+cleaned_filename
        )

        while os.path.exists(new_file_path):
            random_key = self.generate_random_string() 
            new_file_path = os.path.join(
                self.files_dir,
                random_key+"_"+cleaned_filename
            )      
            
        return new_file_path , random_key+"_"+cleaned_filename
    

    
    async def save_uploaded_file(self, file_path: str) -> str:
        """Saves the uploaded file to the specified file path asynchronously."""
        await self.file.seek(0)
        
        async with aiofiles.open(file_path, "wb") as f:
            while content := await self.file.read(self.setttings.FILE_UPLOAD_CHUNK_SIZE):
                await f.write(content)

        
        return file_path
    
    @classmethod 
    def is_file_exists(cls, file_id: str) -> bool:
        """Checks if a file with the given file_id exists in the files directory."""
        file_path = os.path.join(FILES_DIR_PATH, file_id)
        return os.path.exists(file_path)
    
    @classmethod
    def return_metadatas_and_page_content(cls, documents: list) -> tuple[list[str], list[dict]]:
        """Extracts page contents and metadatas from a list of documents."""
        page_contents = [x.page_content for x in documents]
        metadatas = [x.metadata for x in documents]
        
        return page_contents, metadatas