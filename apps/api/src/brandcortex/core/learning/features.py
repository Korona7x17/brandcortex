"""Feature capture — the X side of the learning loop (spec §10.1).

Features per post: source type; intro line; hook style; post time (hour + weekday); age group;
stroke/event; gender; club tagged (y/n); caption length; hashtag set; locale; wow_factor.

Capture begins in Phase 1, before any learning exists. That ordering matters: features cannot be
reconstructed after the fact, so a post drafted without them is permanently invisible to the loop. By
the time the reflection agent switches on in Phase 2 it needs months of history already sitting there.

Brand-shaped dimensions (age group, stroke, gender) go into `PostFeatures.dimensions` as opaque JSON
so the core never learns what a stroke is.

## How dimensions are chosen

No key list. Every scalar in `facts` is copied through as a dimension and anything structured is left
behind. A key list would have to name a brand's fields, which is the one thing this layer may not do —
and it would silently drop a field the day a brand adds one, which is exactly when the loop most wants
it. The cost is a few dimensions nobody groups by; that is cheap, and attribution treats all of them
as opaque strings regardless.

`rows` is the notable exclusion: it is the card's whole table, it is large, and its useful summary
(row count, the winner's margin) is already folded into `wow_factor` by the source adapter.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from brandcortex.schemas.content_item import ContentItem
from brandcortex.schemas.draft import GeneratedDraft

#: Facts that are not dimensions. `wow_factor` has its own numeric column; structured values are
#: dropped by the scalar test below rather than by name.
_NOT_DIMENSIONS = frozenset({"wow_factor"})


def timing(at: datetime | None, *, timezone: str) -> dict[str, int | None]:
    """Post hour and weekday on the brand's local clock.

    Local, not UTC, on purpose: "the best time to post" is a claim about when the audience is awake,
    and a Bangkok evening is a UTC afternoon. Storing UTC would make every learned timing rule wrong
    by a fixed offset the moment a second brand ran in another timezone.

    Weekday is Monday=0, matching `datetime.weekday()`.
    """
    if at is None:
        return {"post_hour": None, "post_weekday": None}
    local = at.astimezone(ZoneInfo(timezone))
    return {"post_hour": local.hour, "post_weekday": local.weekday()}


def dimensions(facts: dict[str, Any]) -> dict[str, Any]:
    """Scalar facts, copied through as opaque grouping keys. See the module docstring."""
    return {
        key: value
        for key, value in facts.items()
        if key not in _NOT_DIMENSIONS and isinstance(value, str | int | float | bool)
    }


def extract(
    item: ContentItem,
    draft: GeneratedDraft,
    *,
    scheduled_for: datetime | None = None,
    timezone: str = "UTC",
    tagged_partner: bool = False,
) -> dict[str, Any]:
    """Build the feature vector for a post at draft time.

    `scheduled_for` fills the timing features when a slot is already known. For a post published on
    approval it is not, and the orchestrator refreshes them from `published_at` — a timing feature
    has to describe when the post actually went out, not when someone drafted it.
    """
    return {
        "source_type": item.source_type,
        "locale": item.locale,
        "intro_line": draft.intro_line,
        "hook_style": draft.hook_style,
        "caption_length": len(draft.post_text),
        "hashtag_set": draft.hashtag_set,
        "tagged_partner": tagged_partner,
        "wow_factor": item.wow_factor,
        "dimensions": dimensions(item.facts),
        **timing(scheduled_for, timezone=timezone),
    }
