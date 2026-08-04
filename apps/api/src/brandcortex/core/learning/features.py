"""Feature capture — the X side of the learning loop (spec §10.1).

Features per post: source type; intro line; hook style; post time (hour + weekday); age group;
stroke/event; gender; club tagged (y/n); caption length; hashtag set; locale; wow_factor.

Capture begins in Phase 1, before any learning exists. That ordering matters: features cannot be
reconstructed after the fact, so a post drafted without them is permanently invisible to the loop. By
the time the reflection agent switches on in Phase 2 it needs months of history already sitting there.

Brand-shaped dimensions (age group, stroke, gender) go into `PostFeatures.dimensions` as opaque JSON so
the core never learns what a stroke is.
"""

from brandcortex.schemas.content_item import ContentItem
from brandcortex.schemas.draft import GeneratedDraft


def extract(
    item: ContentItem, draft: GeneratedDraft, *, scheduled_for=None, timezone: str = "UTC"
) -> dict:
    """Build the feature vector for a post at draft time.

    Post hour and weekday are computed in the brand's timezone, not UTC: "the best time to post" is a
    claim about when the audience is awake.

    TODO(phase-1): implement.
    """
    raise NotImplementedError
