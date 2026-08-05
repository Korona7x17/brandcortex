"""Tenant identity and what a brand can make (spec §5.2).

The dashboard reads its own identity from here rather than hardcoding it. That is the same rule the
Python core follows, applied across the language boundary: a UI with "ThaiSwim" written into a
component is a UI that needs editing to onboard brand #2.

`source_types` and the search/compose endpoints are what let an operator start a card *here* instead
of in the brand's own admin, so this is also the intake surface.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from brandcortex.adapters import registry
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
