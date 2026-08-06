"""Composing the north star from channel insights, correctly.

Turns raw per-post metrics into the `Observation` list the learning loop compares. Four things have to
happen here or the statistics downstream are measuring the wrong thing:

**Normalize before weighting.** A weighted sum of raw counts is not a weighted sum. Metrics live on
different scales — a post might see 2 sessions, 6 shares and 200 reactions — so multiplying raw counts
by weights lets whichever metric has the largest natural magnitude dominate regardless of its weight.
Each metric is z-scored across the comparison set first, so a weight of 0.5 actually means half as
much as a weight of 1.0.

**Rates, not counts.** The channel decides who sees a post, so raw engagement measures
`content quality x delivery decision`. Dividing by reach isolates "of the people who saw this, how many
acted" — the part the content actually controls. Not a clean instrument (reach itself responds to early
engagement) but far better than totals. The dashboard should still show raw counts; that is a different
question, asked by a human, about business outcomes rather than about which content to make.

**A missing component excludes the post — never scores zero.** Channels rename metrics between API
versions. If a mapping misses after a rename and the gap is coerced to `0.0`, every post after that date
looks like a catastrophic failure and the reflection agent will confidently learn from it. Silent zeros
are the most dangerous failure mode in this pipeline, so an incomplete post is dropped and counted.

**Like-aged snapshots only.** Metrics settle over days. Comparing a fresh post's numbers against a
month-old post's numbers partly measures age. Every post contributes the snapshot nearest a fixed age,
and posts too young to have one are excluded.

One consequence worth holding onto: because normalization happens *within* a comparison set, an outcome
value is only meaningful relative to the other posts in that same call. It is not an absolute score and
must never be persisted as one or compared across calls.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import fmean, pstdev

from brandcortex.core.learning.verification import Observation

#: Delivery metric used as the denominator for rate-based components. Not itself an outcome: reach is
#: the channel's decision, not something the content earns.
REACH = "reach"


@dataclass(frozen=True)
class MetricSpec:
    weight: float
    #: Divide by reach before normalizing — isolates content quality from delivery volume.
    per_reach: bool = False


@dataclass(frozen=True)
class NorthStar:
    metrics: Mapping[str, MetricSpec]
    #: How old a post must be before its numbers are stable enough to compare.
    maturity_hours: int = 72
    #: How far a snapshot may sit from the target age and still represent it.
    tolerance_hours: int = 24

    @classmethod
    def from_config(cls, config: Mapping) -> "NorthStar":
        """Build from a `brand_config.north_star` block. Keys starting with `_` are comments."""
        raw = config.get("metrics", {})
        return cls(
            metrics={
                name: MetricSpec(
                    weight=float(spec.get("weight", 0.0)),
                    per_reach=bool(spec.get("per_reach", False)),
                )
                for name, spec in raw.items()
                if not name.startswith("_")
            },
            maturity_hours=int(config.get("maturity_hours", 72)),
            tolerance_hours=int(config.get("tolerance_hours", 24)),
        )

    @property
    def required(self) -> list[str]:
        """Metrics that actually affect the outcome.

        A zero-weighted metric contributes nothing, so its absence must not drop a post. Reactions are
        carried at weight 0 deliberately (§10.4) — excluding posts because a metric we refuse to
        optimize for went missing would be absurd.
        """
        return [name for name, spec in self.metrics.items() if spec.weight != 0]


@dataclass(frozen=True)
class Snapshot:
    captured_at: datetime
    #: Raw channel values. `None` means "not reported", which is never the same as zero.
    metrics: Mapping[str, float | None]


@dataclass(frozen=True)
class PostRecord:
    post_id: str
    #: The arm this post belongs to in the comparison — a feature value, e.g. a source type.
    label: str
    published_at: datetime
    snapshots: Sequence[Snapshot]


@dataclass(frozen=True)
class Dropped:
    post_id: str
    reason: str


@dataclass
class OutcomeSet:
    observations: list[Observation] = field(default_factory=list)
    #: Every post excluded, with why. Never silent: a comparison that quietly discarded half its data
    #: reads as a clean result when it is nothing of the kind.
    dropped: list[Dropped] = field(default_factory=list)
    #: Per-metric mean and standard deviation used to normalize, so a stored verdict is auditable.
    normalization: dict[str, dict[str, float]] = field(default_factory=dict)

    @property
    def drop_rate(self) -> float:
        total = len(self.observations) + len(self.dropped)
        return len(self.dropped) / total if total else 0.0

    def drops_by_reason(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for d in self.dropped:
            counts[d.reason] = counts.get(d.reason, 0) + 1
        return counts


def snapshot_at_age(
    post: PostRecord, *, age: timedelta, tolerance: timedelta
) -> Snapshot | None:
    """The snapshot nearest a fixed post age, or None if none falls within tolerance.

    Picking "the latest snapshot" instead would compare posts at different stages of settling, which
    silently favours whichever arm happens to contain older posts.
    """
    target = post.published_at + age
    candidates = [
        (abs(s.captured_at - target), s)
        for s in post.snapshots
        if abs(s.captured_at - target) <= tolerance
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda pair: pair[0])[1]


def _zscore(values: list[float]) -> list[float]:
    """Standardize, guarding the degenerate case.

    When every post scores identically the standard deviation is zero and there is no signal to
    normalize; that metric contributes nothing rather than raising or producing infinities.
    """
    if not values:
        return []
    spread = pstdev(values)
    if spread == 0:
        return [0.0] * len(values)
    mean = fmean(values)
    return [(v - mean) / spread for v in values]


def build_observations(
    posts: Sequence[PostRecord], north_star: NorthStar, *, as_of: datetime
) -> OutcomeSet:
    """Turn post records into comparable observations.

    `as_of` is passed rather than read from the clock so a comparison is reproducible — the same inputs
    must always yield the same verdict, including months later during an audit.
    """
    result = OutcomeSet()
    age = timedelta(hours=north_star.maturity_hours)
    tolerance = timedelta(hours=north_star.tolerance_hours)
    required = north_star.required

    # --- Pass 1: select a comparable snapshot per post and extract raw components.
    kept: list[tuple[PostRecord, dict[str, float]]] = []
    for post in posts:
        if as_of - post.published_at < age:
            result.dropped.append(Dropped(post.post_id, "immature"))
            continue

        snapshot = snapshot_at_age(post, age=age, tolerance=tolerance)
        if snapshot is None:
            result.dropped.append(Dropped(post.post_id, "no_snapshot_at_target_age"))
            continue

        needs_reach = any(north_star.metrics[m].per_reach for m in required)
        reach = snapshot.metrics.get(REACH)
        if needs_reach and not reach:
            # Zero reach is as unusable as absent reach — it cannot be a denominator.
            result.dropped.append(Dropped(post.post_id, "missing_reach"))
            continue

        components: dict[str, float] = {}
        missing = None
        for name in required:
            value = snapshot.metrics.get(name)
            if value is None:
                missing = name
                break
            spec = north_star.metrics[name]
            components[name] = value / float(reach) if spec.per_reach else float(value)
        if missing:
            result.dropped.append(Dropped(post.post_id, f"missing:{missing}"))
            continue

        kept.append((post, components))

    if not kept:
        return result

    # --- Pass 2: normalize each component across the surviving set, then weight.
    normalized: dict[str, list[float]] = {}
    for name in required:
        raw = [components[name] for _, components in kept]
        normalized[name] = _zscore(raw)
        result.normalization[name] = {
            "mean": fmean(raw),
            "stdev": pstdev(raw),
            "per_reach": float(north_star.metrics[name].per_reach),
        }

    for i, (post, _) in enumerate(kept):
        outcome = sum(
            north_star.metrics[name].weight * normalized[name][i] for name in required
        )
        result.observations.append(
            Observation(label=post.label, outcome=outcome, post_id=post.post_id)
        )

    return result
