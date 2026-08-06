"""Snapshots post performance over its first days (spec §9).

Each published post is sampled a few times across its first 2–3 days because the numbers keep settling;
a single reading taken an hour after publishing understates everything and would bias the whole learning
loop toward whatever posts happened to spike early.

Sampling must cover the maturity age `outcomes` compares at (`brand_config.north_star.maturity_hours`,
72h by default) within its tolerance window. A post with snapshots at 1h and 20d but nothing near 72h is
excluded from every comparison — the learning loop simply never sees it.

Also pulls UTM-attributed sessions from site analytics — the north star — which is a different source
from the channel's own metrics and will not agree with its click count. Attribute sessions over a fixed
window from publish so posts stay comparable: a link in a comment can be shared onward and keep drawing
traffic for months, and an open-ended count would flatter whichever posts are oldest.
"""


def run_once() -> int:
    """Snapshot every post still inside its measurement window. TODO(phase-2)."""
    raise NotImplementedError
