"""The self-improving loop's own state: `playbook` and `experiments` (spec §5.2, §10).

The playbook is the mechanism of self-improvement: the generation engine and scheduler read the active
rules before acting, and a scheduled reflection agent rewrites them from evidence. Rules are versioned
rather than mutated so any change is revertible.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from brandcortex.db.base import Base, TimestampMixin
from brandcortex.db.models.enums import ExperimentStatus, PlaybookRuleStatus


class PlaybookRule(Base, TimestampMixin):
    """One learned heuristic, with the evidence that earned it.

    Confidence gating is what stops a single lucky post from rewriting strategy: a rule carries its
    sample size and confidence, and low-volume brands lean on the hand-authored priors from the spec
    until real evidence accumulates (spec §10.5 — weeks to months at a few posts/day).

    Voice rules are excluded on purpose. House voice is a fixed constraint, not an optimizable lever
    (spec §10.4); the reflection agent may never propose a rule that alters it.
    """

    __tablename__ = "playbook"
    __table_args__ = (
        UniqueConstraint("brand", "rule_key", "version", name="uq_playbook_rule_version"),
        Index("ix_playbook_brand_status", "brand", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String(64), nullable=False)

    # Stable identity of the heuristic across versions, e.g. "timing.preferred_hour.swimmer".
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    rule: Mapped[str] = mapped_column(Text, nullable=False)  # human-readable statement
    payload: Mapped[dict] = mapped_column(JSON, default=dict)  # machine-readable form the engine reads

    # --- What the proposer claimed. Self-reported, and treated as such. ---
    proposed_by: Mapped[str | None] = mapped_column(String(64))
    evidence: Mapped[str | None] = mapped_column(Text)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))

    # --- What independent checks found. Written by `core.learning.verification` and
    # `core.learning.skeptic`, never by whatever proposed the rule. Splitting these from the fields
    # above is the schema-level fix for self-grading: previously one agent filled in both its claim
    # and its confidence in that claim, and nothing recorded who checked it.
    verification: Mapped[dict] = mapped_column(JSON, default=dict)

    # --- Which posts the evidence came from. The channel's ranking algorithm changes, so a rule is
    # always a claim about the era it was learned in: evidence from last October may describe a
    # delivery system that no longer exists. Without these, an old rule and a fresh one look equally
    # authoritative in the playbook UI, and stale evidence never surfaces as something to re-test.
    evidence_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- What the rule predicts, recorded BEFORE activation and scored against reality afterwards.
    # This is the only genuinely independent reviewer in the system: the world does not share the
    # model's priors. A rule that fails its own prediction is retired regardless of how good its
    # evidence looked (see `playbook.score_predictions`).
    prediction: Mapped[dict] = mapped_column(JSON, default=dict)
    prediction_result: Mapped[dict] = mapped_column(JSON, default=dict)

    status: Mapped[PlaybookRuleStatus] = mapped_column(
        String(16), nullable=False, default=PlaybookRuleStatus.PROPOSED
    )
    # Set when a human clears the approval gate. Low-risk knobs (timing) may auto-activate; voice and
    # strategy changes may not.
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Experiment(Base, TimestampMixin):
    """A deliberate one-lever-at-a-time test (spec §10.3).

    One lever per experiment. Changing two things at once makes attribution impossible at the volumes
    this system operates at.
    """

    __tablename__ = "experiments"
    __table_args__ = (Index("ix_experiments_brand_status", "brand", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String(64), nullable=False)

    lever: Mapped[str] = mapped_column(String(128), nullable=False)
    hypothesis: Mapped[str | None] = mapped_column(Text)

    arms: Mapped[list] = mapped_column(JSON, default=list)
    allocation: Mapped[dict] = mapped_column(JSON, default=dict)  # bandit-style exploit/explore split
    results: Mapped[dict] = mapped_column(JSON, default=dict)

    status: Mapped[ExperimentStatus] = mapped_column(
        String(16), nullable=False, default=ExperimentStatus.DRAFT
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    concluded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
