from langchain_ollama import OllamaEmbeddings
from src.helper.config import get_settings, Settings

class Embeder:
    def __init__(self):
        settings: Settings = get_settings()
        self.model_name = settings.EMBEDDING_MODEL
        embed_kwargs = {"model": self.model_name}
        if settings.API_URL_LLM:
            embed_kwargs["base_url"] = settings.API_URL_LLM
        self.embeddings = OllamaEmbeddings(**embed_kwargs)
        self.embed_size = settings.EMBED_MODEL_SIZE
    
    def embed_chunks(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_text(self, query: str) -> list[float]:
        return self.embeddings.embed_query(query)





