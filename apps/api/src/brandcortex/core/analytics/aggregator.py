"""Dashboard queries: joins `posts` × `post_features` × `post_insights` (spec §9).

This join is the reason BrandCortex owns publishing. Because it published the posts it already holds
every `channel_post_id`, so tying performance back to *which content, caption, format, and time produced
it* costs nothing. Facebook's native insights cannot slice by these dimensions — source type, swimmer,
age group, intro line, post time — and that gap is the point of the dashboard.

Questions it must answer: swimmer vs event; best time to post; which intro line; which age groups
travel.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BreakdownRow:
    dimension: str
    value: str
    posts: int
    avg_reach: float | None
    avg_shares: float | None
    avg_utm_sessions: float | None  # north star


def breakdown(
    brand: str, *, dimension: str, since: datetime | None = None, channel: str | None = None
) -> list[BreakdownRow]:
    """Aggregate outcomes by one feature dimension.

    Uses the latest insight snapshot per post: earlier snapshots are still settling and averaging
    across them would weight recent posts down purely for being young.

    TODO(phase-2): implement.
    """
    raise NotImplementedError


def timing_matrix(brand: str, *, source_type: str | None = None) -> list[BreakdownRow]:
    """Hour × weekday performance in the brand's timezone. TODO(phase-2)."""
    raise NotImplementedError
