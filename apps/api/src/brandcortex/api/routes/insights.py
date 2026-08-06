"""Dashboard read endpoints (spec §9).

Serves the joins Facebook's native insights cannot: performance sliced by source type, intro line, post
time, and the brand's own dimensions. Traffic figures come from UTM-attributed site analytics, which is
the source of truth here — not the channel's link-click count.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/breakdown")
def breakdown(brand: str, dimension: str, channel: str | None = None) -> list[dict]:
    """Aggregate outcomes by one feature dimension. TODO(phase-2)."""
    raise NotImplementedError


@router.get("/timing")
def timing(brand: str, source_type: str | None = None) -> list[dict]:
    """Hour x weekday matrix in the brand's timezone. TODO(phase-2)."""
    raise NotImplementedError
