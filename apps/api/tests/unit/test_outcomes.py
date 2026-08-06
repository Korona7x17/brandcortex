"""Tests for north-star composition (`core.analytics.outcomes`).

Two of these are regressions for bugs that were live in the seed config and would have corrupted every
comparison the learning loop ever ran:

* a weighted sum of raw counts is not a weighted sum (`test_scale_does_not_beat_weight`)
* a missing metric coerced to zero manufactures a catastrophe (`test_missing_component_excludes...`)
"""

from datetime import UTC, datetime, timedelta

from brandcortex.core.analytics.outcomes import (
    MetricSpec,
    NorthStar,
    PostRecord,
    Snapshot,
    build_observations,
    snapshot_at_age,
)

NOW = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)

#: Two components, deliberately on very different natural scales.
NS = NorthStar(
    metrics={
        "utm_sessions": MetricSpec(weight=1.0, per_reach=True),
        "shares": MetricSpec(weight=0.5, per_reach=True),
        "reactions": MetricSpec(weight=0.0, per_reach=True),
    }
)


def post(
    post_id: str,
    label: str,
    *,
    days_old: int = 10,
    sessions: float | None = 2,
    shares: float | None = 5,
    reactions: float | None = 200,
    reach: float | None = 1000,
    snapshot_age_hours: int = 72,
) -> PostRecord:
    published = NOW - timedelta(days=days_old)
    return PostRecord(
        post_id=post_id,
        label=label,
        published_at=published,
        snapshots=[
            Snapshot(
                captured_at=published + timedelta(hours=snapshot_age_hours),
                metrics={
                    "utm_sessions": sessions,
                    "shares": shares,
                    "reactions": reactions,
                    "reach": reach,
                },
            )
        ],
    )


class TestNormalizationBeforeWeighting:
    def test_scale_does_not_beat_weight(self) -> None:
        """The regression, constructed so a raw weighted sum gives the *opposite* answer.

        Arm A is 10x better on `utm_sessions` (weight 1.0). Arm B is 3% better on `shares` (weight
        0.5) — but shares run two orders of magnitude larger, so under a raw weighted sum that 3% edge
        outweighs a 10x lead on the metric we said matters twice as much.

        Normalizing first makes the weights mean what the config says they mean.
        """
        A = {"sessions": 10, "shares": 1000}
        B = {"sessions": 1, "shares": 1030}
        posts = [post(f"a{i}", "a", **A) for i in range(4)]
        posts += [post(f"b{i}", "b", **B) for i in range(4)]

        # What the buggy implementation would have concluded, computed here so this test cannot
        # silently become vacuous if the fixtures are edited.
        raw = {
            arm: 1.0 * (m["sessions"] / 1000) + 0.5 * (m["shares"] / 1000)
            for arm, m in (("a", A), ("b", B))
        }
        assert raw["b"] > raw["a"], "fixture no longer exercises the scale bug"

        totals: dict[str, float] = {"a": 0.0, "b": 0.0}
        for o in build_observations(posts, NS, as_of=NOW).observations:
            totals[o.label] += o.outcome

        assert totals["a"] > totals["b"]

    def test_zero_weight_metric_cannot_influence_outcome(self) -> None:
        """Reactions run 40x the other metrics and are weighted 0. This is the guardrail that stops the
        loop drifting toward hype (§10.4), so scale must not sneak it back in."""
        base = [post(f"a{i}", "a", sessions=5, shares=5, reactions=10) for i in range(4)]
        base += [post(f"b{i}", "b", sessions=5, shares=5, reactions=100_000) for i in range(4)]

        outcomes = {o.post_id: o.outcome for o in build_observations(base, NS, as_of=NOW).observations}
        assert len(set(round(v, 9) for v in outcomes.values())) == 1

    def test_records_normalization_for_audit(self) -> None:
        posts = [post(f"a{i}", "a", sessions=i + 1) for i in range(4)]
        posts += [post(f"b{i}", "b", sessions=i + 5) for i in range(4)]
        norm = build_observations(posts, NS, as_of=NOW).normalization
        assert {"utm_sessions", "shares"} <= set(norm)
        assert "mean" in norm["utm_sessions"] and "stdev" in norm["utm_sessions"]

    def test_identical_posts_do_not_explode(self) -> None:
        """Zero variance means no signal, not a division by zero."""
        posts = [post(f"p{i}", "a" if i < 3 else "b") for i in range(6)]
        result = build_observations(posts, NS, as_of=NOW)
        assert len(result.observations) == 6
        assert all(o.outcome == 0.0 for o in result.observations)


class TestMissingComponents:
    def test_missing_component_excludes_post_and_never_scores_zero(self) -> None:
        """The rename bug. If a channel renames a metric and the gap became 0.0, every later post would
        look like a total failure and the reflection agent would learn from it."""
        posts = [post(f"a{i}", "a") for i in range(3)]
        posts.append(post("broken", "a", sessions=None))

        result = build_observations(posts, NS, as_of=NOW)
        assert [o.post_id for o in result.observations] == ["a0", "a1", "a2"]
        assert result.dropped == [type(result.dropped[0])("broken", "missing:utm_sessions")]

    def test_missing_zero_weight_metric_does_not_exclude(self) -> None:
        """Reactions are weighted 0. Dropping a post because a metric we refuse to optimize for went
        missing would discard good data for no reason."""
        result = build_observations([post("p1", "a", reactions=None)], NS, as_of=NOW)
        assert len(result.observations) == 1
        assert not result.dropped

    def test_missing_reach_excludes_when_rates_are_used(self) -> None:
        result = build_observations([post("p1", "a", reach=None)], NS, as_of=NOW)
        assert not result.observations
        assert result.dropped[0].reason == "missing_reach"

    def test_zero_reach_excludes(self) -> None:
        """Unusable as a denominator, and a post nobody saw carries no information anyway."""
        result = build_observations([post("p1", "a", reach=0)], NS, as_of=NOW)
        assert result.dropped[0].reason == "missing_reach"

    def test_count_based_metric_needs_no_reach(self) -> None:
        counts = NorthStar(metrics={"utm_sessions": MetricSpec(weight=1.0, per_reach=False)})
        result = build_observations([post("p1", "a", reach=None)], counts, as_of=NOW)
        assert len(result.observations) == 1


class TestMaturityAndAgeMatching:
    def test_young_posts_are_excluded(self) -> None:
        """Metrics are still settling; including them measures age, not content."""
        result = build_observations(
            [post("young", "a", days_old=1, snapshot_age_hours=12)], NS, as_of=NOW
        )
        assert result.dropped[0].reason == "immature"

    def test_post_without_a_snapshot_near_target_age_is_excluded(self) -> None:
        """Published long ago but only ever measured once, minutes after posting."""
        result = build_observations(
            [post("stale", "a", days_old=30, snapshot_age_hours=1)], NS, as_of=NOW
        )
        assert result.dropped[0].reason == "no_snapshot_at_target_age"

    def test_picks_the_snapshot_nearest_the_target_age(self) -> None:
        """Not the latest — using the latest compares posts at different stages of settling, which
        favours whichever arm happens to hold older posts."""
        published = NOW - timedelta(days=30)
        record = PostRecord(
            post_id="p",
            label="a",
            published_at=published,
            snapshots=[
                Snapshot(published + timedelta(hours=6), {"shares": 1}),
                Snapshot(published + timedelta(hours=70), {"shares": 2}),
                Snapshot(published + timedelta(days=20), {"shares": 99}),
            ],
        )
        chosen = snapshot_at_age(record, age=timedelta(hours=72), tolerance=timedelta(hours=24))
        assert chosen is not None and chosen.metrics["shares"] == 2


class TestDiagnostics:
    def test_drop_rate_and_reasons_are_reported(self) -> None:
        """A comparison that quietly discarded half its data reads as a clean result otherwise."""
        posts = [post(f"ok{i}", "a") for i in range(2)]
        posts += [post("young", "a", days_old=1, snapshot_age_hours=12), post("gap", "b", shares=None)]

        result = build_observations(posts, NS, as_of=NOW)
        assert result.drop_rate == 0.5
        assert result.drops_by_reason() == {"immature": 1, "missing:shares": 1}

    def test_empty_input_is_not_an_error(self) -> None:
        result = build_observations([], NS, as_of=NOW)
        assert not result.observations and result.drop_rate == 0.0


class TestFromConfig:
    def test_parses_a_brand_config_block(self) -> None:
        ns = NorthStar.from_config(
            {
                "_comment": "ignored",
                "maturity_hours": 48,
                "tolerance_hours": 12,
                "metrics": {
                    "_note": {"weight": 99},
                    "utm_sessions": {"weight": 1.0, "per_reach": True},
                    "reactions": {"weight": 0.0, "per_reach": True},
                },
            }
        )
        assert ns.maturity_hours == 48 and ns.tolerance_hours == 12
        assert set(ns.metrics) == {"utm_sessions", "reactions"}
        assert ns.required == ["utm_sessions"]
