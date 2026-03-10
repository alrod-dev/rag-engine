"""Embedding generation service."""

from typing import List, Optional
import numpy as np
from abc import ABC, abstractmethod

from backend.config import settings


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query.

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass


class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key
            model: Model name
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_embedding_model
        self.dimension = settings.embedding_dimension

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required for OpenAIEmbeddings")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t for t in texts if t.strip()]

        if not valid_texts:
            return [[] for _ in texts]

        try:
            response = self.client.embeddings.create(input=valid_texts, model=self.model)

            # Sort by index to maintain order
            embeddings = sorted(response.data, key=lambda x: x.index)
            return [e.embedding for e in embeddings]
        except Exception as e:
            raise RuntimeError(f"Error generating embeddings: {str(e)}")

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query."""
        embeddings = self.embed_texts([query])
        return embeddings[0] if embeddings else []

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class SentenceTransformerEmbeddings(EmbeddingProvider):
    """Sentence Transformer embedding provider (local, no API needed)."""

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """
        Initialize Sentence Transformer embeddings.

        Args:
            model: Model name
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("sentence-transformers package required")

        self.model_name = model
        self.model = SentenceTransformer(model)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        embeddings = self.model.encode(texts, convert_to_numpy=True)

        # Convert to list of lists
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query."""
        embedding = self.model.encode(query, convert_to_numpy=True)
        if isinstance(embedding, np.ndarray):
            return embedding.tolist()
        return embedding

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class HybridEmbeddings:
    """Hybrid embeddings combining multiple providers."""

    def __init__(self, primary: EmbeddingProvider, fallback: Optional[EmbeddingProvider] = None):
        """
        Initialize hybrid embeddings.

        Args:
            primary: Primary embedding provider
            fallback: Fallback provider if primary fails
        """
        self.primary = primary
        self.fallback = fallback

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using primary or fallback."""
        try:
            return self.primary.embed_texts(texts)
        except Exception as e:
            if self.fallback:
                return self.fallback.embed_texts(texts)
            raise

    def embed_query(self, query: str) -> List[float]:
        """Generate query embedding."""
        try:
            return self.primary.embed_query(query)
        except Exception as e:
            if self.fallback:
                return self.fallback.embed_query(query)
            raise

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.primary.get_dimension()


def get_embedding_provider(use_openai: bool = True) -> EmbeddingProvider:
    """
    Get embedding provider based on configuration.

    Args:
        use_openai: Use OpenAI if True, else use local Sentence Transformer

    Returns:
        EmbeddingProvider instance
    """
    if use_openai and settings.openai_api_key:
        try:
            return OpenAIEmbeddings()
        except Exception as e:
            # Fall back to Sentence Transformer
            return SentenceTransformerEmbeddings()
    else:
        return SentenceTransformerEmbeddings()


def get_hybrid_embedding_provider() -> HybridEmbeddings:
    """
    Get hybrid embedding provider with fallback.

    Returns:
        HybridEmbeddings instance
    """
    try:
        primary = OpenAIEmbeddings()
    except Exception:
        primary = SentenceTransformerEmbeddings()

    try:
        fallback = SentenceTransformerEmbeddings()
    except Exception:
        fallback = None

    return HybridEmbeddings(primary, fallback)
