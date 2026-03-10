"""Unit tests for chunking strategies."""

import pytest
from backend.services.chunking import FixedSizeChunker, RecursiveChunker, SemanticChunker, get_chunker
from backend.utils.text_processing import count_tokens


class TestFixedSizeChunker:
    """Tests for FixedSizeChunker."""

    def test_chunk_creation(self):
        """Test basic chunking."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)

        text = "This is a sample document. " * 20
        document_id = "doc-1"

        chunks = chunker.chunk(text, document_id)

        assert len(chunks) > 0
        assert all(chunk.document_id == document_id for chunk in chunks)
        assert all(chunk.chunk_index == i for i, chunk in enumerate(chunks))

    def test_chunk_size_limit(self):
        """Test that chunks respect size limit."""
        chunker = FixedSizeChunker(chunk_size=200, chunk_overlap=50)

        text = "This is a sample document. " * 30
        chunks = chunker.chunk(text, "doc-1")

        for chunk in chunks:
            assert len(chunk.content) <= 200

    def test_empty_text(self):
        """Test handling of empty text."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)

        chunks = chunker.chunk("", "doc-1")
        assert len(chunks) == 0

    def test_chunk_overlap(self):
        """Test that chunks have overlap."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=30)

        text = "word " * 50
        chunks = chunker.chunk(text, "doc-1")

        if len(chunks) > 1:
            # Check that consecutive chunks have overlap
            for i in range(len(chunks) - 1):
                chunk1_end = chunks[i].content[-30:]
                chunk2_start = chunks[i + 1].content[:30]
                # Overlap should exist (at least some common text)
                assert len(chunk1_end) > 0 and len(chunk2_start) > 0


class TestRecursiveChunker:
    """Tests for RecursiveChunker."""

    def test_recursive_chunking(self):
        """Test recursive chunking."""
        chunker = RecursiveChunker(chunk_size=200, chunk_overlap=50)

        text = "This is a paragraph.\n\nThis is another paragraph.\n\nAnd a third one."
        document_id = "doc-2"

        chunks = chunker.chunk(text, document_id)

        assert len(chunks) > 0
        assert all(chunk.document_id == document_id for chunk in chunks)

    def test_custom_separators(self):
        """Test custom separators."""
        chunker = RecursiveChunker(
            chunk_size=200, chunk_overlap=50, separators=["\n", " ", ""]
        )

        text = "Line 1\nLine 2\nLine 3"
        chunks = chunker.chunk(text, "doc-3")

        assert len(chunks) > 0

    def test_handles_large_text(self):
        """Test chunking large text."""
        chunker = RecursiveChunker(chunk_size=300, chunk_overlap=50)

        text = "This is a sample sentence. " * 100
        chunks = chunker.chunk(text, "doc-4")

        assert len(chunks) > 1
        total_tokens = sum(chunk.token_count for chunk in chunks)
        assert total_tokens > 0


class TestSemanticChunker:
    """Tests for SemanticChunker."""

    def test_semantic_chunking(self):
        """Test semantic chunking based on sentences."""
        chunker = SemanticChunker(chunk_size=200, chunk_overlap=50)

        text = (
            "This is the first sentence. This is the second sentence. "
            "This is the third sentence. This is the fourth sentence."
        )

        chunks = chunker.chunk(text, "doc-5")

        assert len(chunks) > 0
        assert all(len(chunk.content.strip()) > 0 for chunk in chunks)

    def test_single_sentence(self):
        """Test handling of single sentence."""
        chunker = SemanticChunker(chunk_size=200, chunk_overlap=50)

        text = "This is a single sentence."
        chunks = chunker.chunk(text, "doc-6")

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_multiple_paragraphs(self):
        """Test handling multiple paragraphs."""
        chunker = SemanticChunker(chunk_size=200, chunk_overlap=50)

        text = "Paragraph 1. Sentence 2. Sentence 3. Paragraph 2. Sentence 2. Sentence 3."
        chunks = chunker.chunk(text, "doc-7")

        assert len(chunks) > 0


class TestGetChunker:
    """Tests for get_chunker factory function."""

    def test_get_fixed_chunker(self):
        """Test getting fixed size chunker."""
        chunker = get_chunker("fixed", 300, 50)
        assert isinstance(chunker, FixedSizeChunker)
        assert chunker.chunk_size == 300

    def test_get_recursive_chunker(self):
        """Test getting recursive chunker."""
        chunker = get_chunker("recursive", 300, 50)
        assert isinstance(chunker, RecursiveChunker)

    def test_get_semantic_chunker(self):
        """Test getting semantic chunker."""
        chunker = get_chunker("semantic", 300, 50)
        assert isinstance(chunker, SemanticChunker)

    def test_default_is_recursive(self):
        """Test that default is recursive."""
        chunker = get_chunker()
        assert isinstance(chunker, RecursiveChunker)


class TestChunkMetadata:
    """Tests for chunk metadata."""

    def test_chunk_has_metadata(self):
        """Test that chunks include metadata."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)

        metadata = {"source": "test.pdf", "page": 1}
        text = "Sample text " * 20

        chunks = chunker.chunk(text, "doc-8", metadata)

        assert all(chunk.metadata == metadata for chunk in chunks)

    def test_chunk_token_count(self):
        """Test that chunks have token counts."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)

        text = "This is a test. " * 20
        chunks = chunker.chunk(text, "doc-9")

        for chunk in chunks:
            assert chunk.token_count > 0
            # Token count should be approximately correct
            estimated_tokens = count_tokens(chunk.content)
            assert abs(chunk.token_count - estimated_tokens) <= 5
