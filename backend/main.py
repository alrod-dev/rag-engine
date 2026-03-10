"""FastAPI application for RAG Engine."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from backend.config import settings
from backend.services.ingestion import DocumentIngestionPipeline
from backend.services.embeddings import get_hybrid_embedding_provider
from backend.services.retrieval import HybridRetriever, VectorStore
from backend.services.generation import get_generator
from backend.routers import documents, query

# Setup logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize services
def init_services():
    """Initialize all services."""
    logger.info("Initializing RAG Engine services...")

    # Initialize ingestion pipeline
    ingestion_pipeline = DocumentIngestionPipeline(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        chunking_strategy=settings.chunking_strategy,
    )
    logger.info(f"Ingestion pipeline initialized with {settings.chunking_strategy} strategy")

    # Initialize embedding provider
    embedding_provider = get_hybrid_embedding_provider()
    logger.info("Embedding provider initialized")

    # Initialize vector store
    vector_store = VectorStore()
    logger.info("Vector store initialized")

    # Initialize retriever
    hybrid_retriever = HybridRetriever(embedding_provider, vector_store)
    logger.info("Hybrid retriever initialized")

    # Initialize generator
    generator = get_generator(use_openai=bool(settings.openai_api_key))
    logger.info(f"Generator initialized: {type(generator).__name__}")

    return {
        "ingestion_pipeline": ingestion_pipeline,
        "embedding_provider": embedding_provider,
        "vector_store": vector_store,
        "hybrid_retriever": hybrid_retriever,
        "generator": generator,
    }


# Global services
_services = None


def get_services():
    """Get initialized services."""
    global _services
    if _services is None:
        _services = init_services()
    return _services


# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    services = get_services()

    # Register routers with dependencies
    documents.init_document_router(
        services["ingestion_pipeline"],
        services["vector_store"],
        services["embedding_provider"],
    )

    query.init_query_router(
        services["hybrid_retriever"],
        services["generator"],
    )

    logger.info("RAG Engine started successfully")


# Include routers
app.include_router(documents.router)
app.include_router(query.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "RAG Engine API",
        "version": settings.api_version,
        "description": "Document Intelligence RAG System",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    services = get_services()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ingestion": "ready",
            "embeddings": "ready",
            "retrieval": "ready",
            "generation": "ready",
        },
        "configuration": {
            "chunking_strategy": settings.chunking_strategy,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "embedding_dimension": settings.embedding_dimension,
            "top_k": settings.similarity_top_k,
            "min_similarity": settings.min_similarity_score,
            "hybrid_search": settings.use_hybrid_search,
        },
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError."""
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input", "message": str(exc)},
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    """Handle RuntimeError."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
