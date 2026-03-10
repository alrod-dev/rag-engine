import re
import tiktoken
from typing import Dict, List, Tuple
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text
    """
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)

    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Remove control characters
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")

    # Remove extra whitespace at start/end
    text = text.strip()

    return text


def extract_metadata(text: str, filename: str) -> Dict[str, str]:
    """
    Extract metadata from text content.

    Args:
        text: Document text
        filename: Document filename

    Returns:
        Dictionary of extracted metadata
    """
    metadata = {
        "filename": filename,
        "file_type": filename.split(".")[-1].lower(),
        "text_length": len(text),
        "num_paragraphs": len([p for p in text.split("\n\n") if p.strip()]),
    }

    # Extract potential title from first line if it looks like a heading
    first_line = text.split("\n")[0].strip()
    if len(first_line) < 150 and first_line:
        metadata["title"] = first_line

    return metadata


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        model: Model name

    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    return len(tokens)


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Split on sentence endings
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
    """
    Extract code blocks from text.

    Args:
        text: Text containing code blocks

    Returns:
        List of (language, code) tuples
    """
    pattern = r"```(\w*)\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def remove_code_blocks(text: str) -> str:
    """
    Remove code blocks from text.

    Args:
        text: Text containing code blocks

    Returns:
        Text without code blocks
    """
    pattern = r"```[\s\S]*?```"
    return re.sub(pattern, "", text)


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.

    Args:
        text: Text containing URLs

    Returns:
        List of URLs
    """
    pattern = r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
    return re.findall(pattern, text)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.

    Args:
        text: Text containing emails

    Returns:
        List of email addresses
    """
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    return re.findall(pattern, text)


def sanitize_chunk_id(text: str) -> str:
    """
    Create a valid chunk ID from text.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized ID
    """
    # Remove special characters and lowercase
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", text[:50]).lower()
    # Remove multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized.strip("_")


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
