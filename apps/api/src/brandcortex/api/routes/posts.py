"""Review queue endpoints — the human-in-the-loop surface (spec §7 step 4, §11 Phase 1).

The Phase 1 UI is deliberately minimal: list drafts, edit, approve. That gate stays until the
generation engine has earned trust; auto-publish is a later decision, not a config flag to flip early.

Two things this surface returns that a plainer CRUD layer would not, both because the reviewer's job
is comparison rather than reading:

* **`generated` alongside the current text.** What the engine wrote and what the human is about to
  approve, so an edit is visible *as* an edit.
* **`facts`.** The numbers the card asserts, next to the caption asserting them. The numeric check
  already guarantees they agree; showing them is what lets a reviewer confirm the card is the *right*
  card, which no check can do.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandcortex.core import brand_config as brand_config_store
from brandcortex.core.learning import playbook
from brandcortex.core.orchestrator import (
    EditRejected,
    InvalidTransition,
    Orchestrator,
    PostNotFound,
    PublishFailed,
)
from brandcortex.core.scheduling.scheduler import Booked, Scheduler
from brandcortex.db.models import Post, PostFeatures, PostStatus
from brandcortex.db.session import get_session
from brandcortex.services import assets

router = APIRouter(prefix="/posts", tags=["posts"])


class PostEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_text: str | None = None
    first_comment_text: str | None = None


class RegenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nudge: str | None = None


class ScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    when: datetime


class ApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edited_text: str | None = None


def _insight(row) -> dict:
    return {
        "captured_at": row.captured_at,
        "reach": row.reach,
        "impressions": row.impressions,
        "reactions": row.reactions,
        "comments": row.comments,
        "shares": row.shares,
        "saves": row.saves,
        "link_clicks": row.link_clicks,
        "utm_sessions": row.utm_sessions,
    }


def _serialize(post: Post, *, detail: bool = False) -> dict:
    payload: dict = {
        "id": str(post.id),
        "content_id": post.content_id,
        "brand": post.brand,
        "channel": post.channel,
        "status": post.status,
        "source_type": post.features.source_type if post.features else None,
        "post_text": post.post_text,
        "first_comment_text": post.first_comment_text,
        "asset_storage_key": post.asset_storage_key,
        "utm_campaign": post.utm_campaign,
        "scheduled_for": post.scheduled_for,
        "approved_at": post.approved_at,
        "published_at": post.published_at,
        "channel_post_id": post.channel_post_id,
        "channel_comment_id": post.channel_comment_id,
        "error": post.error,
        "created_at": post.created_at,
        "edited": bool(
            post.generated_post_text is not None and post.generated_post_text != post.post_text
        ),
    }
    if not detail:
        return payload

    payload["generated"] = {
        "post_text": post.generated_post_text,
        "first_comment_text": post.generated_first_comment_text,
    }
    payload["facts"] = post.facts
    payload["features"] = (
        {
            "source_type": post.features.source_type,
            "locale": post.features.locale,
            "intro_line": post.features.intro_line,
            "hook_style": post.features.hook_style,
            "caption_length": post.features.caption_length,
            "hashtag_set": post.features.hashtag_set,
            "post_hour": post.features.post_hour,
            "post_weekday": post.features.post_weekday,
            "wow_factor": (
                float(post.features.wow_factor) if post.features.wow_factor is not None else None
            ),
            "dimensions": post.features.dimensions,
        }
        if post.features
        else None
    )
    payload["variants"] = [
        {
            "angle": v.angle,
            "position": v.position,
            "post_text": v.post_text,
            "first_comment_text": v.first_comment_text,
            "hook_style": v.hook_style,
            "intro_line": v.intro_line,
            "origin": v.origin,
            "model": v.model,
            "rejected": v.rejected or [],
            "chosen": v.chosen_at is not None,
        }
        for v in sorted(post.variants, key=lambda v: v.position)
    ]
    latest = max(post.insights, key=lambda row: row.captured_at, default=None)
    payload["latest_insight"] = _insight(latest) if latest else None
    return payload


def _post_id(raw: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"no post {raw}") from exc


def _load(session: Session, post_id: str) -> Post:
    post = session.get(Post, _post_id(post_id))
    if post is None:
        raise HTTPException(status_code=404, detail=f"no post {post_id}")
    return post


@router.get("")
def list_posts(
    brand: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[dict]:
    """List posts, newest first. Drives the drafts view."""
    query = select(Post).order_by(Post.created_at.desc()).limit(limit)
    if brand:
        query = query.where(Post.brand == brand)
    if status:
        query = query.where(Post.status == status)
    return [_serialize(post) for post in session.scalars(query).all()]


@router.get("/{post_id}")
def get_post(post_id: str, session: Session = Depends(get_session)) -> dict:
    """One post with its features, its facts, and the latest insight snapshot."""
    return _serialize(_load(session, post_id), detail=True)


@router.get("/{post_id}/card")
def get_post_card(post_id: str, session: Session = Depends(get_session)) -> Response:
    """The captured card image — the exact bytes that publish.

    Served from BrandCortex's own store rather than proxied from the brand's render URL, which is the
    whole point of capturing at draft time: the reviewer looks at the image that ships, not at
    whatever the card route would render right now.
    """
    post = _load(session, post_id)
    if not post.asset_storage_key:
        raise HTTPException(status_code=404, detail="post has no captured card")
    extension = post.asset_storage_key.rsplit(".", 1)[-1].lower()
    media_type = "image/jpeg" if extension in ("jpg", "jpeg") else f"image/{extension}"
    return StreamingResponse(assets.open_stored(post.asset_storage_key), media_type=media_type)


@router.patch("/{post_id}")
def edit_post(post_id: str, payload: PostEdit, session: Session = Depends(get_session)) -> dict:
    """Apply a reviewer's edit to the caption or first comment.

    The engine's original is kept on the row rather than overwritten, so the delta stays recoverable:
    what a reviewer changed is the clearest signal available about where the engine is off, and it is
    lost the moment only the final text is stored.
    """
    try:
        post = Orchestrator(session).edit(
            _post_id(post_id),
            post_text=payload.post_text,
            first_comment_text=payload.first_comment_text,
        )
    except PostNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EditRejected as exc:
        raise HTTPException(status_code=422, detail={"reasons": exc.reasons}) from exc
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _serialize(post, detail=True)


@router.post("/{post_id}/approve")
def approve_post(
    post_id: str,
    payload: ApproveRequest | None = None,
    session: Session = Depends(get_session),
) -> dict:
    """Clear a draft for publishing or scheduling."""
    try:
        post = Orchestrator(session).approve(
            _post_id(post_id), edited_text=payload.edited_text if payload else None
        )
    except PostNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EditRejected as exc:
        raise HTTPException(status_code=422, detail={"reasons": exc.reasons}) from exc
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _serialize(post, detail=True)


@router.post("/{post_id}/publish")
def publish_post(post_id: str, session: Session = Depends(get_session)) -> dict:
    """Publish now: photo + caption, then the first comment with the link.

    A 502 here means the post is `failed` and recoverable, not that its state is unknown — the
    orchestrator commits the failure before raising.
    """
    try:
        post = Orchestrator(session).publish(_post_id(post_id))
    except PostNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PublishFailed as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _serialize(post, detail=True)


@router.get("/{post_id}/insights")
def post_insights(post_id: str, session: Session = Depends(get_session)) -> list[dict]:
    """Every snapshot for one post, oldest first.

    The series, not a single row: the numbers keep settling for two to three days, so any one
    snapshot is a moment rather than a result.
    """
    post = _load(session, post_id)
    return [_insight(row) for row in sorted(post.insights, key=lambda r: r.captured_at)]


@router.post("/{post_id}/variants/{angle}/choose")
def choose_variant(post_id: str, angle: str, session: Session = Depends(get_session)) -> dict:
    """Adopt one of the offered angles.

    Distinct from an edit on purpose. An edit says the copy was wrong; a pick says this framing beat
    the alternatives, which is a cleaner signal and one the learning loop is allowed to act on —
    `hook_style` is a tunable lever, unlike voice.
    """
    try:
        post = Orchestrator(session).choose_variant(_post_id(post_id), angle)
    except PostNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _serialize(post, detail=True)


@router.post("/{post_id}/regenerate")
def regenerate(
    post_id: str,
    payload: RegenerateRequest | None = None,
    session: Session = Depends(get_session),
) -> dict:
    """Write a fresh set of angles, optionally with a steer for this post only."""
    try:
        post = Orchestrator(session).regenerate(
            _post_id(post_id), nudge=payload.nudge if payload else None
        )
    except PostNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _serialize(post, detail=True)


@router.get("/{post_id}/suggested-slot")
def suggested_slot(post_id: str, session: Session = Depends(get_session)) -> dict:
    """When the scheduler would put this post, and why.

    The reasons ship with the time on purpose. A bare "Thursday 19:00" invites an override on
    instinct; "Wednesday is taken, and the last post was also a swimmer" can be disagreed with on
    the merits, which is the difference between a suggestion and an instruction.
    """
    post = _load(session, post_id)
    config = brand_config_store.load(session, post.brand)

    booked = [
        Booked(at=row.scheduled_for or row.published_at, source_type=source)
        for row, source in session.execute(
            select(Post, PostFeatures.source_type)
            .join(PostFeatures, PostFeatures.post_id == Post.id, isouter=True)
            .where(
                Post.brand == post.brand,
                Post.channel == post.channel,
                Post.id != post.id,
                Post.status.in_([PostStatus.SCHEDULED, PostStatus.PUBLISHED]),
            )
        ).all()
        if (row.scheduled_for or row.published_at)
    ]

    scheduler = Scheduler(config, playbook.load_active(session, post.brand))
    try:
        slot = scheduler.next_slot(
            booked=booked,
            source_type=(post.features.source_type if post.features else "") or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "at": slot.at,
        "reasons": slot.reasons,
        "relaxed": slot.relaxed,
        "timezone": config.get("timezone"),
        "booked": len(booked),
    }


@router.post("/{post_id}/schedule")
def schedule_post(
    post_id: str, payload: ScheduleRequest, session: Session = Depends(get_session)
) -> dict:
    """Assign a slot. The post publishes when the publisher worker reaches that time."""
    when = payload.when if payload.when.tzinfo else payload.when.replace(tzinfo=UTC)
    try:
        post = Orchestrator(session).schedule(_post_id(post_id), when)
    except PostNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _serialize(post, detail=True)
