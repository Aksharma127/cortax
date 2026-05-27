# Cortex Phase 1 Setup Guide

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Git

### Step 1: Install Dependencies

```bash
cd cortex/backend
pip install -r requirements.txt
```

### Step 2: Set Up PostgreSQL

**Option A: Using Docker (Recommended)**

```bash
docker run --name cortex-db \
  -e POSTGRES_DB=cortex_db \
  -e POSTGRES_USER=cortex \
  -e POSTGRES_PASSWORD=cortex \
  -p 5432:5432 \
  postgres:15
```

**Option B: Local PostgreSQL**

```bash
createdb cortex_db
# Set password if needed
```

### Step 3: Create Environment File

Create `.env` in `cortex/backend/`:

```env
# Database
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex_db

# Environment
DEBUG=True
ENVIRONMENT=development

# Embeddings
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=100

# File Upload
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=pdf,txt,docx,md

# API
API_PORT=8000
API_HOST=0.0.0.0
```

### Step 4: Run API Server

```bash
cd cortex/backend
python -m uvicorn app.main:app --reload --port 8000
```

Output:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 5: Access API Documentation

Visit: **http://localhost:8000/api/docs**

You'll see:
- All available endpoints
- Request/response schemas
- Try-it-out functionality
- Auto-generated documentation

---

## Testing the Pipeline

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "postgresql",
  "vector_db": "chroma",
  "embedding_model": "all-MiniLM-L6-v2"
}
```

### Test 2: Upload a Document

Create a sample text file:

```bash
cat > sample.txt << 'EOF'
# Research Paper: Deep Learning Applications

## Introduction
This paper explores the practical applications of deep learning in modern systems.

## Main Findings
We discovered that proper data preprocessing is crucial for model performance.
The ingestion pipeline directly impacts downstream retrieval quality.

## Conclusion
A well-designed backend system is essential for production AI applications.
EOF
```

Upload it:

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@sample.txt"
```

Response:

```json
{
  "id": 1,
  "filename": "sample.txt",
  "file_type": "txt",
  "file_size": 425,
  "status": "completed",
  "upload_time": "2024-01-15T10:30:00",
  "total_chunks": 3,
  "total_tokens": 89
}
```

### Test 3: Search

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main findings about data preprocessing?",
    "k": 5
  }'
```

Response:

```json
{
  "query": "What are the main findings about data preprocessing?",
  "results": [
    {
      "content": "We discovered that proper data preprocessing is crucial for model performance.",
      "distance": 0.87,
      "document_id": 1,
      "chunk_index": 2
    },
    {
      "content": "The ingestion pipeline directly impacts downstream retrieval quality.",
      "distance": 0.82,
      "document_id": 1,
      "chunk_index": 3
    }
  ],
  "total_results": 2
}
```

---

## Using Docker Compose (Full Stack)

Create `docker-compose.yml` in `cortex/backend/`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cortex_db
      POSTGRES_USER: cortex
      POSTGRES_PASSWORD: cortex
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://cortex:cortex@postgres:5432/cortex_db
      DEBUG: "True"
    depends_on:
      - postgres
    volumes:
      - ./data:/app/data

volumes:
  postgres_data:
```

Run:

```bash
docker-compose up
```

---

## Understanding the Code Structure

### Core Modules

**`app/core/config.py`**
- Environment variables
- Settings validation
- Configuration for all services

**`app/db/database.py`**
- SQLAlchemy engine setup
- Connection pooling
- Session management
- Dependency injection

**`app/models/models.py`**
- ORM models (User, Document, Chunk)
- Relationships
- Indexes for performance
- Status tracking

**`app/ingestion/loader.py`**
- Multi-format document parsing
- File validation
- PDF/DOCX/TXT/MD support
- Security checks

**`app/ingestion/extractor.py`**
- Text normalization
- Unicode handling
- PDF extraction artifact removal
- Page number/header removal

**`app/ingestion/chunker.py`**
- Fixed token chunking
- Sentence window chunking
- Overlap strategy
- Tokenization-aware splitting

**`app/embeddings/service.py`**
- Embedding model loading
- Batch processing
- Async support
- Similarity computation
- Singleton pattern

**`app/vectorstore/chroma_store.py`**
- ChromaDB integration
- Document storage
- Similarity search
- Metadata filtering
- Persistence

**`app/schemas/schemas.py`**
- Pydantic validation
- Request/response models
- Type safety
- Auto documentation

**`app/main.py`**
- FastAPI application
- Route definitions
- Dependency injection
- Full pipeline orchestration

---

## Key Learnings

### Why This Architecture?

1. **Modularity**: Each component is independent
2. **Testability**: Easy to unit test individual modules
3. **Scalability**: Async patterns allow concurrent processing
4. **Maintainability**: Clear separation of concerns
5. **Production-Ready**: Error handling, logging, validation

### Production Patterns

- **Dependency Injection**: Services are injected, not imported
- **Singleton Pattern**: Single embedding model instance
- **Factory Pattern**: Chunking strategy factory
- **Abstract Base Classes**: Extensible parsers
- **Type Hints**: Type safety throughout
- **Validation**: Input validation at API boundary

### Performance Optimization

- **Connection Pooling**: Reuse DB connections
- **Batch Embedding**: 10-100x faster than sequential
- **Async I/O**: Non-blocking file operations
- **Indexing**: Fast database queries
- **Vector Indexing**: Fast similarity search

---

## Troubleshooting

### Error: "cannot import name 'BaseSettings'"

```bash
pip install pydantic-settings
```

### Error: "no module named 'torch'"

```bash
pip install torch
```

### Error: "connection refused" on PostgreSQL

Ensure PostgreSQL is running:

```bash
# Check if PostgreSQL is running
psql -U cortex -d cortex_db -c "SELECT 1"

# If not, start it (macOS):
brew services start postgresql

# Or via Docker:
docker-compose up -d postgres
```

### Error: "No such file or directory: /data/uploads"

The directory is created automatically on first upload. If you want to pre-create:

```bash
mkdir -p data/uploads
mkdir -p data/chroma_db
```

### Error: "Embedding model download timeout"

First download takes a while. The model is cached in `~/.cache/huggingface/`. 

For faster initialization, use a smaller model:

```env
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

---

## Next Steps

1. **Explore the code**: Read through each module to understand patterns
2. **Modify for your needs**: Change chunking strategy, embedding model, etc
3. **Add tests**: Write unit tests for each module
4. **Benchmark**: Measure performance on your data
5. **Extend**: Add new features (Phase 2, 3, 4)

---

## Production Deployment

For production:

1. Use strong database passwords
2. Set `DEBUG=False`
3. Use environment-specific `.env` files
4. Deploy with production ASGI server (Gunicorn)
5. Use separate PostgreSQL instance
6. Monitor with logging/telemetry
7. Use secrets management (AWS Secrets Manager, etc)

---

## Support & Learning

Key files to study:
- `app/main.py` - Full pipeline
- `app/ingestion/chunker.py` - Token budgeting
- `app/embeddings/service.py` - Batch processing
- `app/vectorstore/chroma_store.py` - Vector operations
- Notebook for high-level concepts

This is production-grade code. Study it carefully.

