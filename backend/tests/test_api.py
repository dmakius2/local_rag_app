"""Tests for the FastAPI HTTP layer.

These exercise routing, validation, status codes, and response shaping only.
The real RAGService (embeddings, FAISS, Ollama) is replaced with a fake via
dependency override, so these tests don't require a model download or a
running Ollama server and don't trigger the app's lifespan startup.
"""
from __future__ import annotations

from typing import List

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.config import Config
from src.dependencies import get_config, get_rag_service
from src.rag import Answer, DocumentInfo, IndexNotReadyError, IndexStats
from src.vector_store import ChunkMetadata


class FakeRAGService:
    def __init__(self):
        self.rebuild_calls = 0
        self.delete_calls = 0
        self.deleted_result = True
        self.raise_on_chat: Exception | None = None
        self.delete_document_calls: List[str] = []
        self.delete_document_result = True

    def chat(self, question: str) -> Answer:
        if self.raise_on_chat:
            raise self.raise_on_chat
        return Answer(
            text="Kubernetes is a container orchestration platform.",
            sources=[ChunkMetadata(filename="k8s.pdf", page_number=5, chunk_id=0, chunk_text="some context")],
        )

    def rebuild_index(self) -> IndexStats:
        self.rebuild_calls += 1
        return IndexStats(documents_processed=2, chunks_created=10, elapsed_seconds=0.5)

    def list_documents(self) -> List[DocumentInfo]:
        return [DocumentInfo(filename="k8s.pdf", page_count=5, chunk_count=10)]

    def delete_index(self) -> bool:
        self.delete_calls += 1
        return self.deleted_result

    def delete_document(self, filename: str) -> bool:
        self.delete_document_calls.append(filename)
        return self.delete_document_result


@pytest.fixture
def fake_service():
    return FakeRAGService()


@pytest.fixture
def test_config(tmp_path):
    documents_dir = tmp_path / "documents"
    documents_dir.mkdir()
    return Config(documents_dir=documents_dir, vectorstore_dir=tmp_path / "vectorstore")


@pytest.fixture
def client(fake_service, test_config):
    app.dependency_overrides[get_rag_service] = lambda: fake_service
    app.dependency_overrides[get_config] = lambda: test_config
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_returns_healthy(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_chat_returns_answer_and_sources(client):
    response = client.post("/chat", json={"question": "What is Kubernetes?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Kubernetes is a container orchestration platform."
    assert body["sources"] == [{"document": "k8s.pdf", "page": 5, "chunk_text": "some context"}]


def test_chat_rejects_blank_question(client):
    response = client.post("/chat", json={"question": "   "})

    assert response.status_code == 422


def test_chat_rejects_missing_question(client):
    response = client.post("/chat", json={})

    assert response.status_code == 422


def test_chat_returns_400_when_index_not_ready(client, fake_service):
    fake_service.raise_on_chat = IndexNotReadyError("No index is loaded.")

    response = client.post("/chat", json={"question": "What is Kubernetes?"})

    assert response.status_code == 400
    assert response.json() == {"detail": "No index is loaded."}


def test_rebuild_index_returns_stats(client, fake_service):
    response = client.post("/index")

    assert response.status_code == 200
    assert response.json() == {"documents_processed": 2, "chunks_created": 10, "elapsed_seconds": 0.5}
    assert fake_service.rebuild_calls == 1


def test_delete_index_returns_deleted_true(client, fake_service):
    fake_service.deleted_result = True

    response = client.delete("/index")

    assert response.status_code == 200
    assert response.json() == {"deleted": True}


def test_delete_index_returns_404_when_nothing_to_delete(client, fake_service):
    fake_service.deleted_result = False

    response = client.delete("/index")

    assert response.status_code == 404


def test_list_documents_returns_summaries(client):
    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == {"documents": [{"filename": "k8s.pdf", "pages": 5, "chunks": 10}]}


def test_upload_documents_saves_files_to_documents_dir(client, test_config):
    response = client.post(
        "/documents",
        files=[
            ("files", ("notes.txt", b"hello world", "text/plain")),
            ("files", ("report.docx", b"fake docx bytes", "application/vnd.openxmlformats")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["uploaded"] == [
        {"filename": "notes.txt", "size_bytes": 11, "extractable": True},
        {"filename": "report.docx", "size_bytes": 15, "extractable": True},
    ]
    assert (test_config.documents_dir / "notes.txt").read_bytes() == b"hello world"
    assert (test_config.documents_dir / "report.docx").read_bytes() == b"fake docx bytes"


def test_upload_documents_marks_legacy_doc_as_not_extractable(client):
    response = client.post("/documents", files=[("files", ("legacy.doc", b"binary doc content", "application/msword"))])

    assert response.status_code == 200
    assert response.json()["uploaded"] == [{"filename": "legacy.doc", "size_bytes": 18, "extractable": False}]


def test_upload_documents_rejects_unsupported_extension(client, test_config):
    response = client.post("/documents", files=[("files", ("virus.exe", b"binary", "application/octet-stream"))])

    assert response.status_code == 400
    assert list(test_config.documents_dir.iterdir()) == []


def test_upload_documents_rejects_empty_file(client):
    response = client.post("/documents", files=[("files", ("empty.txt", b"", "text/plain"))])

    assert response.status_code == 400


def test_upload_documents_sanitizes_path_traversal_filename(client, test_config):
    response = client.post("/documents", files=[("files", ("../../etc/passwd.txt", b"content", "text/plain"))])

    assert response.status_code == 200
    assert response.json()["uploaded"][0]["filename"] == "passwd.txt"
    assert (test_config.documents_dir / "passwd.txt").exists()
    assert not (test_config.documents_dir.parent.parent / "etc").exists()


def test_delete_document_returns_deleted_true(client, fake_service):
    response = client.delete("/documents/k8s.pdf")

    assert response.status_code == 200
    assert response.json() == {"deleted": True, "filename": "k8s.pdf"}
    assert fake_service.delete_document_calls == ["k8s.pdf"]


def test_delete_document_returns_404_when_not_found(client, fake_service):
    fake_service.delete_document_result = False

    response = client.delete("/documents/missing.pdf")

    assert response.status_code == 404


def test_delete_document_rejects_path_traversal_via_encoded_slash(client, fake_service):
    response = client.delete("/documents/..%2F..%2Fetc%2Fpasswd")

    assert response.status_code == 404  # Starlette's routing doesn't match the encoded slash as one segment
    assert fake_service.delete_document_calls == []


def test_delete_document_rejects_dot_dot_segment(client, fake_service):
    response = client.delete("/documents/%2E%2E")

    assert response.status_code == 400
    assert fake_service.delete_document_calls == []
