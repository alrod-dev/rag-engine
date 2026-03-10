"""LLM generation service with streaming support."""

from typing import List, Generator, Optional
import json

from backend.models.schemas import SourcePassage
from backend.config import settings


class StreamingGenerator:
    """Generator for streaming LLM responses."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, temperature: Optional[float] = None):
        """
        Initialize streaming generator.

        Args:
            api_key: OpenAI API key
            model: Model name
            temperature: Sampling temperature
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.temperature = temperature if temperature is not None else settings.temperature

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required for StreamingGenerator")

    def generate_with_sources(
        self,
        query: str,
        sources: List[SourcePassage],
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str | Generator[str, None, None]:
        """
        Generate answer using sources with streaming support.

        Args:
            query: User query
            sources: Retrieved source passages
            max_tokens: Maximum tokens in response
            stream: Whether to stream response

        Returns:
            Generated answer or stream of answer chunks
        """
        # Build context from sources
        context = self._build_context(sources)

        # Build prompt
        system_prompt = """You are an expert assistant that answers questions based on provided documents.

Instructions:
1. Answer the question using only the provided context
2. If the answer is not in the context, say "I don't have enough information to answer that question"
3. Always cite sources by mentioning the document name and section
4. Be concise but thorough
5. Format your response clearly with proper paragraphs"""

        user_prompt = f"""Context from documents:
{context}

Question: {query}

Please provide a detailed answer based on the context above."""

        if stream:
            return self._stream_response(system_prompt, user_prompt, max_tokens)
        else:
            return self._generate_response(system_prompt, user_prompt, max_tokens)

    def _build_context(self, sources: List[SourcePassage]) -> str:
        """Build context string from sources."""
        context_parts = []

        for i, source in enumerate(sources, 1):
            context_parts.append(f"Source {i} ({source.filename}, Relevance: {source.similarity_score:.2%}):")
            context_parts.append(source.content)
            context_parts.append("")

        return "\n".join(context_parts)

    def _generate_response(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """Generate response without streaming."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Error generating response: {str(e)}")

    def _stream_response(self, system_prompt: str, user_prompt: str, max_tokens: int) -> Generator[str, None, None]:
        """Generate streaming response."""
        try:
            with self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=max_tokens,
                stream=True,
            ) as response:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error generating response: {str(e)}"

    def format_answer_with_citations(self, answer: str, sources: List[SourcePassage]) -> str:
        """
        Format answer with source citations.

        Args:
            answer: Generated answer
            sources: Source passages

        Returns:
            Formatted answer with citations
        """
        # Add sources section
        sources_section = "\n\n## Sources\n"

        for i, source in enumerate(sources, 1):
            sources_section += f"{i}. **{source.filename}** (Relevance: {source.similarity_score:.1%})\n"
            sources_section += f"   {source.content[:100]}...\n"

        return answer + sources_section

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            # Rough estimate: ~4 chars per token
            return len(text) // 4


class FallbackGenerator:
    """Fallback generator when OpenAI API is not available."""

    def generate_with_sources(
        self,
        query: str,
        sources: List[SourcePassage],
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str | Generator[str, None, None]:
        """
        Generate simple response from sources.

        Args:
            query: User query
            sources: Retrieved source passages
            max_tokens: Maximum tokens
            stream: Whether to stream

        Returns:
            Generated answer
        """
        answer_parts = []
        answer_parts.append("Based on the provided documents:\n")

        for source in sources:
            answer_parts.append(f"\nFrom {source.filename}:")
            answer_parts.append(source.content[:500])

        answer = "\n".join(answer_parts)

        if stream:
            return self._stream_answer(answer)
        else:
            return answer

    def _stream_answer(self, answer: str) -> Generator[str, None, None]:
        """Stream answer by chunks."""
        words = answer.split()
        chunk = ""
        for word in words:
            chunk += word + " "
            if len(chunk) > 50:
                yield chunk
                chunk = ""
        if chunk:
            yield chunk


def get_generator(use_openai: bool = True) -> StreamingGenerator | FallbackGenerator:
    """
    Get generator based on configuration.

    Args:
        use_openai: Use OpenAI if available

    Returns:
        Generator instance
    """
    if use_openai and settings.openai_api_key:
        try:
            return StreamingGenerator()
        except Exception:
            return FallbackGenerator()
    else:
        return FallbackGenerator()
