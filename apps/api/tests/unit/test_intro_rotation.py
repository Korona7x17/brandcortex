"""Intro rotation tests (spec §6.4, §6.5)."""

import pytest


@pytest.mark.skip(reason="TODO(phase-1): implement core.generation.intro_rotation")
def test_never_repeats_within_lookback() -> None: ...


@pytest.mark.skip(reason="TODO(phase-1): implement core.generation.intro_rotation")
def test_falls_back_to_least_recently_used_when_bank_exhausted() -> None:
    """A small bank plus a busy week must not block a post — degrade to LRU rather than failing."""
