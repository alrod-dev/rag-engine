from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadata about a document."""
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    num_pages: Optional[int] = None
    num_chunks: int = 0
    source_url: Optional[str] = None
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Document representation."""
    document_id: str
    metadata: DocumentMetadata
    chunk_count: int
    is_indexed: bool = False


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    documents: List[Document]
    total_count: int


class DeleteDocumentResponse(BaseModel):
    """Response for document deletion."""
    document_id: str
    deleted: bool
    message: str


class TextChunk(BaseModel):
    """A chunk of text with metadata."""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_count: int


class EmbeddingResponse(BaseModel):
    """Response containing embeddings."""
    chunk_id: str
    embedding: List[float]
    model: str


class SearchQuery(BaseModel):
    """Query for searching documents."""
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    use_hybrid_search: bool = True
    include_sources: bool = True


class SourcePassage(BaseModel):
    """A source passage from a document."""
    document_id: str
    filename: str
    content: str
    chunk_index: int
    similarity_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationRequest(BaseModel):
    """Request for generation with RAG."""
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    use_hybrid_search: bool = True
    include_sources: bool = True
    stream: bool = False
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class GenerationResponse(BaseModel):
    """Response from generation endpoint."""
    query: str
    answer: str
    sources: List[SourcePassage]
    model_used: str
    total_tokens: Optional[int] = None


class ChunkingConfig(BaseModel):
    """Configuration for chunking."""
    strategy: str = Field(default="recursive")
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=100)
    separator: Optional[str] = None


class ChunkVisualizationResponse(BaseModel):
    """Response for chunk visualization."""
    document_id: str
    filename: str
    total_chunks: int
    chunks: List[TextChunk]
    chunking_config: ChunkingConfig


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    status_code: int
    timestamp: datetime


class QueryMetrics(BaseModel):
    """Metrics for a query."""
    query: str
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    num_sources: int
    tokens_used: int
