"""Reading, gating and versioning the playbook (spec §10.3).

The playbook is the mechanism of self-improvement: the generation engine and scheduler read the active
rules before acting, so changing a rule changes behaviour without changing code. Which is exactly why
what gets in matters more than anything else in the learning loop — a bad rule is not one bad post, it
is a bias applied to every future post until someone notices.

## The activation path

    propose  ->  verification.verify   (arithmetic: sample floor, permutation, stability)
             ->  skeptic.challenge     (four lenses, inverted burden, no proposer reasoning)
             ->  prediction recorded   (falsifiable, before it takes effect)
             ->  human gate            (voice/strategy always; low-risk knobs may auto-activate)
             ->  active
             ->  score_predictions     (reality checks it later; failures retire the rule)

`activate` refuses anything that skipped a step. The guard lives here rather than in the caller because
a check that is easy to bypass is a check that will be bypassed — under deadline, by someone reasonable,
with a good excuse.

Three properties keep the whole thing honest:

* **Versioned, never mutated.** A change writes a new version and retires the old, so any regression is
  revertible and every post records which rule versions produced it.
* **Evidence separated from verification.** `evidence`/`confidence` are what the proposer claimed;
  `verification` is what independent checks found. One agent no longer writes both.
* **Risk-tiered gating.** Timing may auto-activate. Voice may not be proposed at all.
"""

from datetime import datetime, timedelta
from typing import Any

#: Rule-key prefixes the learning loop may auto-activate once verified — low-risk, easily reverted,
#: and the spec explicitly allows it (§10.3).
AUTO_ACTIVATE_PREFIXES: tuple[str, ...] = ("timing.",)

#: Prefixes no proposal may ever touch. House voice is a fixed constraint, not an optimizable lever
#: (§10.4): an engagement-maximizing loop would rediscover the hype register the brand rejected, so the
#: protection has to be structural rather than a matter of the reflection agent behaving well.
FROZEN_PREFIXES: tuple[str, ...] = ("voice.",)


class RuleRejected(ValueError):
    """A proposal that may not proceed. Carries why, so the report can say so plainly."""


def load_active(brand: str) -> dict:
    """Return the active rule set for a brand, keyed by `rule_key`.

    Returns an empty playbook when nothing is active yet — Phase 1 runs this way on purpose, and the
    engine must behave correctly with an empty playbook.

    TODO(phase-1): implement.
    """
    raise NotImplementedError


def assert_proposable(rule_key: str) -> None:
    """Reject anything targeting a frozen area, before any work is spent on it."""
    for prefix in FROZEN_PREFIXES:
        if rule_key.startswith(prefix):
            raise RuleRejected(
                f"{rule_key!r} targets frozen area {prefix!r}: house voice is a fixed constraint, not "
                "something the learning loop may tune. Change it through brand_config with human "
                "authorship instead."
            )


def propose(
    brand: str,
    rule_key: str,
    rule: str,
    payload: dict,
    *,
    proposed_by: str,
    evidence: str,
    sample_size: int,
    confidence: float,
    verification: dict,
    prediction: dict,
) -> None:
    """Record a proposed rule. Never activates directly.

    `verification` and `prediction` are required arguments rather than optional extras: a proposal
    without independent checks and without a falsifiable prediction is exactly the artifact this design
    exists to prevent, and making them optional would let it back in through the default value.

    TODO(phase-2): persist as `status=proposed`.
    """
    assert_proposable(rule_key)
    raise NotImplementedError


def can_activate(rule: Any) -> tuple[bool, list[str]]:
    """Whether a proposal has earned activation, and what is missing if not.

    Checks the provenance the schema now makes visible:

    1. not in a frozen area
    2. deterministic verification ran and passed
    3. the skeptic ran and every lens declined to refute
    4. a falsifiable prediction is recorded, so reality can score it later

    Returns reasons rather than raising, because the playbook UI shows them next to the rule — a
    blocked proposal is useful information, not an error.
    """
    missing: list[str] = []
    key = getattr(rule, "rule_key", "") or ""

    for prefix in FROZEN_PREFIXES:
        if key.startswith(prefix):
            missing.append(f"targets frozen area {prefix!r} and may never activate")

    verification = getattr(rule, "verification", None) or {}
    if not verification:
        missing.append("no verification record — deterministic checks did not run")
    elif not verification.get("passed"):
        reasons = verification.get("reasons") or ["unspecified"]
        missing.append("failed deterministic checks: " + "; ".join(reasons))

    skeptic = verification.get("skeptic") if verification else None
    if not skeptic:
        missing.append("no skeptic record — adversarial review did not run")
    elif not skeptic.get("survived"):
        refuted = [v["lens"] for v in skeptic.get("lenses", []) if v.get("refuted")]
        missing.append("refuted by " + ", ".join(refuted or ["skeptic"]))

    if not (getattr(rule, "prediction", None) or {}):
        missing.append("no prediction recorded — nothing for reality to falsify later")

    return (not missing, missing)


def is_auto_activatable(rule_key: str) -> bool:
    """Low-risk knobs skip the human gate once verified; everything else waits for a person."""
    return rule_key.startswith(AUTO_ACTIVATE_PREFIXES)


#: Past this, a rule's evidence describes an era rather than a system. The channel's ranking algorithm
#: changes continuously and without announcement, so a finding from six months ago may be a true
#: statement about a delivery system that no longer exists.
EVIDENCE_STALE_DAYS = 180


def is_evidence_stale(rule: Any, *, as_of: datetime, max_age_days: int = EVIDENCE_STALE_DAYS) -> bool:
    """Whether a rule's evidence is old enough to warrant re-testing.

    A rule with no recorded window counts as stale: unassessable and old are the same thing here, and
    the failure mode to avoid is an ancient rule sitting in the playbook looking exactly as
    authoritative as one earned last week.

    Staleness is a flag for the playbook UI and the reflection report, not an automatic retirement.
    The rule may well still hold — but it should have to prove that again rather than coast.
    """
    evidence_to: datetime | None = getattr(rule, "evidence_to", None)
    if evidence_to is None:
        return True
    return (as_of - evidence_to) > timedelta(days=max_age_days)


def activate(rule_id, *, approved_by: str | None = None) -> None:
    """Activate a verified rule, retiring the previous version of the same `rule_key`.

    Must call `can_activate` and refuse when it returns False, and must require `approved_by` for any
    rule outside `AUTO_ACTIVATE_PREFIXES`.

    TODO(phase-2).
    """
    raise NotImplementedError


def score_predictions(brand: str) -> list[dict]:
    """Score active rules against what actually happened since they activated.

    The one reviewer in this system that does not share the model's priors. A rule predicted something
    measurable before it took effect; this reads the outcome and compares.

    A rule that fails its own prediction is retired even if its original evidence was clean — that is
    the whole value of having recorded one. Retirement is not a bug report; it is the loop working.

    TODO(phase-2): implement once the insights fetcher has history to score against.
    """
    raise NotImplementedError


def rollback(brand: str, rule_key: str, *, to_version: int) -> None:
    """Revert to an earlier version. Reversibility is a stated guardrail (§10.4). TODO(phase-2)."""
    raise NotImplementedError
