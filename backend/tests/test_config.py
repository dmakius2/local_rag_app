import os

from src.config import Config


def test_default_config_values(monkeypatch):
    for key in [
        "CHUNK_SIZE", "CHUNK_OVERLAP", "EMBEDDING_MODEL", "TOP_K",
        "OLLAMA_MODEL", "OLLAMA_BASE_URL", "OLLAMA_TIMEOUT", "LOG_LEVEL",
        "DOCUMENTS_DIR", "VECTORSTORE_DIR",
    ]:
        monkeypatch.delenv(key, raising=False)

    config = Config.load()

    assert config.chunk_size == 500
    assert config.chunk_overlap == 100
    assert config.embedding_model == "all-MiniLM-L6-v2"
    assert config.top_k == 5
    assert config.ollama_model == "llama3.2"


def test_config_reads_environment_overrides(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "1000")
    monkeypatch.setenv("TOP_K", "3")
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")

    config = Config.load()

    assert config.chunk_size == 1000
    assert config.top_k == 3
    assert config.ollama_model == "mistral"


def test_index_and_metadata_paths_are_derived_from_vectorstore_dir(tmp_path):
    config = Config(vectorstore_dir=tmp_path)

    assert config.faiss_index_path == tmp_path / "index.faiss"
    assert config.metadata_path == tmp_path / "metadata.json"


def test_ensure_directories_creates_missing_dirs(tmp_path):
    docs_dir = tmp_path / "documents"
    store_dir = tmp_path / "vectorstore"
    config = Config(documents_dir=docs_dir, vectorstore_dir=store_dir)

    assert not docs_dir.exists()
    assert not store_dir.exists()

    config.ensure_directories()

    assert docs_dir.exists()
    assert store_dir.exists()
