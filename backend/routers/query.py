"""Query and generation routes."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import logging
import time
from typing import Optional

from backend.models.schemas import GenerationRequest, GenerationResponse, SearchQuery, SourcePassage
from backend.services.embeddings import EmbeddingProvider
from backend.services.retrieval import HybridRetriever, VectorStore
from backend.services.generation import StreamingGenerator, FallbackGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])

# Global state
hybrid_retriever: HybridRetriever = None
generator = None


def init_query_router(retriever: HybridRetriever, gen):
    """Initialize router with dependencies."""
    global hybrid_retriever, generator
    hybrid_retriever = retriever
    generator = gen


@router.post("/search")
async def search_documents(search_query: SearchQuery):
    """
    Search documents using hybrid search.

    Args:
        search_query: Search query parameters

    Returns:
        Search results with source passages
    """
    try:
        if not search_query.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        start_time = time.time()

        # Perform hybrid search
        results = hybrid_retriever.search(
            query=search_query.query,
            top_k=search_query.top_k,
            use_hybrid=search_query.use_hybrid_search,
        )

        # Filter by similarity threshold
        filtered_results = [r for r in results if r.similarity_score >= search_query.similarity_threshold]

        # Convert to source passages
        sources = hybrid_retriever.to_source_passages(filtered_results)

        retrieval_time = time.time() - start_time

        logger.info(f"Search completed in {retrieval_time:.2f}s, found {len(sources)} results")

        return {
            "query": search_query.query,
            "results": len(sources),
            "sources": sources,
            "retrieval_time_ms": int(retrieval_time * 1000),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/generate")
async def generate_answer(generation_request: GenerationRequest):
    """
    Generate answer using RAG with streaming support.

    Args:
        generation_request: Generation request parameters

    Returns:
        Generated answer with sources
    """
    try:
        if not generation_request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        start_time = time.time()

        # Search for relevant documents
        search_results = hybrid_retriever.search(
            query=generation_request.query,
            top_k=generation_request.top_k,
            use_hybrid=generation_request.use_hybrid_search,
        )

        retrieval_time = time.time() - start_time

        # Filter by similarity threshold
        filtered_results = [r for r in search_results if r.similarity_score >= generation_request.similarity_threshold]

        if not filtered_results:
            return GenerationResponse(
                query=generation_request.query,
                answer="No relevant documents found for this query.",
                sources=[],
                model_used=getattr(generator, "model", "fallback"),
                total_tokens=0,
            )

        sources = hybrid_retriever.to_source_passages(filtered_results)

        # Generate answer
        if generation_request.stream:
            return StreamingResponse(
                _generate_streaming(generation_request, sources, retrieval_time),
                media_type="text/event-stream",
            )
        else:
            answer = generator.generate_with_sources(
                query=generation_request.query,
                sources=sources,
                max_tokens=generation_request.max_tokens or 2048,
                stream=False,
            )

            generation_time = time.time() - start_time - retrieval_time

            logger.info(f"Generation completed in {generation_time:.2f}s")

            return GenerationResponse(
                query=generation_request.query,
                answer=answer,
                sources=sources,
                model_used=getattr(generator, "model", "fallback"),
                total_tokens=None,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


async def _generate_streaming(generation_request: GenerationRequest, sources: list, retrieval_time: float):
    """Stream generation response."""
    try:
        # Send metadata
        yield f"data: {{\\"query\\": \\"{generation_request.query}\\", \\\"retrieval_time_ms\\": {int(retrieval_time * 1000)}}}\n\n"

        # Stream answer
        for chunk in generator.generate_with_sources(
            query=generation_request.query,
            sources=sources,
            max_tokens=generation_request.max_tokens or 2048,
            stream=True,
        ):
            yield f"data: {{\\"chunk\\": \\"{chunk}\\"}}\n\n"

        # Send sources
        sources_json = [
            {
                "document_id": s.document_id,
                "filename": s.filename,
                "similarity_score": s.similarity_score,
                "content": s.content[:200],
            }
            for s in sources
        ]
        yield f"data: {{\\"sources\\": {sources_json}}}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Error in streaming generation: {str(e)}")
        yield f"data: {{\\"error\\": \\"{str(e)}\\"}}\n\n"


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "RAG Engine is running",
        "retriever_available": hybrid_retriever is not None,
        "generator_available": generator is not None,
    }
