from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document ingestion status."""
    UPLOADING = "uploading"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload."""
    
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., min_length=3, max_length=20)
    
    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, v):
        """Ensure file type is supported."""
        allowed = ["pdf", "txt", "docx", "md"]
        if v.lower() not in allowed:
            raise ValueError(f"File type must be one of {allowed}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "research_paper.pdf",
                "file_type": "pdf"
            }
        }


class DocumentResponse(BaseModel):
    """Response schema for document info."""
    
    id: int
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    upload_time: datetime
    total_chunks: int
    total_tokens: int
    
    class Config:
        from_attributes = True  # SQLAlchemy compatibility


class ChunkResponse(BaseModel):
    """Response schema for chunk info."""
    
    id: int
    document_id: int
    chunk_index: int
    content: str
    token_count: int
    char_count: int
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Request schema for similarity search."""
    
    query: str = Field(..., min_length=1, max_length=5000)
    k: int = Field(default=5, ge=1, le=100)
    document_id: Optional[int] = None  # Optional: filter by document
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the main findings?",
                "k": 5,
                "document_id": 1
            }
        }


class SearchResultItem(BaseModel):
    """Individual search result."""
    
    content: str
    distance: float  # Similarity score
    document_id: int
    chunk_index: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "The main finding is...",
                "distance": 0.92,
                "document_id": 1,
                "chunk_index": 5
            }
        }


class SearchResponse(BaseModel):
    """Response schema for search results."""
    
    query: str
    results: List[SearchResultItem]
    total_results: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the main findings?",
                "results": [
                    {
                        "content": "...",
                        "distance": 0.95,
                        "document_id": 1,
                        "chunk_index": 5
                    }
                ],
                "total_results": 1
            }
        }


class HealthResponse(BaseModel):
    """Response schema for health check."""
    
    status: str = Field(default="ok")
    version: str
    database: str
    vector_db: str
    embedding_model: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "database": "postgresql",
                "vector_db": "chroma",
                "embedding_model": "all-MiniLM-L6-v2"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str
    detail: Optional[str] = None
    status_code: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "File too large",
                "detail": "Maximum file size is 50MB",
                "status_code": 413
            }
        }


class IngestionProgressResponse(BaseModel):
    """Response for ingestion progress tracking."""
    
    document_id: int
    status: DocumentStatus
    stage: str
    progress: float = Field(ge=0, le=1)  # 0.0 to 1.0
    current_step: str
    estimated_completion: Optional[datetime] = None
    
    class Config:
        from_attributes = True
