"""Question-answering endpoint."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from src.dependencies import get_rag_service
from src.models import ChatRequest, ChatResponse, SourceModel
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a question",
    description=(
        "Retrieves the most relevant chunks from the indexed documents and generates "
        "an answer grounded in that context, along with the sources it was drawn from."
    ),
)
async def chat(request: ChatRequest, service: RAGService = Depends(get_rag_service)) -> ChatResponse:
    logger.info("Received chat request (question length=%d)", len(request.question))
    answer = service.chat(request.question)
    sources = [
        SourceModel(document=s.filename, page=s.page_number, chunk_text=s.chunk_text) for s in answer.sources
    ]
    return ChatResponse(answer=answer.text, sources=sources)
