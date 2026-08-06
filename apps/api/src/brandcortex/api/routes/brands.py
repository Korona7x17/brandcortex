"""Tenant identity and what a brand can make (spec §5.2).

The dashboard reads its own identity from here rather than hardcoding it. That is the same rule the
Python core follows, applied across the language boundary: a UI with "ThaiSwim" written into a
component is a UI that needs editing to onboard brand #2.

`source_types` and the search/compose endpoints are what let an operator start a card *here* instead
of in the brand's own admin, so this is also the intake surface.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandcortex.adapters import registry
from brandcortex.config import get_settings
from brandcortex.core import brand_config as brand_config_store
from brandcortex.core.brand_config import BrandNotConfigured
from brandcortex.db.models import BrandConfig
from brandcortex.db.session import get_session

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("")
def list_brands(session: Session = Depends(get_session)) -> list[dict]:
    """Every configured tenant. One today; the shape does not assume that."""
    rows = session.scalars(select(BrandConfig).order_by(BrandConfig.brand)).all()
    return [{"brand": row.brand, "display_name": row.display_name} for row in rows]


@router.get("/{brand}")
def get_brand(brand: str, session: Session = Depends(get_session)) -> dict:
    """Identity and capabilities — what the header shows and what the composer offers."""
    try:
        config = brand_config_store.load(session, brand)
    except BrandNotConfigured as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    adapter = _adapter_or_none(brand)
    return {
        "brand": brand,
        "display_name": config.get("display_name", brand),
        "site_url": getattr(adapter, "site_url", None),
        "timezone": config.get("timezone"),
        "default_locale": config.get("default_locale"),
        "supported_locales": config.get("supported_locales", [config.get("default_locale")]),
        "channels": registry.registered_channels(),
        # What this brand can compose, and the shape of each. The composer UI is built from this
        # rather than from a hardcoded list of ThaiSwim's two card kinds.
        "source_types": getattr(adapter, "SOURCE_TYPES", []) if adapter else [],
        "connected": adapter is not None,
    }


@router.get("/{brand}/search")
def search_subjects(brand: str, q: str = Query(min_length=2), limit: int = 20) -> list[dict]:
    """Find something to make a card about. Delegated to the source adapter, which owns the brand's
    notion of a subject — the core never learns what a swimmer is."""
    adapter = _adapter(brand)
    if not hasattr(adapter, "search"):
        raise HTTPException(status_code=501, detail=f"{brand} adapter does not support search")
    return adapter.search(q, limit=limit)


def _adapter(brand: str):
    try:
        return registry.get_source_adapter(brand)
    except registry.AdapterNotRegistered as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _adapter_or_none(brand: str):
    try:
        return registry.get_source_adapter(brand)
    except registry.AdapterNotRegistered:
        return None


class AngleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=32, pattern=r"^[a-z0-9_]+$")
    instruction: str = Field(min_length=1, max_length=600)


class WriterBrief(BaseModel):
    """What the brand tells the model. Everything here is the brand's to change.

    Note what is *not* here: the hard rules. Numbers must exist in the card's facts, the link never
    goes in the caption, the emoji ceiling holds. Those are checked after the model answers, so no
    edit on this page can remove them — which is what makes the page safe to expose at all.
    """

    model_config = ConfigDict(extra="forbid")

    guidance: str = Field(default="", max_length=4000)
    angles: list[AngleIn] = Field(default_factory=list, max_length=12)
    examples: list[str] = Field(default_factory=list, max_length=12)
    max_variants: int = Field(default=6, ge=1, le=12)


@router.get("/{brand}/writer")
def get_writer_brief(brand: str, session: Session = Depends(get_session)) -> dict:
    try:
        config = brand_config_store.load(session, brand)
    except BrandNotConfigured as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    brief = config.get("writer") or {}
    return {
        "guidance": brief.get("guidance", ""),
        "angles": brief.get("angles", []),
        "examples": brief.get("examples", []),
        "max_variants": brief.get("max_variants", 6),
        "voice": config.get("voice", {}),
        # Whether a model is actually configured. Without one the brief is still worth editing —
        # it is what the model will use the moment a key exists — but the UI should say so.
        "model_configured": bool(get_settings().anthropic_api_key),
        "model": get_settings().generation_model,
    }


@router.put("/{brand}/writer")
def put_writer_brief(
    brand: str, brief: WriterBrief, session: Session = Depends(get_session)
) -> dict:
    """Replace the brief. Angle keys must be unique — they are how a variant is attributed."""
    keys = [a.key for a in brief.angles]
    if len(keys) != len(set(keys)):
        raise HTTPException(status_code=422, detail="angle keys must be unique")

    try:
        config = brand_config_store.load(session, brand)
    except BrandNotConfigured as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    existing = config.get("writer") or {}
    config["writer"] = {
        # Keep the `_comment` keys explaining why the block exists; they are not the UI's to drop.
        **{k: v for k, v in existing.items() if k.startswith("_")},
        "guidance": brief.guidance,
        "angles": [a.model_dump() for a in brief.angles],
        "examples": [e for e in brief.examples if e.strip()],
        "max_variants": brief.max_variants,
    }
    brand_config_store.save(session, config)
    session.commit()
    return get_writer_brief(brand, session)
