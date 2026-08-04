"""Scheduled entrypoint for the reflection agent (spec §10.3).

Runs `core.learning.reflection.reflect`, persists proposed playbook rules, and emits the
human-readable "what I learned" report. Proposals land as `proposed`; only the approval gate (or the
auto-tune allowance for low-risk knobs like timing) makes them active.
"""


def run_once(brand: str, *, window_days: int = 30) -> None:
    """TODO(phase-2)."""
    raise NotImplementedError
