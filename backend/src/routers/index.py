"""Index lifecycle endpoints: rebuild and delete."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_rag_service
from src.models import DeleteIndexResponse, IndexResponse
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["index"])


@router.post(
    "/index",
    response_model=IndexResponse,
    summary="Rebuild the index",
    description=(
        "Re-reads every PDF in the documents directory, re-chunks and re-embeds them, "
        "and rebuilds the FAISS index from scratch."
    ),
)
async def rebuild_index(service: RAGService = Depends(get_rag_service)) -> IndexResponse:
    stats = service.rebuild_index()
    return IndexResponse(
        documents_processed=stats.documents_processed,
        chunks_created=stats.chunks_created,
        elapsed_seconds=stats.elapsed_seconds,
    )


@router.delete(
    "/index",
    response_model=DeleteIndexResponse,
    summary="Delete the index",
    description="Deletes the persisted FAISS index and metadata from disk.",
    responses={404: {"description": "No index exists to delete"}},
)
async def delete_index(service: RAGService = Depends(get_rag_service)) -> DeleteIndexResponse:
    deleted = service.delete_index()
    if not deleted:
        raise HTTPException(status_code=404, detail="No index exists to delete")
    return DeleteIndexResponse(deleted=True)
