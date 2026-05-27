import logging
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """ChromaDB vector store wrapper."""

    def __init__(
        self,
        persist_directory: str = settings.CHROMA_PATH,
        collection_name: str = settings.CHROMA_COLLECTION_NAME
    ):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Path to persistent storage
            collection_name: Name of the collection
        """
        logger.info(f"Initializing ChromaDB: {persist_directory}")

        try:
            # Configure ChromaDB for persistence
            chroma_settings = ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_directory,
                anonymized_telemetry=False
            )

            # Create client
            self.client = chromadb.Client(chroma_settings)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )

            logger.info(f"Collection '{collection_name}' ready")

        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[np.ndarray],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add documents and their embeddings to vector store.
        
        Args:
            documents: List of text chunks
            embeddings: List of embedding vectors
            ids: Unique identifiers for chunks
            metadatas: Optional metadata dicts
            
        Production pattern:
        - Always include metadata
        - Use meaningful IDs
        - Batch operations when possible
        """
        try:
            if metadatas is None:
                metadatas = [{} for _ in documents]

            logger.info(f"Adding {len(documents)} documents to vector store")

            # Convert embeddings to list format
            embeddings_list = [emb.tolist() for emb in embeddings]

            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(f"Successfully added {len(documents)} documents")

        except Exception as e:
            logger.error(f"Adding documents failed: {e}")
            raise

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results
            filter_metadata: Optional metadata filter
            
        Returns:
            Dict with results, distances, metadatas
            
        Production pattern:
        - Always check number of results returned
        - Validate distances
        - Consider filtering
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k,
                where=filter_metadata,
                include=["documents", "distances", "metadatas"]
            )

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def delete_document(self, doc_id: str) -> None:
        """Delete a document by ID."""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document: {doc_id}")
        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            raise

    def get_document_count(self) -> int:
        """Get number of documents in collection."""
        return self.collection.count()

    def get_all_metadata(self) -> List[Dict]:
        """Get all metadata (for analytics)."""
        all_data = self.collection.get()
        return all_data.get("metadatas", [])

    def update_document(
        self,
        doc_id: str,
        document: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update a document."""
        try:
            self.collection.update(
                ids=[doc_id],
                documents=[document],
                embeddings=[embedding.tolist()],
                metadatas=[metadata] if metadata else None
            )
            logger.info(f"Updated document: {doc_id}")
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise

    def persist(self) -> None:
        """Explicitly persist data to disk."""
        try:
            self.client.persist()
            logger.info("ChromaDB persisted to disk")
        except Exception as e:
            logger.error(f"Persistence failed: {e}")

    def delete_collection(self) -> None:
        """Delete entire collection (careful!)."""
        try:
            self.client.delete_collection(self.collection.name)
            logger.warning(f"Deleted collection: {self.collection.name}")
        except Exception as e:
            logger.error(f"Collection deletion failed: {e}")
