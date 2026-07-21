"""RAG orchestration: ties ingestion, retrieval, and generation together.

This module is the only place that knows about all the other components. It
depends on interfaces (EmbeddingService, VectorStore, LLMService) rather than
concrete providers, so any of them can be swapped without changes here.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.chunker import RecursiveCharacterChunker, build_chunks
from src.config import Config
from src.embeddings import EmbeddingService
from src.llm import LLMService
from src.pdf_loader import PDFLoader
from src.vector_store import ChunkMetadata, SearchResult, VectorStore

logger = logging.getLogger(__name__)


class EmptyDocumentDirectoryError(Exception):
    """Raised when no PDFs are found and no existing index can be loaded."""


class IndexNotReadyError(RuntimeError):
    """Raised when an operation needs an index but none is loaded."""


@dataclass(frozen=True)
class Answer:
    """The result of answering a question: the LLM's text plus its sources."""

    text: str
    sources: List[ChunkMetadata]


@dataclass(frozen=True)
class IndexStats:
    """Stats describing the outcome of a full index rebuild."""

    documents_processed: int
    chunks_created: int
    elapsed_seconds: float


@dataclass(frozen=True)
class DocumentInfo:
    """Summary of a single document's presence in the index."""

    filename: str
    page_count: int
    chunk_count: int


class PromptBuilder:
    """Builds the prompt sent to the LLM from retrieved context and a question."""

    TEMPLATE = (
        "You are a helpful assistant.\n\n"
        "Answer ONLY using the provided context.\n\n"
        "If the answer is not contained in the context, clearly state that you don't know.\n\n"
        "Context:\n{context}\n\n"
        "Question:\n{question}\n\n"
        "Answer:"
    )

    def build(self, results: List[SearchResult], question: str) -> str:
        logger.info("Creating PromptBuilder.build()")

        context = "\n\n".join(f"[{r.metadata.filename} p.{r.metadata.page_number}] {r.metadata.chunk_text}" for r in results)
        return self.TEMPLATE.format(context=context, question=question)


class Retriever:
    """Embeds a query and fetches the most relevant chunks from the vector store."""

    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore, top_k: int = 5):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.top_k = top_k
        logger.info("Creating Retriever Object")

    def retrieve(self, question: str) -> List[SearchResult]:
        logger.info("Creating Retriever.retrieve()")
        logger.info("Retrieving top-%d chunks for question", self.top_k)
        query_embedding = self.embedding_service.embed_query(question) #turn question into an embeded number
        return self.vector_store.search(query_embedding, self.top_k)

 
class RAGPipeline:
    """Coordinates ingestion (build/load index) and question answering."""

    def __init__(self, config: Config, embedding_service: EmbeddingService, llm_service: LLMService):
        self.config = config
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.prompt_builder = PromptBuilder()
        self.vector_store: VectorStore | None = None
        logger.info("Creating RAGPipeline Object")


    def initialize(self) -> None:
        logger.info("Runnign RAGPipeline.initialize()")
        """Load an existing index if present, otherwise build one from PDFs."""
        if VectorStore.exists(self.config.faiss_index_path, self.config.metadata_path):
            logger.info("Existing index found, loading from disk")
            self.vector_store = VectorStore.load(self.config.faiss_index_path, self.config.metadata_path)
        else:
            logger.info("No existing index found, building a new one")
            self.vector_store = self._build_index()

    def _build_index(self) -> VectorStore:
        logger.info("Runnign RAGPipeline._build_index()")
        loader = PDFLoader(self.config.documents_dir)
        chunker = RecursiveCharacterChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

        pages = list(loader.load_all())
        if not pages:
            raise EmptyDocumentDirectoryError(
                f"No readable PDF content found in '{self.config.documents_dir}'. "
                "Add PDF files to that directory and try again."
            )

        all_chunks = []
        for page in pages:
            chunks = build_chunks(page.filename, page.page_number, page.text, chunker, start_id=len(all_chunks))
            all_chunks.extend(chunks)
        logger.info("Created %d total chunk(s) from %d page(s)", len(all_chunks), len(pages))

        texts = [c.text for c in all_chunks]
        embeddings = self.embedding_service.embed_texts(texts)

        store = VectorStore(dimension=self.embedding_service.dimension)
        metadata = [
            ChunkMetadata(filename=c.filename, page_number=c.page_number, chunk_id=c.chunk_id, chunk_text=c.text)
            for c in all_chunks
        ]
        store.add(embeddings, metadata)
        store.save(self.config.faiss_index_path, self.config.metadata_path)
        return store

    def answer(self, question: str) -> Answer:
        """Retrieve relevant context and generate an answer from the LLM."""
        logger.info("Runnign RAGPipeline.answer()")
        if self.vector_store is None:
            raise IndexNotReadyError(
                "No index is loaded. Add PDFs to the documents directory and rebuild the index first."
            )

        retriever = Retriever(self.embedding_service, self.vector_store, top_k=self.config.top_k)
        retrieval_start = time.monotonic()
        results = retriever.retrieve(question)
        retrieval_elapsed = time.monotonic() - retrieval_start
        logger.info("Retrieved %d chunk(s) in %.3fs", len(results), retrieval_elapsed)

        if not results:
            return Answer(text="I don't know. No relevant context was found in the indexed documents.", sources=[])

        prompt = self.prompt_builder.build(results, question)

        generation_start = time.monotonic()
        text = self.llm_service.generate(prompt)
        generation_elapsed = time.monotonic() - generation_start
        logger.info("LLM generated response in %.3fs", generation_elapsed)

        sources = [r.metadata for r in results]
        return Answer(text=text, sources=sources)

    def rebuild_index(self) -> IndexStats:
        """Force a full rebuild of the index from the documents directory."""
        logger.info("Running RAGPipeline.rebuild_index()")
        start = time.monotonic()
        self.vector_store = self._build_index()
        elapsed = time.monotonic() - start

        metadata = self.vector_store.all_metadata()
        documents_processed = len({m.filename for m in metadata})
        chunks_created = len(metadata)
        logger.info(
            "Index rebuilt: %d document(s), %d chunk(s) in %.2fs",
            documents_processed,
            chunks_created,
            elapsed,
        )
        return IndexStats(
            documents_processed=documents_processed,
            chunks_created=chunks_created,
            elapsed_seconds=elapsed,
        )

    def list_documents(self) -> List[DocumentInfo]:
        """Return a summary of every document currently represented in the index."""
        logger.info("Running RAGPipeline.list_documents()")
        if self.vector_store is None:
            raise IndexNotReadyError("No index is loaded. Rebuild the index first.")

        pages_by_file: dict[str, set[int]] = {}
        chunks_by_file: dict[str, int] = {}
        for m in self.vector_store.all_metadata():
            pages_by_file.setdefault(m.filename, set()).add(m.page_number)
            chunks_by_file[m.filename] = chunks_by_file.get(m.filename, 0) + 1

        return [
            DocumentInfo(filename=f, page_count=len(pages_by_file[f]), chunk_count=chunks_by_file[f])
            for f in sorted(pages_by_file)
        ]

    def delete_index(self) -> bool:
        """Delete the persisted index from disk. Returns True if one existed."""
        logger.info("Running RAGPipeline.delete_index()")
        existed = VectorStore.exists(self.config.faiss_index_path, self.config.metadata_path)
        if existed:
            self.config.faiss_index_path.unlink(missing_ok=True)
            self.config.metadata_path.unlink(missing_ok=True)
            logger.info("Deleted index at %s and %s", self.config.faiss_index_path, self.config.metadata_path)
        self.vector_store = None
        return existed
exit