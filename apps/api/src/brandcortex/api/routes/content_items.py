"""Intake endpoints for the content-item handoff (spec §4.3).

Secondary to table-watch: this is the direct-API path, letting a brand push an item or letting an
operator trigger ingest of a specific one. Open decision #1 is which becomes primary.

The payload is the versioned envelope — see `schemas/content_item.py` and the JSON Schema in
`packages/contracts`.

A rejected draft comes back `200` with `status: "failed"` and its reasons on the row, not as a `4xx`.
The request succeeded: a post exists, it is in the review queue, and someone can see why it did not
draft. An error status would leave the caller thinking nothing was recorded when something was.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from brandcortex.adapters import registry
from brandcortex.api.routes.posts import _serialize
from brandcortex.core.brand_config import BrandNotConfigured
from brandcortex.core.orchestrator import Orchestrator
from brandcortex.db.session import get_session
from brandcortex.schemas.content_item import ContentItem

router = APIRouter(prefix="/content-items", tags=["content-items"])


def _resolve_channel(channel: str | None) -> str:
    """The channel to draft for. Explicit wins; otherwise the single registered one.

    Guessing is only safe while there is exactly one. The moment a second channel is registered this
    starts refusing, which is the correct behaviour — a card silently drafted for the wrong Page is
    worse than a 400.
    """
    if channel:
        return channel
    registered = registry.registered_channels()
    if len(registered) == 1:
        return registered[0]
    raise HTTPException(
        status_code=400,
        detail=f"`channel` is required; registered channels: {registered or '(none)'}",
    )


@router.post("")
def ingest_content_item(
    item: ContentItem, channel: str | None = None, session: Session = Depends(get_session)
) -> dict:
    """Accept an item and create a draft. Idempotent on content_id + channel."""
    try:
        post = Orchestrator(session).ingest(item, channel=_resolve_channel(channel))
    except BrandNotConfigured as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(post, detail=True)


@router.post("/{content_id}/reingest")
def reingest(
    content_id: str,
    brand: str,
    channel: str | None = None,
    session: Session = Depends(get_session),
) -> dict:
    """Re-fetch an item from its source adapter and draft it.

    Note this does *not* redraft an existing post: `ingest` is idempotent on content id, so an item
    already in the queue comes back unchanged. Rewriting a draft a human may already have edited
    would discard their work, so replacing one is a delete plus a reingest — deliberately two steps.
    """
    try:
        adapter = registry.get_source_adapter(brand)
    except registry.AdapterNotRegistered as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    item = adapter.fetch(content_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{brand} has no content item {content_id}")

    post = Orchestrator(session).ingest(item, channel=_resolve_channel(channel))
    return _serialize(post, detail=True)
