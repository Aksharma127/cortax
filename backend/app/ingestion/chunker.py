import logging
import tiktoken
from abc import ABC, abstractmethod
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Text chunk with metadata."""
    text: str
    index: int  # Position in document
    start_token: int
    end_token: int
    token_count: int
    char_count: int


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""

    @abstractmethod
    def chunk(self, text: str) -> List[Chunk]:
        """Chunk text and return list of chunks."""
        pass


class FixedTokenChunking(ChunkingStrategy):
    """Fixed-size token-based chunking."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 100,
        min_chunk_length: int = 50
    ):
        """
        Args:
            chunk_size: Target tokens per chunk
            overlap: Overlap tokens between chunks
            min_chunk_length: Minimum chars for valid chunk
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_length = min_chunk_length
        
        # Use OpenAI's tokenizer (cl100k_base)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def chunk(self, text: str) -> List[Chunk]:
        """Chunk text using fixed token size with overlap."""
        logger.info(f"Fixed token chunking: text_length={len(text)}")

        # Tokenize
        try:
            tokens = self.tokenizer.encode(text)
        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            return []

        if len(tokens) == 0:
            logger.warning("No tokens after encoding")
            return []

        chunks = []
        chunk_index = 0
        start_token = 0

        # Sliding window
        while start_token < len(tokens):
            # End position
            end_token = min(start_token + self.chunk_size, len(tokens))

            # Extract tokens
            chunk_tokens = tokens[start_token:end_token]

            # Decode back to text
            try:
                chunk_text = self.tokenizer.decode(chunk_tokens)
            except Exception as e:
                logger.error(f"Decoding failed: {e}")
                start_token = end_token
                continue

            # Validate chunk
            if len(chunk_text) >= self.min_chunk_length:
                chunk = Chunk(
                    text=chunk_text,
                    index=chunk_index,
                    start_token=start_token,
                    end_token=end_token,
                    token_count=len(chunk_tokens),
                    char_count=len(chunk_text)
                )
                chunks.append(chunk)
                chunk_index += 1

            # Move window (with overlap)
            start_token = end_token - self.overlap

            # Prevent infinite loop
            if end_token >= len(tokens):
                break

        logger.info(f"Fixed token chunking complete: chunks={len(chunks)}")
        return chunks


class SentenceWindowChunking(ChunkingStrategy):
    """Sentence-aware chunking with sliding window."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 100,
        min_chunk_length: int = 50
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_length = min_chunk_length
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Simple approach: split on periods, question marks, exclamation marks.
        Real systems need better sentence splitting (spacy, nltk, etc.)
        """
        # This is a naive implementation
        # For production, use sentence_transformers or spacy
        sentences = []
        current = []

        for char in text:
            current.append(char)
            if char in '.!?\n':
                sentence = ''.join(current).strip()
                if sentence:
                    sentences.append(sentence)
                current = []

        # Add remaining
        if current:
            sentence = ''.join(current).strip()
            if sentence:
                sentences.append(sentence)

        return sentences

    def chunk(self, text: str) -> List[Chunk]:
        """Chunk text respecting sentence boundaries."""
        logger.info(f"Sentence window chunking: text_length={len(text)}")

        sentences = self._split_sentences(text)
        if not sentences:
            logger.warning("No sentences detected")
            return []

        chunks = []
        chunk_index = 0
        current_chunk_sentences = []
        current_tokens = []

        for sentence in sentences:
            try:
                sentence_tokens = self.tokenizer.encode(sentence)
            except Exception as e:
                logger.error(f"Sentence tokenization failed: {e}")
                continue

            # Would adding this sentence exceed limit?
            if len(current_tokens) + len(sentence_tokens) > self.chunk_size and current_chunk_sentences:
                # Save current chunk
                chunk_text = ' '.join(current_chunk_sentences)
                if len(chunk_text) >= self.min_chunk_length:
                    chunk = Chunk(
                        text=chunk_text,
                        index=chunk_index,
                        start_token=0,  # Simplified
                        end_token=len(current_tokens),
                        token_count=len(current_tokens),
                        char_count=len(chunk_text)
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                # Start new chunk with overlap (previous sentence)
                if len(current_chunk_sentences) > 1:
                    current_chunk_sentences = [current_chunk_sentences[-1]]
                    current_tokens = self.tokenizer.encode(current_chunk_sentences[0])
                else:
                    current_chunk_sentences = []
                    current_tokens = []

            # Add sentence to current chunk
            current_chunk_sentences.append(sentence)
            current_tokens.extend(sentence_tokens)

        # Add final chunk
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            if len(chunk_text) >= self.min_chunk_length:
                chunk = Chunk(
                    text=chunk_text,
                    index=chunk_index,
                    start_token=0,
                    end_token=len(current_tokens),
                    token_count=len(current_tokens),
                    char_count=len(chunk_text)
                )
                chunks.append(chunk)

        logger.info(f"Sentence window chunking complete: chunks={len(chunks)}")
        return chunks


class ChunkerFactory:
    """Factory for creating chunking strategies."""

    STRATEGIES = {
        "fixed_token": FixedTokenChunking,
        "sentence_window": SentenceWindowChunking,
    }

    @staticmethod
    def create(
        strategy_name: str = "fixed_token",
        **kwargs
    ) -> ChunkingStrategy:
        """
        Create a chunking strategy.
        
        Usage:
            chunker = ChunkerFactory.create(
                "fixed_token",
                chunk_size=512,
                overlap=100
            )
            chunks = chunker.chunk(text)
        """
        strategy_class = ChunkerFactory.STRATEGIES.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown chunking strategy: {strategy_name}")

        return strategy_class(**kwargs)
