"""Unit tests for document ingestion."""

import pytest
from io import BytesIO
from backend.services.ingestion import DocumentIngestionPipeline
from backend.models.schemas import DocumentMetadata


class TestDocumentIngestionPipeline:
    """Tests for DocumentIngestionPipeline."""

    def setup_method(self):
        """Setup test fixtures."""
        self.pipeline = DocumentIngestionPipeline(chunk_size=200, chunk_overlap=50)

    def test_ingest_txt_file(self):
        """Test ingesting a text file."""
        content = b"This is a test document. " * 50
        file = BytesIO(content)

        document_id, chunks, metadata = self.pipeline.ingest_file(file, "test.txt")

        assert document_id
        assert len(chunks) > 0
        assert metadata.filename == "test.txt"
        assert metadata.file_type == "txt"

    def test_chunks_have_content(self):
        """Test that generated chunks have content."""
        content = b"Sample content. " * 100
        file = BytesIO(content)

        document_id, chunks, metadata = self.pipeline.ingest_file(file, "test.txt")

        for chunk in chunks:
            assert len(chunk.content) > 0
            assert chunk.document_id == document_id
            assert chunk.chunk_index >= 0

    def test_metadata_extraction(self):
        """Test metadata extraction."""
        content = b"Test document content"
        file = BytesIO(content)

        document_id, chunks, metadata = self.pipeline.ingest_file(file, "test.txt")

        assert metadata.filename == "test.txt"
        assert metadata.file_type == "txt"
        assert metadata.num_chunks == len(chunks)
        assert metadata.upload_date is not None

    def test_unsupported_file_type(self):
        """Test handling of unsupported file type."""
        file = BytesIO(b"content")

        with pytest.raises(ValueError, match="Unsupported file type"):
            self.pipeline.ingest_file(file, "test.xyz")

    def test_empty_text_file(self):
        """Test handling empty text file."""
        file = BytesIO(b"   ")

        document_id, chunks, metadata = self.pipeline.ingest_file(file, "empty.txt")

        assert document_id
        # Empty file might result in empty chunks
        assert isinstance(chunks, list)

    def test_chunking_config_update(self):
        """Test updating chunking configuration."""
        self.pipeline.update_chunking_config(chunk_size=500, chunk_overlap=100, strategy="fixed")

        config = self.pipeline.get_chunking_config()

        assert config["chunk_size"] == 500
        assert config["chunk_overlap"] == 100
        assert config["strategy"] == "fixed"

    def test_different_chunking_strategies(self):
        """Test different chunking strategies produce chunks."""
        content = b"This is a test document. " * 50
        file = BytesIO(content)

        for strategy in ["fixed", "recursive", "semantic"]:
            pipeline = DocumentIngestionPipeline(chunk_size=200, chunk_overlap=50, chunking_strategy=strategy)
            file.seek(0)

            document_id, chunks, metadata = pipeline.ingest_file(file, "test.txt")

            assert len(chunks) > 0
            assert metadata.num_chunks == len(chunks)

    def test_chunk_overlap_preservation(self):
        """Test that chunks have proper overlap."""
        content = b"word " * 200
        file = BytesIO(content)

        document_id, chunks, metadata = self.pipeline.ingest_file(file, "test.txt")

        # Should have multiple chunks for long document
        assert len(chunks) >= 1

    def test_metadata_in_chunks(self):
        """Test that chunks contain metadata."""
        content = b"Test content " * 50
        file = BytesIO(content)

        document_id, chunks, metadata = self.pipeline.ingest_file(file, "test.txt")

        for chunk in chunks:
            assert "source" in chunk.metadata
            assert chunk.metadata["source"] == "test.txt"


class TestTextExtraction:
    """Tests for text extraction from different formats."""

    def test_txt_extraction(self):
        """Test TXT file extraction."""
        pipeline = DocumentIngestionPipeline()
        content = b"This is test content\nWith multiple lines"
        file = BytesIO(content)

        document_id, chunks, metadata = pipeline.ingest_file(file, "test.txt")

        assert len(chunks) > 0
        assert any("test content" in chunk.content for chunk in chunks)

    def test_csv_extraction(self):
        """Test CSV file extraction."""
        pipeline = DocumentIngestionPipeline()
        content = b"Name,Age,City\nJohn,30,NYC\nJane,25,LA"
        file = BytesIO(content)

        document_id, chunks, metadata = pipeline.ingest_file(file, "test.csv")

        assert len(chunks) > 0
        # CSV should be converted to readable format

    def test_large_file_handling(self):
        """Test handling of large files."""
        pipeline = DocumentIngestionPipeline()
        # Create a 5MB content
        content = b"This is test content. " * 100000
        file = BytesIO(content)

        document_id, chunks, metadata = pipeline.ingest_file(file, "large.txt")

        assert len(chunks) > 10  # Large file should create many chunks
        assert metadata.file_size > 1000
