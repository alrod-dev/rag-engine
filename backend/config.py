from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_title: str = "RAG Engine API"
    api_version: str = "1.0.0"
    debug: bool = False

    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-large"
    temperature: float = 0.7
    max_tokens: int = 2048

    # Pinecone Configuration
    pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY", None)
    pinecone_environment: Optional[str] = os.getenv("PINECONE_ENVIRONMENT", None)
    pinecone_index: str = "rag-engine"
    use_pinecone: bool = False  # Use Pinecone if credentials provided

    # Vector Search Configuration
    embedding_dimension: int = 3072  # text-embedding-3-large dimension
    similarity_top_k: int = 5
    min_similarity_score: float = 0.3
    use_hybrid_search: bool = True
    bm25_weight: float = 0.3
    semantic_weight: float = 0.7

    # Document Processing
    max_file_size_mb: int = 100
    allowed_file_types: list = [".pdf", ".docx", ".txt", ".csv"]

    # Chunking Strategy
    chunk_size: int = 512
    chunk_overlap: int = 100
    chunking_strategy: str = "recursive"  # fixed, recursive, or semantic

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    database_url: Optional[str] = os.getenv("DATABASE_URL", None)

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
