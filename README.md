# Local RAG

A fully local Retrieval Augmented Generation (RAG) application. Ask questions
about your own PDF documents and get answers grounded in their content —
no cloud AI services, no API keys, no data leaving your machine.

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
  names, directories, log level) lives in one config module and can be
  overridden via environment variables or `.env`.

## Architecture

```text
                User
                  │
             CLI Application (main.py)
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

Each component communicates through a small, explicit interface:

| Component        | File                | Responsibility                                  |
|-------------------|---------------------|--------------------------------------------------|
| PDF Loader        | `pdf_loader.py`     | Discover PDFs, extract text per page             |
| Chunker           | `chunker.py`        | Split page text into overlapping chunks          |
| Embedding Service | `embeddings.py`     | Turn text into vectors (Sentence Transformers)   |
| Vector Store      | `vector_store.py`   | Persist/search embeddings + metadata (FAISS)     |
| Retriever         | `rag.py`            | Embed a query, fetch top-k similar chunks        |
| Prompt Builder    | `rag.py`            | Assemble the grounded prompt template            |
| LLM Service       | `llm.py`            | Generate an answer from a prompt (Ollama today)  |
| RAG Orchestrator  | `rag.py`            | Wire the above into build-index / answer flows   |

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

Edit `.env` if you want to change the model, chunk size, top-k, or
directories. All settings have sensible defaults, so this step is optional.

## Running the application

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
contents of `vectorstore/` and run the app again.

## Project structure

```text
local-rag/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── documents/          # Drop your PDFs here
├── vectorstore/         # FAISS index + metadata (generated)
├── src/
│   ├── __init__.py
│   ├── config.py        # Central configuration
│   ├── pdf_loader.py     # PDF discovery + text extraction
│   ├── chunker.py        # Recursive character chunking
│   ├── embeddings.py     # Sentence Transformers embedding service
│   ├── vector_store.py   # FAISS index + metadata persistence
│   ├── llm.py            # LLM provider interface + Ollama implementation
│   ├── rag.py            # Retriever, prompt builder, RAG orchestrator
│   └── main.py           # Interactive CLI entrypoint
└── tests/
    ├── test_config.py
    ├── test_chunker.py
    ├── test_pdf_loader.py
    └── test_vector_store.py
```

## Running tests

```bash
pytest
```

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

## Error handling

The app fails gracefully and prints actionable messages for:

- Ollama not installed / not running
- Requested Ollama model not pulled
- Empty or missing `documents/` directory
- Invalid or unreadable PDFs (skipped, ingestion continues)
- Missing or corrupt FAISS index (rebuilt automatically)
- Embedding generation failures

## Future roadmap

Version 0.1 is intentionally scoped to a local CLI, but the architecture is
designed to grow without rework:

- **FastAPI REST API** — wrap `RAGPipeline` in HTTP endpoints; no changes to
  ingestion or retrieval logic required.
- **React frontend** — consume the future REST API.
- **Docker** — containerize the app and an Ollama sidecar.
- **User authentication** — add an auth layer in front of the API.
- **Amazon S3** — swap the document source behind a new loader implementing
  the same interface as `PDFLoader`.
- **PostgreSQL / pgvector** — implement an alternative to `VectorStore` with
  the same interface for teams needing a shared, scalable vector DB.
- **Background indexing workers** — move `RAGPipeline._build_index` into an
  async task queue for large document sets.
- **Multiple LLM providers** — add `OpenAILLMService`, `ClaudeLLMService`,
  etc., all implementing `LLMService`.
- **Streaming responses** — extend `LLMService.generate` with a streaming
  variant, surfaced through the CLI/API as tokens arrive.
- **Kubernetes** — deploy the containerized API and workers to a cluster.
