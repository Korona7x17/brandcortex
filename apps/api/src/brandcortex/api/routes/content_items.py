"""Intake endpoints for the content-item handoff (spec §4.3).

Secondary to table-watch: this is the direct-API path, letting a brand push an item or letting an
operator trigger ingest of a specific one. Open decision #1 is which becomes primary.

The payload is the versioned envelope — see `schemas/content_item.py` and the JSON Schema in
`packages/contracts`.
"""

from fastapi import APIRouter

from brandcortex.schemas.content_item import ContentItem

router = APIRouter(prefix="/content-items", tags=["content-items"])


@router.post("")
def ingest_content_item(item: ContentItem) -> dict:
    """Accept an item and create a draft. Idempotent on content_id + channel. TODO(phase-1)."""
    raise NotImplementedError


@router.post("/{content_id}/reingest")
def reingest(content_id: str) -> dict:
    """Re-fetch an item from its source adapter and redraft. TODO(phase-1)."""
    raise NotImplementedError
