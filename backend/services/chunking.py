"""Document chunking strategies."""

from typing import List, Dict, Any
from abc import ABC, abstractmethod
import re
from backend.models.schemas import TextChunk
from backend.utils.text_processing import count_tokens, clean_text


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 100):
        """
        Initialize chunking strategy.

        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def chunk(self, text: str, document_id: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """
        Chunk text according to strategy.

        Args:
            text: Text to chunk
            document_id: ID of source document
            metadata: Additional metadata

        Returns:
            List of text chunks
        """
        pass


class FixedSizeChunker(ChunkingStrategy):
    """Chunks text into fixed-size pieces with overlap."""

    def chunk(self, text: str, document_id: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """Chunk text into fixed-size pieces."""
        if metadata is None:
            metadata = {}

        chunks = []
        text = clean_text(text)

        # Calculate stride (how much to move forward each iteration)
        stride = self.chunk_size - self.chunk_overlap

        for i in range(0, len(text), stride):
            chunk_text = text[i : i + self.chunk_size]

            if len(chunk_text.strip()) < 50:  # Skip very small chunks
                continue

            chunk = TextChunk(
                chunk_id=f"{document_id}_chunk_{len(chunks)}",
                document_id=document_id,
                content=chunk_text,
                chunk_index=len(chunks),
                metadata=metadata,
                token_count=count_tokens(chunk_text),
            )
            chunks.append(chunk)

        return chunks


class RecursiveChunker(ChunkingStrategy):
    """Chunks text recursively using separators (sentences, paragraphs, etc)."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 100, separators: List[str] = None):
        """
        Initialize recursive chunker.

        Args:
            chunk_size: Target size of each chunk
            chunk_overlap: Overlap between chunks
            separators: List of separators to try (in order)
        """
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str, document_id: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """Chunk text recursively using separators."""
        if metadata is None:
            metadata = {}

        text = clean_text(text)
        chunks = []

        # Try to split on separators
        chunks = self._split_text(text, self.separators)

        # Merge small chunks and create TextChunk objects
        merged_chunks = self._merge_chunks(chunks)

        result_chunks = []
        for i, chunk_text in enumerate(merged_chunks):
            if len(chunk_text.strip()) < 50:
                continue

            chunk = TextChunk(
                chunk_id=f"{document_id}_chunk_{len(result_chunks)}",
                document_id=document_id,
                content=chunk_text,
                chunk_index=len(result_chunks),
                metadata=metadata,
                token_count=count_tokens(chunk_text),
            )
            result_chunks.append(chunk)

        return result_chunks

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text on separators."""
        good_splits = []

        for separator in separators:
            if separator == "":
                splits = list(text)
            else:
                splits = text.split(separator)

            # Filter out empty strings and very small pieces
            good_splits = [s for s in splits if len(s) > self.chunk_overlap]

            if len(good_splits) > 1:
                break

        if not good_splits:
            return [text]

        return good_splits

    def _merge_chunks(self, chunks: List[str]) -> List[str]:
        """Merge small chunks together."""
        separator = "\n\n"
        merged = []
        current_chunk = ""

        for chunk in chunks:
            if not chunk.strip():
                continue

            # Add to current chunk
            test_text = current_chunk + separator + chunk if current_chunk else chunk

            if count_tokens(test_text) <= self.chunk_size:
                current_chunk = test_text
            else:
                # Current chunk is full
                if current_chunk:
                    merged.append(current_chunk)
                current_chunk = chunk

        # Add remaining chunk
        if current_chunk:
            merged.append(current_chunk)

        # Add overlap
        result = []
        for i, chunk in enumerate(merged):
            if i == 0:
                result.append(chunk)
            else:
                # Add overlap from previous chunk
                prev_chunk = merged[i - 1]
                overlap_text = prev_chunk[-self.chunk_overlap :] if len(prev_chunk) > self.chunk_overlap else prev_chunk
                result.append(overlap_text + separator + chunk)

        return result


class SemanticChunker(ChunkingStrategy):
    """Chunks text based on semantic similarity between sentences."""

    def chunk(self, text: str, document_id: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """
        Chunk text using sentence-level semantic similarity.

        Args:
            text: Text to chunk
            document_id: Source document ID
            metadata: Additional metadata

        Returns:
            List of chunks
        """
        if metadata is None:
            metadata = {}

        text = clean_text(text)

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return [
                TextChunk(
                    chunk_id=f"{document_id}_chunk_0",
                    document_id=document_id,
                    content=text,
                    chunk_index=0,
                    metadata=metadata,
                    token_count=count_tokens(text),
                )
            ]

        # Group sentences into chunks
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            test_text = current_chunk + " " + sentence if current_chunk else sentence
            token_count = count_tokens(test_text)

            if token_count <= self.chunk_size:
                current_chunk = test_text
            else:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append(current_chunk)

                current_chunk = sentence

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk)

        # Convert to TextChunk objects
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk = TextChunk(
                chunk_id=f"{document_id}_chunk_{i}",
                document_id=document_id,
                content=chunk_text,
                chunk_index=i,
                metadata=metadata,
                token_count=count_tokens(chunk_text),
            )
            result.append(chunk)

        return result


def get_chunker(strategy: str = "recursive", chunk_size: int = 512, chunk_overlap: int = 100) -> ChunkingStrategy:
    """
    Get a chunking strategy instance.

    Args:
        strategy: Strategy name (fixed, recursive, semantic)
        chunk_size: Target chunk size
        chunk_overlap: Chunk overlap

    Returns:
        ChunkingStrategy instance
    """
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size, chunk_overlap)
    elif strategy == "semantic":
        return SemanticChunker(chunk_size, chunk_overlap)
    else:  # recursive is default
        return RecursiveChunker(chunk_size, chunk_overlap)
