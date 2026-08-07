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


@router.get("/health/assets")
def asset_health() -> dict:
    """Whether the captured cards are reachable where this deployment thinks they are.

    Pointing a deployment at a new bucket is the kind of change whose symptoms all arrive later —
    a capture that silently writes to a container disk, a publish that cannot open the bytes it is
    supposed to send. This answers it directly, and is the artifact to check after switching
    `ASSET_*` rather than waiting for a post to fail.

    Reports the backend and what is wrong with it, never the endpoint, the bucket or a key.
    """
    from brandcortex.services import assets

    store = assets.get_store()
    backend = "filesystem" if isinstance(store, assets.FilesystemStore) else "s3"
    problems = store.problems()
    return {"backend": backend, "ok": not problems, "problems": problems}


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
