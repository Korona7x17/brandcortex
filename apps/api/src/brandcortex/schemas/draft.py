"""What the generation engine returns, and what a channel adapter accepts (spec §6, §7).

`GeneratedDraft` is the boundary between the core and every channel adapter. It carries the caption and
the first comment separately because that split is a hard rule, not a formatting preference: Facebook is
trialing a ~2-links/month body cap, comments are exempt from it, and photo posts out-reach link posts.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GeneratedDraft(BaseModel):
    """Copy for one content item on one channel."""

    model_config = ConfigDict(extra="forbid")

    post_text: str = Field(description="The caption. Must not contain the canonical link.")
    first_comment_text: str = Field(
        description="Posted immediately after the photo, carrying the UTM-tagged canonical link."
    )

    # Recorded into `post_features` at draft time so the learning loop has history from post #1.
    intro_line: str | None = None
    hook_style: str | None = None
    hashtag_set: str | None = None

    # Which playbook rule versions shaped this draft. Without this, a rollback cannot tell which posts
    # were produced under which rules, and attribution silently mixes regimes.
    playbook_versions: dict[str, int] = Field(default_factory=dict)


class PublishRequest(BaseModel):
    """What the orchestrator hands a channel adapter."""

    model_config = ConfigDict(extra="forbid")

    brand: str
    asset_storage_key: str
    draft: GeneratedDraft
    # Set for native channel-side scheduling (FB: published=false + scheduled_publish_time).
    scheduled_for: datetime | None = None


class PublishResult(BaseModel):
    """What a channel adapter returns. Both ids are required for analytics to join later."""

    model_config = ConfigDict(extra="forbid")

    channel_post_id: str
    channel_comment_id: str | None = None
    published_at: datetime | None = None
