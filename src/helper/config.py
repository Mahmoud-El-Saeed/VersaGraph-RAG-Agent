from pydantic_settings import BaseSettings ,SettingsConfigDict

class Settings(BaseSettings):
    
    # File Config
    FILE_ALLOWED_TYPES: list[str]
    FILE_MAX_SIZE_MB: int
    FILE_UPLOAD_CHUNK_SIZE: int
    
    # Chunk Config
    CHUNK_SIZE: int
    CHUNK_OVERLAP: int
    
    # Vector Store Config
    VECTOR_STORE_TYPE: str
    EMBEDDING_MODEL: str
    EMBED_MODEL_SIZE: int
    DISTANCE_METRIC: str
    URL_QDRANT: str
    QDRANT_API_KEY: str
    COLLECTION_APP_NAME: str
    COLLECTION_CHATS_HISTORY_NAME: str
    
    # MongoDB Config
    MONGODB_URL: str
    MONGOBD_USERNAME: str
    MONGODB_PASSWORD: str
    MONGODB_DATABASE: str
    
    
    # LLM Config 
    LLM_PROVIDER: str
    LLM_MODEL: str
    API_KEY_GROQ: str
    API_URL_LLM: str # Use it if you want to run ollama
    LLM_TEMPERATURE: float
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

def get_settings():
    return Settings()

if __name__ == "__main__":
    settings = get_settings()
    print(settings)