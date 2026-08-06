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


@router.get("/health/channels")
def channel_health() -> dict:
    """Whether each registered channel could publish right now.

    Surfaced so a revoked scope or an expired token is visible while someone is awake, rather than
    discovered by a post that was due to go out. Reports problems in words, and never the token.
    """
    from brandcortex.adapters import registry

    out: dict[str, dict] = {}
    for channel in registry.registered_channels():
        adapter = registry.get_channel_adapter(channel)
        problems = (
            adapter.health_problems()
            if hasattr(adapter, "health_problems")
            else ([] if adapter.health_check() else ["health check failed"])
        )
        out[channel] = {"ok": not problems, "problems": problems}
    return out
