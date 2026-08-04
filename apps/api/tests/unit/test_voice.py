"""Voice constraint tests (spec §6.1, §10.4).

These are the tests that keep the product's character intact. The learning loop can change timing,
formats, and hooks; it cannot be allowed to change voice, and a validator is the only thing that
actually enforces that at runtime.
"""

import pytest


@pytest.mark.skip(reason="TODO(phase-1): implement core.generation.voice")
def test_rejects_stacked_emojis() -> None: ...


@pytest.mark.skip(reason="TODO(phase-1): implement core.generation.voice")
def test_rejects_link_in_post_body() -> None:
    """A URL in the caption costs reach and burns Meta's monthly link allowance — links belong in the
    first comment."""


@pytest.mark.skip(reason="TODO(phase-1): implement core.generation.voice")
def test_rejects_echo_of_on_image_tagline() -> None: ...
