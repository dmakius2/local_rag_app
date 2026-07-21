"""Pydantic request/response models for the FastAPI layer.

Kept separate from the RAG engine's own dataclasses (src/rag.py) so the HTTP
schema can evolve independently of internal orchestration types.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """Service liveness status."""
    print("BACKEND: HealthResponse()")
    status: str = Field(description="Service health status", examples=["healthy"])


class ChatRequest(BaseModel):
    """A question to ask the indexed documents."""

    question: str = Field(
        min_length=1,
        description="Natural-language question to ask the indexed documents",
        examples=["What is Kubernetes?"],
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value


class SourceModel(BaseModel):
    """A single document/page an answer was drawn from."""

    document: str = Field(description="Source PDF filename")
    page: int = Field(description="1-indexed page number within the source document")
    chunk_text: str = Field(description="Retrieved chunk text this answer was grounded in")


class ChatResponse(BaseModel):
    """The generated answer plus the sources it was grounded in."""

    answer: str = Field(description="Generated answer grounded in retrieved context")
    sources: List[SourceModel] = Field(default_factory=list, description="Documents/pages the answer was drawn from")


class IndexResponse(BaseModel):
    """Result of rebuilding the FAISS index."""

    documents_processed: int = Field(description="Number of PDF documents processed")
    chunks_created: int = Field(description="Number of text chunks embedded and stored")
    elapsed_seconds: float = Field(description="Time taken to rebuild the index, in seconds")


class DocumentModel(BaseModel):
    """Summary of a single indexed document."""

    filename: str = Field(description="PDF filename")
    pages: int = Field(description="Number of indexed pages for this document")
    chunks: int = Field(description="Number of indexed chunks for this document")


class DocumentsResponse(BaseModel):
    """All documents currently represented in the index."""

    documents: List[DocumentModel] = Field(default_factory=list, description="All currently indexed documents")


class DeleteIndexResponse(BaseModel):
    """Result of deleting the index."""

    deleted: bool = Field(description="Whether an existing index was found and deleted")


class ErrorResponse(BaseModel):
    """Standard error payload. Never contains stack traces."""

    detail: str = Field(description="Human-readable error message")
