"""Enumerations shared across models.

None of these name a brand or a channel. `brand` and `channel` are free-form keyed strings resolved
through the adapter registry, so adding IG or brand #2 never touches this file.
"""

from enum import StrEnum


class PostStatus(StrEnum):
    """Lifecycle of a post inside BrandCortex.

    Note this is *our* authoritative record of "posted to channel". The brand's own engine history
    means "content generated / available" and is a different event entirely (spec §4.4).
    """

    DRAFT = "draft"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class PlaybookRuleStatus(StrEnum):
    PROPOSED = "proposed"  # reflection agent suggested it; awaiting the approval gate
    ACTIVE = "active"  # generation engine and scheduler read this
    RETIRED = "retired"  # superseded or rolled back; kept for revertibility


class ExperimentStatus(StrEnum):
    DRAFT = "draft"
    RUNNING = "running"
    CONCLUDED = "concluded"
    ABANDONED = "abandoned"
