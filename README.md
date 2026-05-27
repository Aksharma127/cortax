# Cortex: Autonomous Research & Intelligence System

**Production-Grade Document Ingestion Pipeline for Enterprise AI**

This is not a toy chatbot project. This is enterprise-level AI backend engineering designed to teach real-world patterns and practices.

## I am  Building

A complete, industrial-strength document ingestion pipeline that:

✅ Ingests multiple document formats (PDF, DOCX, TXT, Markdown)  
✅ Extracts and cleans text intelligently  
✅ Tokenizes and chunks with semantic awareness  
✅ Generates embeddings with batch processing  
✅ Stores in PostgreSQL for metadata & queries  
✅ Indexes in ChromaDB for semantic search  
✅ Serves via FastAPI with full type safety  
✅ Runs asynchronously for scalability  
✅ Includes comprehensive logging & error handling  
✅ Follows enterprise architecture patterns  


This demonstrates real backend engineering, not toy projects.

| Area | Topics |
|------|--------|
| **Backend** | FastAPI, Uvicorn, async/await, dependency injection |
| **Databases** | SQLAlchemy ORM, connection pooling, indexing, relationships |
| **AI/ML** | Embeddings, tokenization, chunking strategies, batch processing |
| **Vector Databases** | ChromaDB, similarity search, metadata filtering, persistence |
| **Document Systems** | Multi-format parsing, text normalization, PDF extraction |
| **Production Patterns** | Type safety, validation, logging, error handling, configuration |
| **Architecture** | Separation of concerns, modular design, extensibility |
| **DevOps** | Docker, environment setup, deployment preparation |

## Project Structure

```
cortex/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # Route handlers
│   │   ├── core/              # Configuration
│   │   ├── db/                # Database setup
│   │   ├── ingestion/         # Document loading, extraction, chunking
│   │   ├── embeddings/        # Embedding generation
│   │   ├── vectorstore/       # Vector DB integration
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic validation
│   │   ├── services/          # Business logic
│   │   └── utils/             # Utilities
│   ├── tests/                 # Test suite
│   ├── requirements.txt       # Dependencies
│   ├── Dockerfile             # Container definition
│   └── .env.example           # Configuration template
│
├── notebooks/                 # Learning notebooks
│   ├── phase_1_deep_breakdown.ipynb
│   └── phase_1_implementation_guide.ipynb
│
├── docker-compose.yml         # Full stack orchestration
├── SETUP_GUIDE.md            # Quick start guide
└── README.md                 # This file
```

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Docker (optional)

### 1. Clone & Navigate

```bash
cd cortex/backend
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Database

**With Docker:**
```bash
docker run --name cortex-db \
  -e POSTGRES_DB=cortex_db \
  -e POSTGRES_USER=cortex \
  -e POSTGRES_PASSWORD=cortex \
  -p 5432:5432 \
  postgres:15
```

**Or locally:**
```bash
createdb cortex_db
```

### 4. Create .env File

```bash
cp .env.example .env
```

### 5. Run API Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 6. Visit API Docs

Open: **http://localhost:8000/api/docs**

## Using the API

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@research_paper.pdf"
```

Response:
```json
{
  "id": 1,
  "filename": "research_paper.pdf",
  "status": "completed",
  "total_chunks": 42,
  "total_tokens": 15230
}
```

### Search for Relevant Chunks

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main findings?", "k": 5}'
```

Response:
```json
{
  "query": "What are the main findings?",
  "results": [
    {
      "content": "Our study found that...",
      "distance": 0.92,
      "document_id": 1,
      "chunk_index": 5
    }
  ],
  "total_results": 1
}
```

### List Documents

```bash
curl "http://localhost:8000/api/documents"
```

### Health Check

```bash
curl "http://localhost:8000/health"
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│          FastAPI Application            │
│     Type-Safe | Async | Documented      │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┼──────────┬────────────┐
    ▼         ▼          ▼            ▼
┌────────┐ ┌──────────┐ ┌──────┐ ┌────────┐
│Document│ │Text      │ │Token │ │Embedding
│Loader  │ │Extractor │ │izer  │ │Service
│        │ │          │ │      │ │
│- Parse │ │- Clean   │ │- Count│ │- Batch
│- Validate│ │- Normalize│ │- Budget│ │- Async
└────────┘ └──────────┘ └──────┘ └────────┘
    │         │          │            │
    └─────────┼──────────┴────────────┘
              ▼
         ┌─────────────┐
         │   Chunker   │
         │             │
         │- Strategies │
         │- Overlaps   │
         │- Metadata   │
         └──────┬──────┘
                ▼
        ┌───────────────┐
        │  PostgreSQL   │ ◄─── Metadata & Relationships
        │               │
        │ - Documents   │
        │ - Chunks      │
        │ - Users       │
        │ - Logs        │
        └───────────────┘
                
        ┌───────────────┐
        │   ChromaDB    │ ◄─── Vector Search & Storage
        │               │
        │ - Embeddings  │
        │ - Similarity  │
        │ - Metadata    │
        └───────────────┘
```

## Core Modules Explained

### 1. Document Loader (`app/ingestion/loader.py`)
- Multi-format support (PDF, DOCX, TXT, MD)
- File validation (size, type, content)
- Security checks (zip bombs, malformed files)
- Async file operations

### 2. Text Extractor (`app/ingestion/extractor.py`)
- Unicode normalization
- PDF extraction cleanup
- Whitespace normalization
- Page number removal
- Header/footer detection

### 3. Chunker (`app/ingestion/chunker.py`)
- Fixed token chunking (baseline)
- Sentence window chunking (quality)
- Semantic chunking (advanced)
- Token counting
- Overlap strategies

### 4. Embedding Service (`app/embeddings/service.py`)
- Model loading & caching
- Batch processing (10-100x faster)
- Async support
- Similarity computation
- Dimension handling

### 5. Vector Store (`app/vectorstore/chroma_store.py`)
- Document storage
- Similarity search
- Metadata filtering
- Collection management
- Persistence

### 6. Database (`app/db/database.py`, `app/models/models.py`)
- Connection pooling
- Session management
- Relationship modeling
- Indexes for performance
- Status tracking

### 7. API (`app/main.py`)
- FastAPI application
- Type-safe request/response
- Dependency injection
- Error handling
- Full pipeline orchestration

## Configuration

See `.env.example` for all available options:

```env
# Database
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex_db

# Embeddings
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=100

# File Upload
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=pdf,txt,docx,md
```

## Testing

Run tests:

```bash
pytest tests/
```

Key things to test:
- Text cleaning edge cases
- Chunking correctness
- Embedding consistency
- Database operations
- API endpoints

## Production Deployment

### Using Docker Compose

```bash
cd cortex
docker-compose up -d
```

### Configuration for Production

```env
ENVIRONMENT=production
DEBUG=False
EMBEDDING_DEVICE=cuda  # If you have GPU
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

### Security Checklist

- [ ] Use strong database passwords
- [ ] Set `DEBUG=False`
- [ ] Use HTTPS in production
- [ ] Implement rate limiting
- [ ] Add authentication
- [ ] Use secrets manager
- [ ] Enable request logging
- [ ] Monitor error rates

## Learning Outcomes



## Key Differentiators

### Compared to Tutorial Code

| Aspect | Tutorial | This Project |
|--------|----------|--------------|
| Structure | Single file | Modular architecture |
| Type Safety | Optional | Required everywhere |
| Error Handling | Minimal | Comprehensive |
| Configuration | Hardcoded | Environment-based |
| Database | SQLite | PostgreSQL + pooling |
| Async | Rarely used | Full async/await |
| Logging | Print statements | Professional logging |
| Documentation | Comments | Docstrings + notebooks |
| Deployment | Not covered | Docker ready |

### What Recruiters See

This project signals:
- **Production thinking**: Architecture matters
- **Backend engineering**: Not just ML
- **Scalability awareness**: Async, pooling, batching
- **Type safety**: Professional code practices
- **DevOps knowledge**: Docker, configuration
- **Systems thinking**: Database design, relationships
- **Real-world experience**: Error handling, logging

NOT:
- Another chatbot tutorial
- Notebook-only work
- Copy-pasted code

## Next Phases

### Phase 2: Retrieval Intelligence
- Hybrid search (semantic + keyword BM25)
- Cross-encoder reranking
- Query rewriting with LLM
- Context compression

### Phase 3: Agentic Workflows
- Multi-agent orchestration with LangGraph
- State management
- Conditional routing
- Tool use and memory

### Phase 4: Conversational Memory
- Session management
- Long-term memory storage
- Context window optimization
- User preference tracking

### Phase 5-7: Advanced Features
- Streaming responses
- Local LLM serving (Ollama)
- Semantic caching
- Multi-user authentication
- Analytics dashboard

## Resources

### Learning Notebooks

1. `notebooks/phase_1_deep_breakdown.ipynb` - Concepts
2. `notebooks/phase_1_implementation_guide.ipynb` - Code walkthrough

### Documentation

- `SETUP_GUIDE.md` - Quick start
- Code comments - Inline explanations
- Docstrings - Function documentation

### External Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG Best Practices](https://github.com/langchain-ai/langchain)

## Troubleshooting

### "connection refused" on PostgreSQL

```bash
# Make sure PostgreSQL is running
docker-compose up -d postgres

# Or check local installation
brew services start postgresql
```

### "CUDA out of memory"

Set in `.env`:
```env
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=8  # Reduce batch size
```

### "Model download timeout"

First download takes time. Models are cached in `~/.cache/huggingface/`

Use smaller model:
```env
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

## Support

For questions, open issues on GitHub or check the notebooks for detailed explanations.

## License

This project is for educational purposes. Use freely for learning.

---

**Last Updated**:  28 May 2026 
**Python Version**: 3.10+  
**Status**: Production-ready Phase 1

