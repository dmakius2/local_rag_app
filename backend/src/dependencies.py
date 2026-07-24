"""FastAPI dependency providers.

Kept separate from api.py so routers can depend on RAGService without
importing the app module itself (avoids circular imports).
"""
from __future__ import annotations

from fastapi import Request

from src.config import Config
from src.services.rag_service import RAGService


def get_rag_service(request: Request) -> RAGService:
    """Return the RAGService instance created at application startup."""
    return request.app.state.rag_service


def get_config(request: Request) -> Config:
    """Return the Config instance created at application startup."""
    return request.app.state.config
