"""Tests for the deterministic playbook checks (`core.learning.verification`).

These matter more than most tests in the repo. This module is what stands between "a model noticed a
pattern" and "a rule now shapes every post," so the cases below are mostly *known-bad findings that
must be rejected* — the calibration the skeptic design calls for, applied to the arithmetic first.
"""

import random

from brandcortex.core.learning.verification import (
    InsufficientData,
    Observation,
    Thresholds,
    effect_size,
    leave_one_out_stability,
    permutation_test,
    verify,
)


def obs(label: str, values: list[float]) -> list[Observation]:
    return [Observation(label=label, outcome=v, post_id=f"{label}-{i}") for i, v in enumerate(values)]


class TestPermutationTest:
    def test_pure_noise_is_not_significant(self) -> None:
        """The case that matters: labels carry no information, so the test must not endorse them."""
        rng = random.Random(1234)
        values = [rng.gauss(100, 20) for _ in range(40)]
        observations = obs("a", values[:20]) + obs("b", values[20:])
        assert permutation_test(observations) > 0.05

    def test_large_real_effect_is_detected(self) -> None:
        observations = obs("a", [200.0] * 12) + obs("b", [100.0] * 12)
        assert permutation_test(observations) < 0.01

    def test_never_reports_exactly_zero(self) -> None:
        """2000 shuffles cannot justify p=0, so the estimator is (hits+1)/(n+1)."""
        observations = obs("a", [500.0] * 15) + obs("b", [1.0] * 15)
        p = permutation_test(observations)
        assert p > 0
        assert p == 1 / 2001

    def test_is_reproducible(self) -> None:
        """A stored verdict has to be recomputable, or nobody can audit it later."""
        observations = obs("a", [10, 12, 9, 15, 11]) + obs("b", [8, 7, 12, 6, 9])
        assert permutation_test(observations, seed=7) == permutation_test(observations, seed=7)

    def test_requires_two_arms(self) -> None:
        try:
            permutation_test(obs("a", [1, 2, 3]))
        except InsufficientData:
            return
        raise AssertionError("single-arm comparison should raise InsufficientData")


class TestLeaveOneOutStability:
    def test_consistent_effect_is_stable(self) -> None:
        observations = obs("a", [20, 21, 19, 20, 22, 18]) + obs("b", [10, 11, 9, 10, 12, 8])
        assert leave_one_out_stability(observations) > 0.85

    def test_single_outlier_driven_effect_is_fragile(self) -> None:
        """One post shared by a large account can manufacture an entire finding."""
        observations = obs("a", [10, 10, 10, 10, 10, 900]) + obs("b", [10, 10, 10, 10, 10, 10])
        assert leave_one_out_stability(observations) < 0.2

    def test_zero_effect_is_not_stable(self) -> None:
        observations = obs("a", [10, 10, 10]) + obs("b", [10, 10, 10])
        assert leave_one_out_stability(observations) == 0.0


class TestEffectSize:
    def test_signed_difference_of_means(self) -> None:
        assert effect_size(obs("a", [10, 20]) + obs("b", [5, 5])) == 10.0


class TestVerify:
    """End-to-end gate. Each rejection here is a rule that would otherwise have shaped every post."""

    def test_accepts_a_clean_finding(self) -> None:
        observations = obs("a", [22, 20, 24, 21, 23, 19, 25, 22, 21, 23]) + obs(
            "b", [12, 11, 13, 10, 14, 12, 11, 13, 12, 10]
        )
        result = verify(observations)
        assert result.passed, result.reasons
        assert result.checks["p_value"] < 0.05
        assert result.checks["stability"] > 0.5

    def test_rejects_thin_data(self) -> None:
        """At a few posts a day this is the common case, and the one an eager agent talks past."""
        result = verify(obs("a", [30, 32, 31]) + obs("b", [10, 11, 9]))
        assert not result.passed
        assert any("sample floor" in r for r in result.reasons)

    def test_rejects_noise_that_looks_like_a_pattern(self) -> None:
        rng = random.Random(99)
        values = [rng.gauss(50, 15) for _ in range(24)]
        result = verify(obs("a", values[:12]) + obs("b", values[12:]))
        assert not result.passed
        assert any("chance alone" in r for r in result.reasons)

    def test_rejects_outlier_driven_finding(self) -> None:
        observations = obs("a", [10, 10, 10, 10, 10, 10, 10, 10, 10, 4000]) + obs(
            "b", [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        )
        result = verify(observations)
        assert not result.passed
        assert any("outlier" in r for r in result.reasons)

    def test_rejects_multi_arm_comparison(self) -> None:
        """Multi-way comparisons must be framed pairwise so each carries its own evidence."""
        result = verify(obs("a", [1] * 10) + obs("b", [2] * 10) + obs("c", [3] * 10))
        assert not result.passed
        assert any("2 arms" in r for r in result.reasons)

    def test_never_raises_on_degenerate_input(self) -> None:
        """An unevaluable comparison is a failed one — the caller shouldn't need a try block."""
        assert not verify([]).passed
        assert not verify(obs("a", [1, 2, 3])).passed

    def test_records_what_ran_for_audit(self) -> None:
        observations = obs("a", [20] * 10) + obs("b", [10] * 10)
        checks = verify(observations).checks
        assert {"thresholds", "counts", "effect_size", "p_value", "stability"} <= set(checks)

    def test_thresholds_are_configurable(self) -> None:
        observations = obs("a", [30, 32, 31, 33]) + obs("b", [10, 11, 9, 12])
        assert not verify(observations).passed
        assert verify(observations, thresholds=Thresholds(min_per_label=4)).passed
