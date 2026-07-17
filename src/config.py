"""Central configuration for the RAG application.

All tunable settings live here and are sourced from environment variables
(with sensible defaults), so the rest of the codebase never reads os.environ
directly. This keeps configuration a single, swappable seam.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env_str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    value = os.environ.get(key)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_path(key: str, default: Path) -> Path:
    value = os.environ.get(key)
    if value is None or value.strip() == "":
        return default
    return Path(value)


@dataclass(frozen=True)
class Config:
    """Immutable application configuration.

    Instantiate via Config.load() rather than the constructor directly so
    environment variables are consulted consistently.
    """
    print("Created Config Object")

    # Directories
    documents_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "documents")
    vectorstore_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "vectorstore")

    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 100

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    # Retrieval
    top_k: int = 5

    # LLM (Ollama)
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 120

    # Logging
    log_level: str = "INFO"

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def faiss_index_path(self) -> Path:
        return self.vectorstore_dir / "index.faiss"

    @property
    def metadata_path(self) -> Path:
        return self.vectorstore_dir / "metadata.json"

    @classmethod
    def load(cls) -> "Config":
        """Build a Config from environment variables, falling back to defaults."""
        return cls(
            documents_dir=_env_path("DOCUMENTS_DIR", PROJECT_ROOT / "documents"),
            vectorstore_dir=_env_path("VECTORSTORE_DIR", PROJECT_ROOT / "vectorstore"),
            chunk_size=_env_int("CHUNK_SIZE", 500),
            chunk_overlap=_env_int("CHUNK_OVERLAP", 100),
            embedding_model=_env_str("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            top_k=_env_int("TOP_K", 5),
            ollama_model=_env_str("OLLAMA_MODEL", "llama3.2"),
            ollama_base_url=_env_str("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_timeout=_env_int("OLLAMA_TIMEOUT", 120),
            log_level=_env_str("LOG_LEVEL", "INFO"),
            api_host=_env_str("API_HOST", "0.0.0.0"),
            api_port=_env_int("API_PORT", 8000),
        )
    print("Runnign Config.load()")

    def ensure_directories(self) -> None:
        logger.info("ensure_directories - making sure /documents and /vectorstore dirs are created")
        """Create required directories if they don't already exist."""
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.vectorstore_dir.mkdir(parents=True, exist_ok=True)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once for the whole application."""
    print("configure_logging - RUNNING")
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    print("Logging is set up and now LIVE!")
