"""Document retrieval service with hybrid search."""

from typing import List, Dict, Tuple, Optional
import numpy as np
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.models.schemas import TextChunk, SourcePassage
from backend.services.embeddings import EmbeddingProvider


@dataclass
class SearchResult:
    """Result from a search query."""

    chunk: TextChunk
    similarity_score: float
    score_source: str  # "semantic" or "keyword"


class VectorStore:
    """In-memory vector store for embeddings."""

    def __init__(self):
        """Initialize vector store."""
        self.chunks: Dict[str, TextChunk] = {}
        self.embeddings: Dict[str, List[float]] = {}
        self.documents: Dict[str, List[str]] = {}  # document_id -> chunk_ids

    def add_chunks(self, chunks: List[TextChunk], embeddings: List[List[float]]):
        """Add chunks with embeddings to store."""
        for chunk, embedding in zip(chunks, embeddings):
            self.chunks[chunk.chunk_id] = chunk
            self.embeddings[chunk.chunk_id] = embedding

            # Index by document
            if chunk.document_id not in self.documents:
                self.documents[chunk.document_id] = []
            self.documents[chunk.document_id].append(chunk.chunk_id)

    def get_chunk(self, chunk_id: str) -> Optional[TextChunk]:
        """Get a chunk by ID."""
        return self.chunks.get(chunk_id)

    def get_document_chunks(self, document_id: str) -> List[TextChunk]:
        """Get all chunks for a document."""
        chunk_ids = self.documents.get(document_id, [])
        return [self.chunks[cid] for cid in chunk_ids if cid in self.chunks]

    def delete_document(self, document_id: str):
        """Delete all chunks for a document."""
        chunk_ids = self.documents.get(document_id, [])
        for chunk_id in chunk_ids:
            if chunk_id in self.chunks:
                del self.chunks[chunk_id]
            if chunk_id in self.embeddings:
                del self.embeddings[chunk_id]
        if document_id in self.documents:
            del self.documents[document_id]

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find most similar chunks using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of (chunk_id, similarity_score) tuples
        """
        if not self.embeddings:
            return []

        query_vec = np.array(query_embedding)

        # Calculate cosine similarity with all chunks
        similarities = []
        for chunk_id, embedding in self.embeddings.items():
            emb_vec = np.array(embedding)

            # Cosine similarity
            norm_q = np.linalg.norm(query_vec)
            norm_e = np.linalg.norm(emb_vec)

            if norm_q > 0 and norm_e > 0:
                similarity = np.dot(query_vec, emb_vec) / (norm_q * norm_e)
                similarities.append((chunk_id, similarity))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class HybridRetriever:
    """Hybrid retriever combining semantic and keyword search."""

    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore):
        """
        Initialize hybrid retriever.

        Args:
            embedding_provider: Embedding provider for semantic search
            vector_store: Vector store with indexed chunks
        """
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.chunks_for_tfidf: List[TextChunk] = []

    def _build_tfidf_index(self):
        """Build TF-IDF index for keyword search."""
        chunks_list = list(self.vector_store.chunks.values())

        if not chunks_list:
            return

        texts = [chunk.content for chunk in chunks_list]
        self.tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")

        try:
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            self.chunks_for_tfidf = chunks_list
        except Exception as e:
            # If TF-IDF fails, fall back to semantic search only
            self.tfidf_vectorizer = None
            self.tfidf_matrix = None

    def _keyword_search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Keyword search using TF-IDF.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of (chunk_id, similarity_score) tuples
        """
        if not self.tfidf_vectorizer or self.tfidf_matrix is None:
            return []

        try:
            query_vec = self.tfidf_vectorizer.transform([query])
            similarities = (query_vec * self.tfidf_matrix.T).toarray()[0]

            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    chunk_id = self.chunks_for_tfidf[idx].chunk_id
                    results.append((chunk_id, float(similarities[idx])))

            return results
        except Exception:
            return []

    def search(
        self, query: str, top_k: int = 5, use_hybrid: bool = True, semantic_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        Perform search using hybrid approach.

        Args:
            query: Search query
            top_k: Number of results to return
            use_hybrid: Use hybrid search vs semantic only
            semantic_weight: Weight for semantic results (0-1)

        Returns:
            List of search results
        """
        results = {}

        if use_hybrid:
            # Rebuild TF-IDF index if needed
            if self.tfidf_vectorizer is None:
                self._build_tfidf_index()

            # Keyword search
            keyword_results = self._keyword_search(query, top_k)
            for chunk_id, score in keyword_results:
                if chunk_id not in results:
                    results[chunk_id] = {"semantic": 0.0, "keyword": 0.0}
                results[chunk_id]["keyword"] = score
                results[chunk_id]["source"] = "keyword"

        # Semantic search
        try:
            query_embedding = self.embedding_provider.embed_query(query)
            semantic_results = self.vector_store.similarity_search(query_embedding, top_k)

            for chunk_id, score in semantic_results:
                if chunk_id not in results:
                    results[chunk_id] = {"semantic": 0.0, "keyword": 0.0}
                results[chunk_id]["semantic"] = score
                results[chunk_id]["source"] = "semantic"
        except Exception:
            pass

        # Combine scores if hybrid
        combined_results = []
        keyword_weight = 1.0 - semantic_weight

        for chunk_id, scores in results.items():
            if chunk_id not in self.vector_store.chunks:
                continue

            if use_hybrid:
                combined_score = (scores["semantic"] * semantic_weight + scores["keyword"] * keyword_weight) / (
                    semantic_weight + keyword_weight
                )
            else:
                combined_score = scores["semantic"]

            chunk = self.vector_store.chunks[chunk_id]
            combined_results.append(SearchResult(chunk=chunk, similarity_score=combined_score, score_source=scores["source"]))

        # Sort by combined score and return top k
        combined_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return combined_results[:top_k]

    def to_source_passages(self, results: List[SearchResult]) -> List[SourcePassage]:
        """
        Convert search results to source passages.

        Args:
            results: Search results

        Returns:
            List of source passages
        """
        passages = []
        for result in results:
            passage = SourcePassage(
                document_id=result.chunk.document_id,
                filename=result.chunk.metadata.get("source", "Unknown"),
                content=result.chunk.content,
                chunk_index=result.chunk.chunk_index,
                similarity_score=result.similarity_score,
                metadata=result.chunk.metadata,
            )
            passages.append(passage)
        return passages
