"""FastAPI application exposing the RAG engine over HTTP.

This module only adapts src.services.RAGService to HTTP concerns (routing,
request/response validation, status codes, request logging). All RAG
orchestration logic lives in RAGService / RAGPipeline and is shared with the
CLI (src/main.py) — nothing here duplicates that logic.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config import Config, configure_logging
from src.llm import LLMConnectionError, LLMError, LLMModelNotFoundError
from src.models import ErrorResponse
from src.rag import EmptyDocumentDirectoryError, IndexNotReadyError
from src.routers import chat, documents, health, index
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config.load()
    configure_logging(config.log_level)
    config.ensure_directories()

    service = RAGService(config)
    try:
        service.initialize()
    except EmptyDocumentDirectoryError as exc:
        logger.warning("Starting API with no index loaded: %s", exc)

    app.state.rag_service = service
    app.state.config = config
    logger.info("RAG API startup complete")
    yield


app = FastAPI(
    title="Local RAG API",
    description=(
        "HTTP interface over a fully local Retrieval-Augmented Generation engine. "
        "The same RAGService instance backs this API and the CLI (src/main.py)."
    ),
    version="0.2.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    logger.info("Request started: %s %s", request.method, request.url.path)
    response = await call_next(request)
    elapsed = time.monotonic() - start
    logger.info(
        "Request finished: %s %s -> %d (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.exception_handler(EmptyDocumentDirectoryError)
async def handle_empty_documents(request: Request, exc: EmptyDocumentDirectoryError) -> JSONResponse:
    return JSONResponse(status_code=400, content=ErrorResponse(detail=str(exc)).model_dump())


@app.exception_handler(IndexNotReadyError)
async def handle_index_not_ready(request: Request, exc: IndexNotReadyError) -> JSONResponse:
    return JSONResponse(status_code=400, content=ErrorResponse(detail=str(exc)).model_dump())


@app.exception_handler(LLMModelNotFoundError)
async def handle_model_not_found(request: Request, exc: LLMModelNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=503, content=ErrorResponse(detail=str(exc)).model_dump())


@app.exception_handler(LLMConnectionError)
async def handle_llm_connection_error(request: Request, exc: LLMConnectionError) -> JSONResponse:
    return JSONResponse(status_code=503, content=ErrorResponse(detail=str(exc)).model_dump())


@app.exception_handler(LLMError)
async def handle_llm_error(request: Request, exc: LLMError) -> JSONResponse:
    logger.exception("LLM error while processing %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content=ErrorResponse(detail="LLM generation failed").model_dump())


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content=ErrorResponse(detail="An unexpected error occurred").model_dump())


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(index.router)


if __name__ == "__main__":
    import uvicorn

    _config = Config.load()
    uvicorn.run("src.api:app", host=_config.api_host, port=_config.api_port, reload=False)
