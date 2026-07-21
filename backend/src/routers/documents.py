"""Indexed document listing endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.dependencies import get_rag_service
from src.models import DocumentModel, DocumentsResponse
from src.services.rag_service import RAGService

router = APIRouter(tags=["documents"])


@router.get(
    "/documents",
    response_model=DocumentsResponse,
    summary="List indexed documents",
    description="Returns every document currently represented in the vector index, with page and chunk counts.",
)
async def list_documents(service: RAGService = Depends(get_rag_service)) -> DocumentsResponse:
    docs = service.list_documents()
    return DocumentsResponse(
        documents=[DocumentModel(filename=d.filename, pages=d.page_count, chunks=d.chunk_count) for d in docs]
    )
