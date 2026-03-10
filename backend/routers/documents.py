"""Document management routes."""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List
import logging

from backend.models.schemas import DocumentListResponse, Document, DeleteDocumentResponse, DocumentMetadata
from backend.services.ingestion import DocumentIngestionPipeline
from backend.services.embeddings import get_embedding_provider
from backend.services.retrieval import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Global state (in production, use a real database)
ingestion_pipeline: DocumentIngestionPipeline = None
vector_store: VectorStore = None
embedding_provider = None
documents_metadata: dict = {}


def init_document_router(pipeline: DocumentIngestionPipeline, store: VectorStore, embeddings):
    """Initialize router with dependencies."""
    global ingestion_pipeline, vector_store, embedding_provider
    ingestion_pipeline = pipeline
    vector_store = store
    embedding_provider = embeddings


@router.post("/upload", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document.

    Args:
        file: File to upload

    Returns:
        Document metadata and ID
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Check file type
        file_ext = "." + file.filename.split(".")[-1].lower()
        allowed_extensions = [".pdf", ".docx", ".txt", ".csv"]

        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported")

        # Ingest document
        file_content = await file.read()
        from io import BytesIO

        file_obj = BytesIO(file_content)
        document_id, chunks, metadata = ingestion_pipeline.ingest_file(file_obj, file.filename)

        # Generate embeddings
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = embedding_provider.embed_texts(chunk_texts)

        # Store in vector store
        vector_store.add_chunks(chunks, embeddings)

        # Store metadata
        documents_metadata[document_id] = metadata

        logger.info(f"Uploaded document {document_id} with {len(chunks)} chunks")

        return {
            "document_id": document_id,
            "filename": metadata.filename,
            "num_chunks": metadata.num_chunks,
            "file_size": metadata.file_size,
            "message": "Document uploaded and indexed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents."""
    documents = []

    for doc_id, metadata in documents_metadata.items():
        doc = Document(
            document_id=doc_id,
            metadata=metadata,
            chunk_count=metadata.num_chunks,
            is_indexed=True,
        )
        documents.append(doc)

    return DocumentListResponse(documents=documents, total_count=len(documents))


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document metadata."""
    if document_id not in documents_metadata:
        raise HTTPException(status_code=404, detail="Document not found")

    metadata = documents_metadata[document_id]
    chunks = vector_store.get_document_chunks(document_id)

    return {
        "document_id": document_id,
        "metadata": metadata,
        "num_chunks": len(chunks),
        "is_indexed": True,
    }


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(document_id: str):
    """Delete a document and its chunks."""
    if document_id not in documents_metadata:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Delete from vector store
        vector_store.delete_document(document_id)

        # Delete metadata
        del documents_metadata[document_id]

        logger.info(f"Deleted document {document_id}")

        return DeleteDocumentResponse(
            document_id=document_id,
            deleted=True,
            message="Document deleted successfully",
        )

    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@router.post("/chunks/config")
async def update_chunking_config(config: dict):
    """Update chunking configuration."""
    try:
        strategy = config.get("strategy", "recursive")
        chunk_size = config.get("chunk_size", 512)
        chunk_overlap = config.get("chunk_overlap", 100)

        ingestion_pipeline.update_chunking_config(chunk_size, chunk_overlap, strategy)

        return {
            "message": "Chunking configuration updated",
            "config": ingestion_pipeline.get_chunking_config(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks/config")
async def get_chunking_config():
    """Get current chunking configuration."""
    return ingestion_pipeline.get_chunking_config()
