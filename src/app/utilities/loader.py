from langchain_community.document_loaders import PyMuPDFLoader , Docx2txtLoader, TextLoader 

class Loader:
    def __init__(self, file_extension: str):
        self.file_extension = file_extension

    def load(self,file_path: str) -> list:
        """ Loads the file using the appropriate loader."""
        if self.file_extension == "pdf":
            loader = PyMuPDFLoader(file_path)
        elif self.file_extension == "docx":
            loader = Docx2txtLoader(file_path)
        elif self.file_extension == "txt":
            loader = TextLoader(file_path)
        else:
            return None
        return loader.load()
    
    