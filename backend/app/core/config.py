from pydantic_settings import BaseSettings
from typing import Literal
import os


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    APP_NAME: str = "Cortex Ingestion Pipeline"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    DATABASE_URL: str = "postgresql://cortex:cortex@localhost:5432/cortex_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    CHROMA_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "cortex_documents"

    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 100
    MIN_CHUNK_LENGTH: int = 50

    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "txt", "docx", "md"]
    UPLOAD_DIR: str = "./data/uploads"

    TOKENIZER_NAME: str = "cl100k_base"

    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
