"""Review queue endpoints — the human-in-the-loop surface (spec §7 step 4, §11 Phase 1).

The Phase 1 UI is deliberately minimal: list drafts, edit, approve. That gate stays until the generation
engine has earned trust; auto-publish is a later decision, not a config flag to flip early.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from brandcortex.db.session import get_session

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("")
def list_posts(
    brand: str | None = None,
    status: str | None = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    """List posts, newest first. Drives the drafts view. TODO(phase-1)."""
    raise NotImplementedError


@router.get("/{post_id}")
def get_post(post_id: str, session: Session = Depends(get_session)) -> dict:
    """One post with its features and latest insight snapshot. TODO(phase-1)."""
    raise NotImplementedError


@router.patch("/{post_id}")
def edit_post(post_id: str, payload: dict, session: Session = Depends(get_session)) -> dict:
    """Apply a reviewer's edit to the caption or first comment.

    Record what changed, not just the result: the delta between generated and approved copy is the
    clearest signal available about where the engine is off, and it is lost if only the final text is
    stored.

    TODO(phase-1).
    """
    raise NotImplementedError


@router.post("/{post_id}/approve")
def approve_post(post_id: str, session: Session = Depends(get_session)) -> dict:
    """Clear a draft for publishing or scheduling. TODO(phase-1)."""
    raise NotImplementedError


@router.post("/{post_id}/publish")
def publish_post(post_id: str, session: Session = Depends(get_session)) -> dict:
    """Publish now: photo + caption, then the first comment with the link. TODO(phase-1)."""
    raise NotImplementedError
