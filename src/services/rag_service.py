"""Service layer shared by the CLI and the FastAPI HTTP layer.

RAGService owns construction and lifecycle of the RAGPipeline so both
entrypoints run through identical orchestration logic. Neither the CLI nor
the API layer talks to EmbeddingService, LLMService, or RAGPipeline directly.
"""
from __future__ import annotations

import logging
import time
from typing import List

from src.config import Config
from src.embeddings import EmbeddingService
from src.llm import OllamaLLMService
from src.rag import Answer, DocumentInfo, IndexStats, RAGPipeline

logger = logging.getLogger(__name__)


class RAGService:
    """Thin orchestration wrapper around RAGPipeline used by every entrypoint."""

    def __init__(self, config: Config):
        self.config = config
        embedding_service = EmbeddingService(model_name=config.embedding_model)
        llm_service = OllamaLLMService(
            model=config.ollama_model,
            base_url=config.ollama_base_url,
            timeout=config.ollama_timeout,
        )
        self.pipeline = RAGPipeline(config=config, embedding_service=embedding_service, llm_service=llm_service)
        logger.info("Creating RAGService Object")

    def initialize(self) -> None:
        """Load an existing index if present, otherwise build one from PDFs."""
        self.pipeline.initialize()

    def chat(self, question: str) -> Answer:
        """Answer a question using the indexed documents."""
        start = time.monotonic()
        answer = self.pipeline.answer(question)
        elapsed = time.monotonic() - start
        logger.info("Processed chat request in %.3fs (%d source chunk(s))", elapsed, len(answer.sources))
        return answer

    def rebuild_index(self) -> IndexStats:
        """Rebuild the FAISS index from scratch and return stats about the run."""
        return self.pipeline.rebuild_index()

    def list_documents(self) -> List[DocumentInfo]:
        """Return a summary of every document currently represented in the index."""
        return self.pipeline.list_documents()

    def delete_index(self) -> bool:
        """Delete the persisted index. Returns True if one existed."""
        return self.pipeline.delete_index()
