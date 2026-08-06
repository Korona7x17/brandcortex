"""Normalized performance snapshot returned by a channel adapter (spec §9, §10.1).

Every channel reports different metric names; the adapter maps them into this shape and keeps the
original payload in `raw`. Meta in particular renames insight metrics between Graph versions, so the
raw copy is what makes history recomputable after a rename.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InsightSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_post_id: str
    captured_at: datetime

    reach: int | None = None
    impressions: int | None = None
    reactions: int | None = Field(
        default=None, description="Recorded for context. Never a target — see spec §10.4."
    )
    comments: int | None = None
    shares: int | None = Field(default=None, description="Amplification: highest-value channel signal")
    saves: int | None = None
    link_clicks: int | None = Field(
        default=None,
        description="The channel's own count. Not the site's truth — cross-check against UTM sessions "
        "as the anti-reward-hacking check.",
    )

    raw: dict = Field(default_factory=dict)


class TrafficSnapshot(BaseModel):
    """Real arrivals from site analytics (GA4 / Plausible), joined by UTM campaign.

    This is the north star. It will not match the channel's link-click number, and it is the one that
    counts.
    """

    model_config = ConfigDict(extra="forbid")

    utm_campaign: str
    captured_at: datetime
    sessions: int
    raw: dict = Field(default_factory=dict)
