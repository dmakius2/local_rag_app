"""Liveness check endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from src.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns whether the API process is up and able to serve requests.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(status="healthy")
