from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.core.config import settings
from app.db.database import get_db, init_db, close_db
from app.schemas.schemas import (
    DocumentUploadRequest,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    HealthResponse,
    ErrorResponse
)
from app.models.models import Document, Chunk, DocumentStatus
from app.ingestion.loader import DocumentLoader
from app.ingestion.extractor import TextExtractor
from app.ingestion.chunker import ChunkerFactory
from app.embeddings.service import EmbeddingService
from app.vectorstore.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade document ingestion pipeline",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Global instances (Singleton pattern)
embedding_service = None
vector_store = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global embedding_service, vector_store
    
    logger.info("Starting up Cortex ingestion pipeline...")
    
    try:
        # Initialize database
        init_db()
        
        # Initialize embedding service (loads model)
        embedding_service = EmbeddingService()
        
        # Initialize vector store
        vector_store = ChromaVectorStore()
        
        logger.info("Startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down...")
    
    if vector_store:
        vector_store.persist()
    
    logger.info("Shutdown complete")


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        database="postgresql",
        vector_db="chromadb",
        embedding_model=embedding_service.get_model_info()["model_name"]
    )


@app.get("/api/models")
async def get_models_info():
    """Get information about loaded models."""
    return {
        "embedding_service": embedding_service.get_model_info()
    }


@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and ingest a document.
    
    Supports: PDF, TXT, DOCX, Markdown
    """
    try:
        logger.info(f"Received upload: {file.filename}, size={file.size}")
        
        # Validate file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file.size} > {settings.MAX_FILE_SIZE}"
            )
        
        # Read file content
        content = await file.read()
        
        # Save file
        file_path = await DocumentLoader.save_upload(content, file.filename)
        
        # Validate file
        if not DocumentLoader.validate_file(file_path):
            raise HTTPException(status_code=400, detail="Invalid file format")
        
        # Load and parse document
        raw_text = await DocumentLoader.load_file(file_path)
        
        # Clean text
        cleaned_text = TextExtractor.extract_and_clean(raw_text)
        
        # Create document record
        doc = Document(
            filename=file.filename,
            file_type=file.filename.split('.')[-1].lower(),
            file_size=len(content),
            status=DocumentStatus.EXTRACTING
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        logger.info(f"Document created: id={doc.id}, filename={doc.filename}")
        
        # Chunking
        logger.info("Starting chunking...")
        doc.status = DocumentStatus.CHUNKING
        db.commit()
        
        chunker = ChunkerFactory.create(
            "fixed_token",
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        chunks = chunker.chunk(cleaned_text)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks produced")
        
        logger.info(f"Created {len(chunks)} chunks")
        
        # Embedding
        logger.info("Starting embedding...")
        doc.status = DocumentStatus.EMBEDDING
        db.commit()
        
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await embedding_service.embed_batch_async(chunk_texts)
        
        logger.info(f"Generated embeddings: {len(embeddings)} vectors")
        
        # Storage
        logger.info("Storing chunks and embeddings...")
        doc.status = DocumentStatus.STORING
        db.commit()
        
        db_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = Chunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk.text,
                token_count=chunk.token_count,
                char_count=chunk.char_count,
                embedding_id=f"doc_{doc.id}_chunk_{i}"
            )
            db_chunks.append(db_chunk)
        
        db.add_all(db_chunks)
        db.commit()
        
        logger.info(f"Stored {len(db_chunks)} chunks in PostgreSQL")
        
        chunk_ids = [f"doc_{doc.id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": doc.id,
                "chunk_index": i,
                "filename": doc.filename
            }
            for i in range(len(chunks))
        ]
        
        vector_store.add_documents(
            documents=chunk_texts,
            embeddings=embeddings,
            ids=chunk_ids,
            metadatas=metadatas
        )
        
        logger.info(f"Stored {len(chunk_ids)} embeddings in ChromaDB")
        
        # Update document
        doc.status = DocumentStatus.COMPLETED
        doc.total_chunks = len(chunks)
        doc.total_tokens = sum(c.token_count for c in chunks)
        doc.ingestion_end_time = datetime.utcnow()
        db.commit()
        db.refresh(doc)
        
        logger.info(f"Document ingestion complete: id={doc.id}")
        
        return DocumentResponse.from_orm(doc)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Semantic search over indexed documents."""
    try:
        logger.info(f"Search: '{request.query}', k={request.k}")
        
        query_embedding = embedding_service.embed_single(request.query)
        
        logger.info(f"Query embedding: shape={query_embedding.shape}")
        
        search_results = vector_store.search(
            query_embedding=query_embedding,
            k=request.k
        )
        
        # Parse results
        results = []
        if search_results["ids"] and len(search_results["ids"]) > 0:
            for i, doc_id in enumerate(search_results["ids"][0]):
                result = SearchResultItem(
                    content=search_results["documents"][0][i],
                    distance=float(search_results["distances"][0][i]),
                    document_id=search_results["metadatas"][0][i]["document_id"],
                    chunk_index=search_results["metadatas"][0][i]["chunk_index"]
                )
                results.append(result)
        
        logger.info(f"Search returned {len(results)} results")
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents", response_model=list[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    """List all ingested documents."""
    documents = db.query(Document).all()
    return [DocumentResponse.from_orm(doc) for doc in documents]


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document by ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.from_orm(doc)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT
    )
