"""Adversarial review of a surviving playbook proposal.

Runs only after `verification.verify` passes. That ordering is the point: arithmetic settles what
arithmetic can settle, and the model is spent only on the failure modes a p-value cannot see — a
confound, a fished hypothesis, a rule that contradicts one already active.

## Three design rules, each aimed at a specific way self-review fails

**The skeptic never sees the proposer's reasoning.** It receives the claim and the raw observations,
never the analysis that produced them. A reviewer handed an argument evaluates the argument; a reviewer
handed data has to do independent work. This is why a "fresh instance" of the same model is not
automatically an independent check — what you withhold matters more than which weights you call.

**The burden of proof is inverted.** The question is never "is this sound?" but "make the strongest
case this is wrong, and default to refuted when uncertain." Models ratify what they are asked to
approve. Passing must cost effort; failing must be free.

**Lenses are diverse, not redundant.** Three identical skeptics correlate almost perfectly — same
weights, same priors, same blind spots — so they mostly buy the illusion of three opinions. Four
different *questions* cover far more failure space than four votes on one question.

## Auditing

A skeptic that has never rejected anything is not a safeguard, it is a ritual. Every verdict is
persisted so `rejection_rate()` can be read against reality, and `CALIBRATION_CASES` holds known-bad
findings the suite feeds it to confirm it still says no.
"""

from dataclasses import dataclass, field
from typing import Any

from brandcortex.core.learning.verification import Observation


@dataclass(frozen=True)
class Lens:
    key: str
    #: What this lens alone is responsible for catching.
    question: str


#: Each lens must be able to fail a proposal on its own. None of these is computable, which is exactly
#: why they are the model's job and the checks in `verification.py` are not.
LENSES: tuple[Lens, ...] = (
    Lens(
        "confound",
        "Name a mechanism that would produce this pattern without the causal claim being true. "
        "Consider whether the two arms differ in when they were posted, what subjects they covered, "
        "or how they were selected, rather than in the feature being credited.",
    ),
    Lens(
        "multiplicity",
        "How many comparisons were examined to surface this one? If many features were scanned across "
        "the same posts, the most striking result is expected to look striking by chance. State how "
        "much of this finding survives that.",
    ),
    Lens(
        "consistency",
        "Does this contradict an active rule, or restate one already in force? A rule that conflicts "
        "with an active rule must not be activated alongside it; a rule that merely restates one adds "
        "no information and should be rejected as redundant.",
    ),
    Lens(
        "generalization",
        "Does this depend on something that will not recur — one exceptional subject, one event, one "
        "seasonal moment? A rule is a claim about future posts, not a description of past ones.",
    ),
)


@dataclass
class LensVerdict:
    lens: str
    refuted: bool
    argument: str


@dataclass
class SkepticVerdict:
    #: True only when every lens declines to refute. Any single refutation blocks activation.
    survived: bool
    verdicts: list[LensVerdict] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.survived

    @property
    def refutations(self) -> list[LensVerdict]:
        return [v for v in self.verdicts if v.refuted]

    def as_record(self) -> dict[str, Any]:
        """Serialized for `PlaybookRule.verification`, so a rejection can be read back later."""
        return {
            "survived": self.survived,
            "lenses": [
                {"lens": v.lens, "refuted": v.refuted, "argument": v.argument} for v in self.verdicts
            ],
        }


PROMPT_TEMPLATE = """\
You are reviewing a proposed rule for an automated content system. Your job is to REFUTE it.

Claim: {claim}

Observations (raw, unanalyzed):
{observations}

Active rules already in force:
{active_rules}

Comparisons examined in this analysis run: {comparisons_examined}

{lens_question}

Answer only this question. Do not assess the claim's overall merit, and do not comment on the other
ways it might be wrong — other reviewers hold those.

Default to refuted. If you cannot construct a specific, concrete argument that the claim survives your
question, return refuted. "It seems plausible" is a refutation, not a defence.
"""


def challenge(
    claim: str,
    observations: list[Observation],
    *,
    active_rules: list[str],
    comparisons_examined: int,
    lenses: tuple[Lens, ...] = LENSES,
) -> SkepticVerdict:
    """Run every lens against a proposal and combine the verdicts.

    Note what is deliberately absent from the signature: the proposing agent's evidence, reasoning, and
    self-reported confidence. Passing them would defeat the whole exercise.

    `comparisons_examined` must be the true count of comparisons the reflection run considered, not the
    count it chose to report. The multiplicity lens is worthless if it is fed the filtered number.

    Any single refutation blocks the rule. Majority voting is the wrong rule here: the lenses ask
    different questions, so three abstaining on a confound they were not asked about says nothing about
    the one that found it.

    TODO(phase-2): implement against the Anthropic API. Each lens is an independent call — no shared
    conversation, or the later lenses anchor on the earlier ones.
    """
    raise NotImplementedError


#: Findings that must be rejected. A checker never tested on known-bad input is untested code sitting
#: in the highest-stakes path in the system.
CALIBRATION_CASES: tuple[dict[str, Any], ...] = (
    {
        "name": "one_viral_post",
        "claim": "Posts naming a club drive 3x the traffic of posts that do not.",
        "note": "Effect rests entirely on a single post an unusually large account shared.",
        "expect_refuted_by": "confound",
    },
    {
        "name": "fished_hypothesis",
        "claim": "Tuesday posts outperform Thursday posts.",
        "note": "Surfaced by scanning 7 weekdays x 6 features across 40 posts.",
        "expect_refuted_by": "multiplicity",
    },
    {
        "name": "restates_active_rule",
        "claim": "Posting in the evening beats posting at midday.",
        "note": "An active rule already fixes the preferred window to 19:00-21:00.",
        "expect_refuted_by": "consistency",
    },
    {
        "name": "unrepeatable_subject",
        "claim": "Posts about swimmers over 70 outperform all other age groups.",
        "note": "All three such posts covered the same record-holding individual.",
        "expect_refuted_by": "generalization",
    },
)


def rejection_rate(verdicts: list[SkepticVerdict]) -> float:
    """Share of proposals refuted. Read this before trusting the skeptic.

    A rate at or near zero over a meaningful number of runs means the skeptic is ratifying, and the
    prompts or the model need work — not that every proposal was sound.
    """
    if not verdicts:
        return 0.0
    return sum(1 for v in verdicts if not v.survived) / len(verdicts)
