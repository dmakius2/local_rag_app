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
from src.dependencies import get_rag_service
from src.rag import Answer, DocumentInfo, IndexNotReadyError, IndexStats
from src.vector_store import ChunkMetadata


class FakeRAGService:
    def __init__(self):
        self.rebuild_calls = 0
        self.delete_calls = 0
        self.deleted_result = True
        self.raise_on_chat: Exception | None = None

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


@pytest.fixture
def fake_service():
    return FakeRAGService()


@pytest.fixture
def client(fake_service):
    app.dependency_overrides[get_rag_service] = lambda: fake_service
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
