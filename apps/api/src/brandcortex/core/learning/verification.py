"""Deterministic checks a playbook rule must survive before anything else looks at it.

This module exists to take the highest-stakes judgment in the system away from a model. "Is this
pattern real or is it noise?" has an arithmetic answer, and a reflection agent asserting `confidence:
0.8` is not that answer — it is the same agent that wants the rule to pass, grading its own work.

Three checks, each targeting a different way a finding is wrong:

* **Sample floor** — at a few posts a day, most comparisons simply do not have the data yet. Cheapest
  check, catches the most cases, and it is the one an eager agent is most likely to talk past.
* **Permutation test** — if the labels were meaningless, how often would chance alone produce an effect
  this large? Distribution-free, so it makes no normality assumption that engagement data would violate
  anyway.
* **Leave-one-out stability** — does the effect survive dropping the single most influential post? One
  card that happened to get shared by a big account can manufacture an entire "finding".

All three are seeded and pure, so a stored verdict can be recomputed later and audited. That matters:
a check nobody can re-run is a check nobody can trust.

Thresholds are deliberately conservative. The cost of a false positive here is a rule that quietly
shapes every future post; the cost of a false negative is waiting a few more weeks, which the spec
already tells us to expect (§10.5).
"""

import random
from dataclasses import dataclass, field
from statistics import fmean
from typing import Any


@dataclass(frozen=True)
class Observation:
    """One post's contribution to a comparison."""

    label: str
    #: North-star value for this post — UTM sessions plus weighted amplification, never reactions.
    outcome: float
    #: Post id, so a rejected finding can be traced back to what produced it.
    post_id: str | None = None


@dataclass(frozen=True)
class Thresholds:
    #: Per-arm minimum. Below this, no comparison is meaningful regardless of how clean it looks.
    min_per_label: int = 8
    #: Permutation p-value ceiling. 0.05 is convention, not law; at this volume it is already generous.
    max_p_value: float = 0.05
    #: Effect must retain this share of its size after dropping the most influential single post.
    min_stability: float = 0.5
    permutations: int = 2000
    seed: int = 0


@dataclass
class VerificationResult:
    passed: bool
    #: Structured record of what ran and what it returned. Written to `PlaybookRule.verification` —
    #: by the checks, never by the proposing agent.
    checks: dict[str, Any] = field(default_factory=dict)
    #: Human-readable failure reasons, empty when passed.
    reasons: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed


class InsufficientData(ValueError):
    """A comparison that cannot be evaluated at all — not the same as one that failed."""


def _split(observations: list[Observation]) -> tuple[str, str, list[float], list[float]]:
    labels = sorted({o.label for o in observations})
    if len(labels) != 2:
        raise InsufficientData(
            f"expected exactly 2 labels to compare, got {len(labels)}: {labels}. "
            "Frame multi-way comparisons as pairwise ones so each gets its own evidence."
        )
    a, b = labels
    return a, b, [o.outcome for o in observations if o.label == a], [
        o.outcome for o in observations if o.label == b
    ]


def effect_size(observations: list[Observation]) -> float:
    """Difference in mean outcome between the two arms, first label minus second."""
    _, _, xs, ys = _split(observations)
    if not xs or not ys:
        raise InsufficientData("both labels need at least one observation")
    return fmean(xs) - fmean(ys)


def permutation_test(
    observations: list[Observation], *, permutations: int = 2000, seed: int = 0
) -> float:
    """Probability of seeing an effect this large if the labels carried no information.

    Shuffles the labels `permutations` times and counts how often chance alone reproduces the observed
    difference. Two-sided.

    Returns `(hits + 1) / (permutations + 1)` rather than `hits / permutations`, so a p-value is never
    reported as exactly zero — with 2000 shuffles the evidence simply cannot justify that claim.
    """
    a, _, xs, ys = _split(observations)
    if not xs or not ys:
        raise InsufficientData("both labels need at least one observation")

    observed = abs(fmean(xs) - fmean(ys))
    pool = [o.outcome for o in observations]
    n_a = len(xs)
    rng = random.Random(seed)

    hits = 0
    for _ in range(permutations):
        rng.shuffle(pool)
        if abs(fmean(pool[:n_a]) - fmean(pool[n_a:])) >= observed:
            hits += 1
    return (hits + 1) / (permutations + 1)


def leave_one_out_stability(observations: list[Observation]) -> float:
    """Share of the effect that survives dropping the single most influential observation.

    Returns `min |effect with one post removed| / |full effect|`. A value near 1.0 means no single post
    is carrying the result; 0.2 means one post is carrying almost all of it.

    Returns 0.0 when the full effect is zero — nothing to be stable about.
    """
    full = abs(effect_size(observations))
    if full == 0:
        return 0.0

    worst = full
    for i in range(len(observations)):
        reduced = observations[:i] + observations[i + 1 :]
        try:
            worst = min(worst, abs(effect_size(reduced)))
        except InsufficientData:
            # Removing this post empties an arm — the comparison was too thin to be stable anyway.
            return 0.0
    return worst / full


def verify(
    observations: list[Observation], *, thresholds: Thresholds | None = None
) -> VerificationResult:
    """Run every deterministic check. This is the gate a rule must clear before a skeptic is worth
    spending a token on, and before a human is worth interrupting.

    Never raises for thin data — an unevaluable comparison is a failed one, reported as such.
    """
    t = thresholds or Thresholds()
    checks: dict[str, Any] = {"thresholds": t.__dict__.copy()}
    reasons: list[str] = []

    counts = {label: sum(1 for o in observations if o.label == label) for label in {o.label for o in observations}}
    checks["counts"] = counts

    if len(counts) != 2:
        return VerificationResult(
            passed=False,
            checks=checks,
            reasons=[f"needs exactly 2 arms to compare, got {sorted(counts)}"],
        )

    thin = {label: n for label, n in counts.items() if n < t.min_per_label}
    if thin:
        reasons.append(
            f"below the sample floor of {t.min_per_label} per arm: "
            + ", ".join(f"{label}={n}" for label, n in sorted(thin.items()))
        )

    checks["effect_size"] = effect_size(observations)
    checks["p_value"] = permutation_test(
        observations, permutations=t.permutations, seed=t.seed
    )
    checks["stability"] = leave_one_out_stability(observations)

    if checks["p_value"] > t.max_p_value:
        reasons.append(
            f"p={checks['p_value']:.3f} exceeds {t.max_p_value} — chance alone reproduces an effect "
            "this large too often"
        )
    if checks["stability"] < t.min_stability:
        reasons.append(
            f"stability={checks['stability']:.2f} below {t.min_stability} — dropping one post collapses "
            "the effect, so it rests on an outlier"
        )

    return VerificationResult(passed=not reasons, checks=checks, reasons=reasons)
