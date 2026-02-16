from langchain_text_splitters import RecursiveCharacterTextSplitter 
from src.helper.config import get_settings , Settings

class TextSplitter:
    
    def __init__(self):
        self.settings: Settings = get_settings()
        self.chunk_size = self.settings.CHUNK_SIZE
        self.chunk_overlap = self.settings.CHUNK_OVERLAP
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )    
    
    def split_texts(self, texts: list[str], metadatas: list[dict]) -> list[dict]:
        documents = self.splitter.create_documents(texts=texts, metadatas=metadatas)
        return documents

    