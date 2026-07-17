# Local RAG

A fully local Retrieval Augmented Generation (RAG) application. Ask questions
about your own PDF documents and get answers grounded in their content —
no cloud AI services, no API keys, no data leaving your machine.

Usable two ways: as an interactive CLI, or as a FastAPI REST service — both
run through the exact same `RAGService`, so behavior never diverges between
them.

## Features

- **Local by default** — embeddings run via Sentence Transformers, generation
  runs via [Ollama](https://ollama.com); nothing is sent to a third-party API.
- **PDF ingestion** — recursively reads every PDF in `documents/`, extracting
  text page by page with PyMuPDF.
- **Persistent vector index** — chunks are embedded and stored in a FAISS
  index under `vectorstore/`, with metadata (filename, page, chunk id, text)
  kept alongside it. The index is built once and reused on subsequent runs.
- **Source-attributed answers** — every answer lists which document(s) and
  page(s) it was drawn from.
- **Grounded prompting** — the LLM is instructed to answer only from
  retrieved context, and to say so explicitly when the answer isn't there.
- **Provider-agnostic LLM layer** — all Ollama-specific code lives behind a
  single `LLMService` interface, so swapping in OpenAI, Claude, Gemini, or
  another local model later doesn't touch the retrieval pipeline.
- **Centralized configuration** — every tunable (chunk size, top-k, model
  names, directories, log level, API host/port) lives in one config module
  and can be overridden via environment variables or `.env`.
- **CLI and REST API** — the interactive shell and a FastAPI HTTP service
  both call into the same `RAGService`, so there's a single orchestration
  path and no duplicated business logic.

## Architecture

```text
                        User
                          │
        ┌─────────────────┴─────────────────┐
        │                                    │
  CLI Application                    FastAPI Application
    (main.py)                             (api.py)
        │                                    │
        └─────────────────┬──────────────────┘
                           │
                     RAGService
              (services/rag_service.py)
                           │
                RAG Orchestrator (rag.py)
        ┌─────────┴─────────┐
        │                   │
 Embedding Service      LLM Service
  (embeddings.py)         (llm.py)
        │                   │
Sentence Transformers   Ollama HTTP API
        │
      FAISS
   (vector_store.py)
        │
     PDF Documents
   (pdf_loader.py, chunker.py)
```

`RAGService` is the single orchestration seam: it owns pipeline construction
and lifecycle, and is the only thing either entrypoint talks to. The CLI and
the API never call `RAGPipeline`, `EmbeddingService`, or `LLMService`
directly — the RAG engine itself has no knowledge of FastAPI or the CLI.

Each component communicates through a small, explicit interface:

| Component          | File                        | Responsibility                                       |
|---------------------|-----------------------------|--------------------------------------------------------|
| PDF Loader          | `pdf_loader.py`             | Discover PDFs, extract text per page                  |
| Chunker             | `chunker.py`                | Split page text into overlapping chunks               |
| Embedding Service   | `embeddings.py`             | Turn text into vectors (Sentence Transformers)        |
| Vector Store        | `vector_store.py`           | Persist/search embeddings + metadata (FAISS)          |
| Retriever           | `rag.py`                    | Embed a query, fetch top-k similar chunks             |
| Prompt Builder      | `rag.py`                    | Assemble the grounded prompt template                  |
| LLM Service         | `llm.py`                    | Generate an answer from a prompt (Ollama today)       |
| RAG Orchestrator    | `rag.py`                    | Wire the above into build-index / answer / index-mgmt |
| RAG Service         | `services/rag_service.py`   | Shared orchestration seam used by CLI and API          |
| CLI                 | `main.py`                   | Interactive shell entrypoint                           |
| FastAPI App         | `api.py`                    | HTTP entrypoint: middleware, exception handling        |
| Routers             | `routers/*.py`              | Endpoint definitions per resource                       |
| Pydantic Models     | `models.py`                 | Request/response validation and OpenAPI schema         |

This separation is deliberate: any single component can be replaced (a new
chunking strategy, a cloud vector DB, a different LLM provider) without
touching the others.

## Installation

### 1. Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com), or via
Homebrew on macOS:

```bash
brew install ollama
```

Start the Ollama server (if it isn't already running as a background service):

```bash
ollama serve
```

### 2. Pull the default model

```bash
ollama pull llama3.2
```

You can use a different model by changing `OLLAMA_MODEL` in your `.env` file
(see below) — no code changes required.

### 3. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` if you want to change the model, chunk size, top-k, API host/port,
or directories. All settings have sensible defaults, so this step is optional.

## Running the CLI

1. Add one or more PDF files to the `documents/` directory.
2. Launch the interactive shell:

   ```bash
   python src/main.py
   ```

3. On first run, the app extracts text, chunks it, generates embeddings, and
   builds a FAISS index under `vectorstore/`. On subsequent runs, it loads
   the existing index instead of rebuilding it.
4. Ask questions:

   ```text
   Question: What is Kubernetes?

   Answer:
   Kubernetes is ...

   Sources:
     - k8s-overview.pdf (page 3)
   ```

5. Type `exit` (or `quit`, or Ctrl+D) to leave the shell.

To force a rebuild of the index (e.g. after adding new PDFs), delete the
contents of `vectorstore/` and run the app again, or use `POST /index` on
the API (see below) — either entrypoint calls the same rebuild logic.

## Running the FastAPI server

The API wraps the same `RAGService` the CLI uses, so it needs the same
Ollama server and `documents/` setup described above.

Start it with uvicorn:

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

or, using the values from `.env` (`API_HOST` / `API_PORT`):

```bash
python src/api.py
```

Add `--reload` to the uvicorn command for autoreload during development.

### Swagger UI / OpenAPI docs

Once running, interactive API documentation is available at:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Raw OpenAPI schema: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

Every endpoint has a summary, description, and typed request/response model,
so the schema is fully generated from the code — no hand-written API docs to
keep in sync.

### Endpoints

| Method | Path         | Description                                              |
|--------|--------------|------------------------------------------------------------|
| GET    | `/health`    | Liveness check                                            |
| POST   | `/chat`      | Ask a question, get a grounded answer + sources           |
| POST   | `/index`     | Rebuild the FAISS index from `documents/`                 |
| DELETE | `/index`     | Delete the persisted index                                 |
| GET    | `/documents` | List documents currently represented in the index         |

### curl examples

```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Kubernetes?"}'

# Rebuild the index after adding new PDFs to documents/
curl -X POST http://localhost:8000/index

# List indexed documents
curl http://localhost:8000/documents

# Delete the index
curl -X DELETE http://localhost:8000/index
```

Example `/chat` response:

```json
{
  "answer": "Kubernetes is a container orchestration platform...",
  "sources": [
    { "document": "k8s-overview.pdf", "page": 3 }
  ]
}
```

Example `/index` response:

```json
{
  "documents_processed": 2,
  "chunks_created": 134,
  "elapsed_seconds": 4.12
}
```

## Project structure

```text
local-rag/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── documents/              # Drop your PDFs here
├── vectorstore/             # FAISS index + metadata (generated)
├── src/
│   ├── __init__.py
│   ├── config.py             # Central configuration
│   ├── pdf_loader.py         # PDF discovery + text extraction
│   ├── chunker.py            # Recursive character chunking
│   ├── embeddings.py         # Sentence Transformers embedding service
│   ├── vector_store.py       # FAISS index + metadata persistence
│   ├── llm.py                # LLM provider interface + Ollama implementation
│   ├── rag.py                # Retriever, prompt builder, RAG orchestrator
│   ├── main.py                # Interactive CLI entrypoint
│   ├── api.py                 # FastAPI app: middleware, exception handlers
│   ├── dependencies.py        # FastAPI dependency providers
│   ├── models.py              # Pydantic request/response models
│   ├── services/
│   │   └── rag_service.py     # Shared orchestration seam (CLI + API)
│   └── routers/
│       ├── health.py          # GET /health
│       ├── chat.py            # POST /chat
│       ├── index.py           # POST /index, DELETE /index
│       └── documents.py       # GET /documents
└── tests/
    ├── test_config.py
    ├── test_chunker.py
    ├── test_pdf_loader.py
    ├── test_vector_store.py
    └── test_api.py
```

## Running tests

```bash
pytest
```

`tests/test_api.py` covers the HTTP layer (health, chat, index) using
FastAPI's `TestClient` with a fake `RAGService` injected via dependency
override, so it doesn't require a running Ollama server or a downloaded
embedding model.

## Configuration reference

All settings can be set via environment variables or `.env`:

| Variable           | Default              | Description                              |
|--------------------|----------------------|-------------------------------------------|
| `OLLAMA_MODEL`     | `llama3.2`           | Ollama model used for generation          |
| `OLLAMA_BASE_URL`  | `http://localhost:11434` | Ollama server URL                    |
| `OLLAMA_TIMEOUT`   | `120`                | Request timeout (seconds)                 |
| `EMBEDDING_MODEL`  | `all-MiniLM-L6-v2`   | Sentence Transformers model name          |
| `TOP_K`            | `5`                  | Number of chunks retrieved per question   |
| `CHUNK_SIZE`       | `500`                | Max characters per chunk                  |
| `CHUNK_OVERLAP`    | `100`                | Overlap between consecutive chunks        |
| `DOCUMENTS_DIR`    | `documents`          | Where to read PDFs from                   |
| `VECTORSTORE_DIR`  | `vectorstore`        | Where the FAISS index + metadata live     |
| `LOG_LEVEL`        | `INFO`               | Python logging level                      |
| `API_HOST`         | `0.0.0.0`            | Host the FastAPI server binds to          |
| `API_PORT`         | `8000`               | Port the FastAPI server binds to          |

## Error handling

The RAG engine fails gracefully; the CLI prints actionable messages and the
API translates the same errors into HTTP status codes:

| Condition                                    | CLI behavior            | API status |
|-----------------------------------------------|--------------------------|------------|
| Ollama not installed / not running             | Prints error, keeps prompting | 503 |
| Requested Ollama model not pulled               | Prints error, keeps prompting | 503 |
| Empty/missing `documents/` directory (indexing) | Prints error, exits     | 400 |
| No index loaded yet (`/chat`, `/documents`)     | N/A (CLI always builds on startup) | 400 |
| `DELETE /index` with no index present           | N/A                      | 400 (CLI) / 404 (API) |
| Invalid or unreadable PDFs                       | Skipped, ingestion continues | Skipped, ingestion continues |
| Malformed/missing request fields                 | N/A                      | 422 |
| Unexpected internal error                        | Prints generic message, no traceback | 500, no traceback |

All error responses are `{"detail": "..."}` — stack traces are always logged
server-side, never returned in the response body.

## Logging

Every entrypoint logs through the same `configure_logging()` setup. In
addition to component-level logs, the RAG layer and API log:

- retrieved chunk counts and retrieval time
- LLM response time
- total chat processing time
- indexing duration, documents processed, and chunks created
- every incoming HTTP request/response with status code and elapsed time
  (via `api.py`'s logging middleware)

## Future roadmap

Version 0.2 adds a FastAPI REST layer on top of the same RAG engine. Planned
next:

- **React frontend** — consume the REST API.
- **Docker** — containerize the app and an Ollama sidecar.
- **User authentication** — add an auth layer in front of the API.
- **Amazon S3** — swap the document source behind a new loader implementing
  the same interface as `PDFLoader`.
- **PostgreSQL / pgvector** — implement an alternative to `VectorStore` with
  the same interface for teams needing a shared, scalable vector DB.
- **Background indexing workers** — move `RAGPipeline.rebuild_index` into an
  async task queue for large document sets, with an `/index/status` endpoint.
- **Multiple LLM providers** — add `OpenAILLMService`, `ClaudeLLMService`,
  etc., all implementing `LLMService`.
- **Streaming responses** — extend `LLMService.generate` with a streaming
  variant, surfaced through the CLI/API as tokens arrive.
- **Kubernetes** — deploy the containerized API and workers to a cluster.
