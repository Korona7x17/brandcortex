"""Posts and their measurement trail: `posts`, `post_features`, `post_insights` (spec §5.2).

A post is BrandCortex's own state about one content item on one channel. `content_id` is a reference
into the brand's data, not a foreign key we can enforce — the brand owns that row and we never join
across the seam in SQL.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brandcortex.db.base import Base, TimestampMixin
from brandcortex.db.models.enums import PostStatus, status_column


class Post(Base, TimestampMixin):
    __tablename__ = "posts"
    __table_args__ = (
        # One post per content item per channel: re-posting the same card to the same Page is a bug,
        # not a feature. Cross-channel reuse of one content item is expected and allowed.
        UniqueConstraint("content_id", "channel", name="uq_posts_content_channel"),
        Index("ix_posts_brand_status", "brand", "status"),
        Index("ix_posts_scheduled_for", "scheduled_for"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Reference into the brand's data. Deliberately not a FK — see module docstring. A string, not a
    # UUID: ThaiSwim's `card_renders.id` is a cuid, and a brand's id format is its own business.
    content_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[PostStatus] = mapped_column(
        status_column(PostStatus), nullable=False, default=PostStatus.DRAFT
    )

    # BrandCortex's frozen copy of the card, captured at draft time. These exact bytes are what
    # publishes, so the reviewer approves the image that ships and the brand's live render can move
    # afterwards without consequence.
    asset_storage_key: Mapped[str | None] = mapped_column(String(512))

    # The content item's `facts` as they stood when the draft was written — the brand's snapshot,
    # denormalized and frozen. Three things need it and none of them can get it any other way: the
    # review UI shows what the card asserts next to what the caption says, the numeric check has to
    # re-run against a reviewer's edit, and afterwards this is the only surviving record of what the
    # image claimed, since the brand's own row can change and the card re-renders from live data.
    facts: Mapped[dict] = mapped_column(JSON, default=dict)

    # The caption as it will publish. Never contains the canonical link — links go in the first
    # comment (spec §8). A reviewer may edit this; the pair below keeps what the engine actually wrote.
    post_text: Mapped[str | None] = mapped_column(Text)
    # The first comment, carrying the UTM-tagged canonical link.
    first_comment_text: Mapped[str | None] = mapped_column(Text)

    # The engine's own output, frozen at draft time and never edited afterwards. The delta between
    # these and the columns above is the single most valuable training signal the system produces — a
    # reviewer's edit is a direct statement about what the engine got wrong. Storing both texts rather
    # than a diff keeps it recomputable with whatever comparison turns out to be the useful one.
    generated_post_text: Mapped[str | None] = mapped_column(Text)
    generated_first_comment_text: Mapped[str | None] = mapped_column(Text)

    # The campaign carried by the link in the first comment. Unique because it is the join key between
    # site analytics and this post: two posts sharing one campaign would merge their traffic silently,
    # so the collision has to be a write error at draft time instead.
    utm_campaign: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)

    # When the brand rendered the card — the envelope's `generated_at`, copied across the seam. It is
    # also the ingest cursor: the watcher polls for rows newer than the newest one it has drafted, so
    # the cursor lives in the same table as the evidence it was advanced by, and re-deriving it after
    # a restart is one query rather than a piece of worker state that can go missing.
    source_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Channel-side identifiers, captured on publish. These are what make analytics joinable back to
    # "which content, caption, format and time produced this" — the whole point of §9.
    channel_post_id: Mapped[str | None] = mapped_column(String(128), index=True)
    channel_comment_id: Mapped[str | None] = mapped_column(String(128))

    error: Mapped[str | None] = mapped_column(Text)

    features: Mapped["PostFeatures | None"] = relationship(
        back_populates="post", uselist=False, cascade="all, delete-orphan"
    )
    insights: Mapped[list["PostInsight"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class PostFeatures(Base, TimestampMixin):
    """The feature vector for one post — the X side of the learning loop (spec §10.1).

    Captured at draft time from Phase 1 onward, before any learning exists, so the reflection agent has
    history the day it switches on.
    """

    __tablename__ = "post_features"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )

    source_type: Mapped[str | None] = mapped_column(String(64), index=True)
    intro_line: Mapped[str | None] = mapped_column(Text)
    hook_style: Mapped[str | None] = mapped_column(String(64))

    # Post time split for the timing model. Stored in the brand's local timezone: "best hour to post"
    # is a statement about the audience's clock, not UTC.
    post_hour: Mapped[int | None] = mapped_column(Integer)
    post_weekday: Mapped[int | None] = mapped_column(Integer)

    locale: Mapped[str | None] = mapped_column(String(8))
    caption_length: Mapped[int | None] = mapped_column(Integer)
    hashtag_set: Mapped[str | None] = mapped_column(String(128))
    tagged_partner: Mapped[bool | None] = mapped_column()
    wow_factor: Mapped[float | None] = mapped_column(Numeric(4, 3))

    # Brand-shaped dimensions lifted from the content item's `facts` (for ThaiSwim: age group, stroke,
    # event, gender). JSON keeps the core brand-agnostic — attribution treats these as opaque keys.
    dimensions: Mapped[dict] = mapped_column(JSON, default=dict)

    post: Mapped[Post] = relationship(back_populates="features")


class PostInsight(Base, TimestampMixin):
    """One snapshot of a published post's performance — the Y side of the loop.

    Snapshotted several times over the first 2–3 days because the numbers keep settling; each row is a
    point in time, never an update in place.
    """

    __tablename__ = "post_insights"
    __table_args__ = (
        UniqueConstraint("post_id", "captured_at", name="uq_post_insights_snapshot"),
        Index("ix_post_insights_post_captured", "post_id", "captured_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    reach: Mapped[int | None] = mapped_column(Integer)
    impressions: Mapped[int | None] = mapped_column(Integer)
    reactions: Mapped[int | None] = mapped_column(Integer)  # recorded, never optimized for
    comments: Mapped[int | None] = mapped_column(Integer)
    shares: Mapped[int | None] = mapped_column(Integer)  # amplification — highest-value signal
    saves: Mapped[int | None] = mapped_column(Integer)
    link_clicks: Mapped[int | None] = mapped_column(Integer)

    # North star. Comes from site analytics via UTM, not from the channel: FB's click number is not the
    # site's truth and the link lives in a comment. The two will not match, by design.
    utm_sessions: Mapped[int | None] = mapped_column(Integer)

    # Raw channel payload, kept because Meta renames metrics between Graph versions and we would
    # otherwise lose the ability to recompute history after a rename.
    raw: Mapped[dict] = mapped_column(JSON, default=dict)

    post: Mapped[Post] = relationship(back_populates="insights")
