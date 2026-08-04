"""The reflection agent — reads outcomes, writes the playbook (spec §10.2, §10.3).

Runs on a schedule and performs:

* **Feature attribution vs the north star** — which features move UTM sessions and amplification.
* **Timing model per source type** — best hour/weekday, in the brand's timezone.
* **Format / copy / intro ranking with fatigue detection** — a line that used to travel and no longer
  does should leave rotation.
* **Anomaly mining** — outliers with *written hypotheses*, not just flagged numbers.
* **Content-opportunity scan** — see `opportunities.py`.

Output is twofold: proposed playbook rules, and a human-readable "what I learned" report. The report is
not decoration; it is how a human keeps oversight of a system that rewrites its own instructions.

## This agent does not grade itself

Nothing here decides whether a finding is real. That was the original design flaw: one agent produced
the claim, the evidence, and the confidence in its own claim. The path now is:

    reflect()  ->  verification.verify()   arithmetic — sample floor, permutation test, stability
               ->  skeptic.challenge()     four lenses, inverted burden, no access to this reasoning
               ->  prediction recorded     falsifiable, before the rule takes effect
               ->  playbook.can_activate() refuses anything that skipped a step

`ReflectionReport.proposed_rules` are therefore *candidates*, never conclusions. This agent should
report an effect it observed and let the checks decide; a `confidence` it assigns itself is context for
a human, not a gate.

`comparisons_examined` must be the true number of comparisons this run considered — including the ones
that showed nothing. The multiplicity lens is worthless if it is fed the count after filtering, and
under-reporting it is the easiest way for a genuinely fished result to look clean.

Two constraints bind the agent absolutely:

* The north star is **UTM sessions + amplification**. Reactions are recorded and never optimized for —
  an engagement-maximizing loop drifts back to the hype voice the owner rejected, because hype wins
  reactions in the short term. Metric choice is what prevents that.
* **Voice is not optimizable.** The agent may not propose a rule that alters it.
"""

from dataclasses import dataclass


@dataclass
class ReflectionReport:
    brand: str
    window_days: int
    summary: str
    #: Candidates, not conclusions — each still has to clear verification, the skeptic, and the gate.
    proposed_rules: list[dict]
    anomalies: list[dict]
    sample_size: int
    #: Every comparison this run considered, including the ones that showed nothing. Feeds the
    #: multiplicity lens; under-reporting it is how a fished result passes for a clean one.
    comparisons_examined: int = 0


def reflect(brand: str, *, window_days: int = 30) -> ReflectionReport:
    """Analyse recent posts and emit proposals plus a written report.

    TODO(phase-2): implement. Below roughly 20–30 posts the correct output is usually "not enough
    evidence yet" — the spec is explicit that meaningful learning takes weeks to months at a few posts
    a day, and a confident finding from five posts is noise wearing a lab coat.
    """
    raise NotImplementedError
