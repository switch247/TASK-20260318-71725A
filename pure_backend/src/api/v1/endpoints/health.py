"""Expose health and metrics endpoints for runtime verification and monitoring."""

from fastapi import APIRouter

from src.core.metrics import snapshot

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> dict[str, int]:
    return snapshot()
