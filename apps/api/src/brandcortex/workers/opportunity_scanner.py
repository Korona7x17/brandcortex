"""Scheduled entrypoint for the content-opportunity scan (spec §10.2).

Queues high-shareability items the brand has produced but never posted. This is the half of the loop
that creates new posts rather than tuning existing ones.
"""


def run_once(brand: str, *, limit: int = 10) -> int:
    """TODO(phase-2)."""
    raise NotImplementedError
