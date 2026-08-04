"""Tests for the activation gate (`core.learning.playbook`).

Each case is a way an unverified rule could reach `active` and start shaping every post. The gate lives
in `playbook` rather than in the caller precisely so these cases can be enumerated in one place.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from brandcortex.core.learning.playbook import (
    RuleRejected,
    assert_proposable,
    can_activate,
    is_auto_activatable,
    is_evidence_stale,
)


@dataclass
class FakeRule:
    """Structural stand-in for `PlaybookRule` — the gate reads attributes, not the ORM."""

    rule_key: str = "timing.preferred_hour.swimmer"
    verification: dict[str, Any] = field(default_factory=dict)
    prediction: dict[str, Any] = field(default_factory=dict)
    evidence_to: datetime | None = None


PASSING_VERIFICATION = {
    "passed": True,
    "p_value": 0.01,
    "stability": 0.8,
    "skeptic": {
        "survived": True,
        "lenses": [
            {"lens": "confound", "refuted": False, "argument": "..."},
            {"lens": "multiplicity", "refuted": False, "argument": "..."},
            {"lens": "consistency", "refuted": False, "argument": "..."},
            {"lens": "generalization", "refuted": False, "argument": "..."},
        ],
    },
}
PREDICTION = {"metric": "utm_sessions", "direction": "increase", "min_effect": 0.15, "horizon": 20}


def fully_verified(**overrides: Any) -> FakeRule:
    return FakeRule(verification=dict(PASSING_VERIFICATION), prediction=dict(PREDICTION), **overrides)


class TestFrozenAreas:
    def test_voice_rules_cannot_be_proposed(self) -> None:
        """House voice is a fixed constraint. The protection is structural because an
        engagement-maximizing loop would otherwise rediscover the register the brand rejected."""
        try:
            assert_proposable("voice.max_emoji")
        except RuleRejected as exc:
            assert "frozen" in str(exc)
            return
        raise AssertionError("voice rules must be unproposable")

    def test_voice_rules_cannot_activate_even_if_fully_verified(self) -> None:
        ok, missing = can_activate(fully_verified(rule_key="voice.banned_phrases"))
        assert not ok
        assert any("frozen" in m for m in missing)

    def test_non_frozen_keys_are_proposable(self) -> None:
        assert_proposable("timing.preferred_hour.swimmer")


class TestCanActivate:
    def test_fully_verified_rule_passes(self) -> None:
        ok, missing = can_activate(fully_verified())
        assert ok, missing

    def test_blocks_rule_with_no_verification(self) -> None:
        """The original self-grading failure: a proposal arriving with only its own confidence."""
        ok, missing = can_activate(FakeRule(prediction=dict(PREDICTION)))
        assert not ok
        assert any("no verification" in m for m in missing)

    def test_blocks_rule_that_failed_deterministic_checks(self) -> None:
        rule = fully_verified()
        rule.verification = {"passed": False, "reasons": ["below the sample floor of 8 per arm"]}
        ok, missing = can_activate(rule)
        assert not ok
        assert any("sample floor" in m for m in missing)

    def test_blocks_rule_the_skeptic_never_saw(self) -> None:
        rule = fully_verified()
        rule.verification = {"passed": True}
        ok, missing = can_activate(rule)
        assert not ok
        assert any("no skeptic" in m for m in missing)

    def test_blocks_rule_refuted_by_a_single_lens(self) -> None:
        """Any one refutation blocks: the lenses ask different questions, so three abstaining on a
        confound they weren't asked about says nothing about the one that found it."""
        rule = fully_verified()
        rule.verification = {
            "passed": True,
            "skeptic": {
                "survived": False,
                "lenses": [
                    {"lens": "confound", "refuted": True, "argument": "arms differ in post time"},
                    {"lens": "multiplicity", "refuted": False, "argument": "..."},
                ],
            },
        }
        ok, missing = can_activate(rule)
        assert not ok
        assert any("confound" in m for m in missing)

    def test_blocks_rule_with_no_prediction(self) -> None:
        """Without a prediction there is nothing for reality to falsify, and the only genuinely
        independent reviewer in the system never gets to weigh in."""
        rule = fully_verified()
        rule.prediction = {}
        ok, missing = can_activate(rule)
        assert not ok
        assert any("prediction" in m for m in missing)

    def test_reports_every_reason_at_once(self) -> None:
        """The playbook UI shows these next to the rule; one-at-a-time would mean N review cycles."""
        ok, missing = can_activate(FakeRule(rule_key="voice.tone"))
        assert not ok
        assert len(missing) >= 3


class TestRiskTiering:
    def test_timing_is_auto_activatable(self) -> None:
        assert is_auto_activatable("timing.preferred_hour.swimmer")

    def test_strategy_is_not(self) -> None:
        assert not is_auto_activatable("format.intro_rotation.lookback")
        assert not is_auto_activatable("hashtags.core")


class TestEvidenceStaleness:
    """The channel's ranking algorithm changes without announcement, so a rule is always a claim about
    the era it was learned in."""

    def test_recent_evidence_is_fresh(self) -> None:
        rule = FakeRule()
        rule.evidence_to = datetime(2026, 7, 1, tzinfo=UTC)
        assert not is_evidence_stale(rule, as_of=datetime(2026, 8, 4, tzinfo=UTC))

    def test_old_evidence_is_stale(self) -> None:
        rule = FakeRule()
        rule.evidence_to = datetime(2025, 8, 1, tzinfo=UTC)
        assert is_evidence_stale(rule, as_of=datetime(2026, 8, 4, tzinfo=UTC))

    def test_missing_window_counts_as_stale(self) -> None:
        """Unassessable and old are the same thing: the failure to avoid is an ancient rule looking as
        authoritative as one earned last week."""
        assert is_evidence_stale(FakeRule(), as_of=datetime(2026, 8, 4, tzinfo=UTC))
