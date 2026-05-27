from sqlalchemy import Column, String, Integer, DateTime, Text, Float, ForeignKey, Enum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class DocumentStatus(str, enum.Enum):
    """Document ingestion status lifecycle."""
    UPLOADING = "uploading"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")


class Document(Base):
    """Document metadata."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADING, index=True)
    
    # Ingestion metadata
    upload_time = Column(DateTime, default=datetime.utcnow, index=True)
    ingestion_start_time = Column(DateTime, nullable=True)
    ingestion_end_time = Column(DateTime, nullable=True)
    ingestion_duration = Column(Float, nullable=True)  # seconds
    
    # Processing results
    total_chunks = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Vector DB reference
    vector_collection_id = Column(String(255), nullable=True, index=True)

    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index("idx_user_upload", "user_id", "upload_time"),
        Index("idx_status_upload", "status", "upload_time"),
    )


class Chunk(Base):
    """Chunk metadata."""
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # Position in document
    content = Column(Text, nullable=False)
    
    # Tokenization
    token_count = Column(Integer, nullable=False)
    char_count = Column(Integer, nullable=False)
    
    # Embedding reference
    embedding_id = Column(String(255), nullable=True, index=True)  # ChromaDB ID
    embedding_dimension = Column(Integer, nullable=True)
    
    # Metadata for retrieval
    source_page = Column(Integer, nullable=True)
    source_section = Column(String(255), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index("idx_doc_chunk", "document_id", "chunk_index"),
        Index("idx_embedding", "embedding_id"),
    )


class IngestionLog(Base):
    """Ingestion pipeline audit log."""
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Pipeline stage
    stage = Column(String(50), nullable=False)  # extraction, chunking, embedding, etc
    
    # Timing
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Status and metadata
    status = Column(String(20), nullable=False)  # success, failed, warning
    message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("idx_doc_stage", "document_id", "stage"),
    )
