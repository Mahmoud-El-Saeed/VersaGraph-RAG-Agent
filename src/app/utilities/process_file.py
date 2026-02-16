import os
import re
from fastapi import UploadFile
import aiofiles
from .ProcessEnum import ProcessSignal
from src.helper.config import get_settings, Settings
import string
import random

class FileProcessor:
    
    def __init__(self,file: UploadFile):
        self.file = file
        self.setttings: Settings = get_settings()
        self.file_extension = self.file.filename.split(".")[-1].lower()
        self.src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.files_dir = os.path.join(self.src_dir, "data", "files")
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
        await self.file.seek(0)
        
        async with aiofiles.open(file_path, "wb") as f:
            while content := await self.file.read(self.setttings.FILE_UPLOAD_CHUNK_SIZE):
                await f.write(content)

        
        return file_path
    
    