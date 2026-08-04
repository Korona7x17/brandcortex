"""Per-brand configuration and generation state: `brand_config`, `intro_history` (spec §5.2).

`brand_config` is where everything brand-specific lives so the core stays neutral: voice rules, the
intro bank, hashtag sets, the unit-label standard, tag targets, north-star weighting. Adding brand #2
means inserting a row here plus writing a source adapter — not editing core code.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from brandcortex.db.base import Base, TimestampMixin


class BrandConfig(Base, TimestampMixin):
    __tablename__ = "brand_config"

    brand: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # IANA timezone. Drives scheduling slots and the post_hour/post_weekday features — "best time to
    # post" is a claim about the audience's local clock.
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Bangkok")
    default_locale: Mapped[str] = mapped_column(String(8), default="th")

    # Voice rules: tone, banned constructions, emoji ceiling, taglines never to echo. Read by the
    # generation engine, and deliberately outside the learning loop's reach.
    voice: Mapped[dict] = mapped_column(JSON, default=dict)

    # Rotating soft intros, per locale. The engine picks one not used in the last N posts.
    intro_bank: Mapped[dict] = mapped_column(JSON, default=dict)

    # Core + optional hashtag sets.
    hashtags: Mapped[dict] = mapped_column(JSON, default=dict)

    # One unit-label standard, applied everywhere. Open decision #3: `50 ม.` vs `50 เมตร`.
    unit_labels: Mapped[dict] = mapped_column(JSON, default=dict)

    # Partner Pages worth tagging when the facts name them (clubs, teams).
    tag_targets: Mapped[dict] = mapped_column(JSON, default=dict)

    # How the north star is composed from UTM sessions and amplification. Reactions carry no weight —
    # weighting them would steer the loop back toward the hype voice the brand rejected.
    north_star: Mapped[dict] = mapped_column(JSON, default=dict)

    # Scheduling policy: source-type alternation, minimum spacing, preferred windows.
    scheduling: Mapped[dict] = mapped_column(JSON, default=dict)


class IntroHistory(Base, TimestampMixin):
    """Recently used intro lines, enforcing no-repeat rotation (spec §6.5).

    Kept separate from `post_features` because the rotation check runs at draft time against a small
    recent window, while features are a wide analytical record.
    """

    __tablename__ = "intro_history"
    __table_args__ = (Index("ix_intro_history_brand_used", "brand", "used_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64))
    locale: Mapped[str | None] = mapped_column(String(8))
    intro_line: Mapped[str] = mapped_column(Text, nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    post_id: Mapped[uuid.UUID | None] = mapped_column()
