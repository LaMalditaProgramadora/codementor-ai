from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CodeMentor AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://codementor_user:codementor_pass@localhost:5432/codementor"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_SUBMISSIONS: str = "submissions"
    MINIO_BUCKET_VIDEOS: str = "videos"
    MINIO_USE_SSL: bool = False
    
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:70b"
    OLLAMA_TIMEOUT: int = 6000
    
    # CodeBERT
    CODEBERT_MODEL: str = "microsoft/codebert-base"
    SIMILARITY_THRESHOLD: float = 0.85
    
    # Whisper
    WHISPER_MODEL: str = "base"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
