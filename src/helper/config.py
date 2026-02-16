from pydantic_settings import BaseSettings ,SettingsConfigDict

class Settings(BaseSettings):
    
    FILE_ALLOWED_TYPES: list[str]
    FILE_MAX_SIZE_MB: int
    FILE_UPLOAD_CHUNK_SIZE: int
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

def get_settings():
    return Settings()

if __name__ == "__main__":
    settings = get_settings()
    print(settings)