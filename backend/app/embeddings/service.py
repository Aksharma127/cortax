import logging
import asyncio
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding generation with batch processing and caching."""

    _instance: Optional['EmbeddingService'] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls):
        """Singleton pattern: one embedding model per process."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize embedding service."""
        if self._model is None:
            self._load_model()

    @classmethod
    def _load_model(cls):
        """Load embedding model from HuggingFace."""
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")

        try:
            cls._model = SentenceTransformer(
                settings.EMBEDDING_MODEL_NAME,
                device=settings.EMBEDDING_DEVICE
            )
            logger.info(f"Model loaded on device: {settings.EMBEDDING_DEVICE}")
            logger.info(f"Embedding dimension: {cls._model.get_sentence_embedding_dimension()}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    @property
    def model(self) -> SentenceTransformer:
        """Get the embedding model."""
        if self._model is None:
            self._load_model()
        return self._model

    def embed_single(
        self,
        text: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Embed a single text.
        
        Args:
            text: Text to embed
            normalize: L2 normalize embedding
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=normalize
            )
            return embedding

        except Exception as e:
            logger.error(f"Embedding failed for text: {e}")
            raise

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
        normalize: bool = True,
        show_progress: bool = False
    ) -> List[np.ndarray]:
        """
        Embed multiple texts with batching.
        
        Batch processing is ESSENTIAL for production:
        - 10-100x faster than sequential
        - Better GPU memory utilization
        - Standard in inference serving
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            normalize: L2 normalize embeddings
            show_progress: Show progress bar
            
        Returns:
            List of embedding arrays
        """
        logger.info(f"Embedding {len(texts)} texts with batch_size={batch_size}")

        try:
            # SentenceTransformers handles batching internally
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress
            )

            logger.info(
                f"Embedding complete: {len(texts)} texts, "
                f"shape={embeddings.shape}"
            )

            # Convert to list of arrays
            return [embeddings[i] for i in range(len(texts))]

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise

    async def embed_batch_async(
        self,
        texts: List[str],
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
        normalize: bool = True
    ) -> List[np.ndarray]:
        """
        Embed batch asynchronously.
        
        Why async?
        - Non-blocking embedding in web application
        - Process other requests while embedding
        - Better resource utilization
        
        The trick: Run CPU-bound embedding in thread pool.
        """
        loop = asyncio.get_event_loop()

        # Run embedding in thread pool (non-blocking)
        embeddings = await loop.run_in_executor(
            None,
            self.embed_batch,
            texts,
            batch_size,
            normalize
        )

        return embeddings

    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Similarity = (A · B) / (|A| |B|)
        
        Range: [-1, 1]
        - 1.0 = identical direction
        - 0.0 = orthogonal
        - -1.0 = opposite direction
        
        For normalized embeddings: similarity = dot product
        """
        if embedding1.shape != embedding2.shape:
            raise ValueError("Embeddings must have same shape")

        # Cosine similarity using dot product (if normalized)
        similarity = np.dot(embedding1, embedding2)

        return float(similarity)

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()

    def get_model_info(self) -> dict:
        """Get information about loaded model."""
        return {
            "model_name": settings.EMBEDDING_MODEL_NAME,
            "device": settings.EMBEDDING_DEVICE,
            "dimension": self.get_dimension(),
            "batch_size": settings.EMBEDDING_BATCH_SIZE,
            "model_class": self.model.__class__.__name__
        }

    @staticmethod
    def cosine_similarity_matrix(embeddings: List[np.ndarray]) -> np.ndarray:
        """
        Calculate cosine similarity matrix between all embeddings.
        
        Useful for:
        - Deduplication
        - Clustering analysis
        - Diversity measurement
        
        Returns matrix of shape (n, n) where entry [i,j] is similarity
        between embedding i and j.
        """
        embeddings_array = np.array(embeddings)
        
        # Normalize each embedding
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        normalized = embeddings_array / norms
        
        # Compute similarity matrix
        similarity_matrix = np.dot(normalized, normalized.T)
        
        return similarity_matrix
