"""Liveness and dependency checks."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
def ready() -> dict:
    """Readiness: both DBs reachable, each registered channel adapter healthy.

    Channel health is worth surfacing here because a Page token expires quietly — without a check, the
    first sign is a scheduled publish failing overnight.

    TODO(phase-1).
    """
    raise NotImplementedError
