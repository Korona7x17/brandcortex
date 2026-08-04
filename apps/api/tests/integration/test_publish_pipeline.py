"""End-to-end pipeline tests against fake adapters (spec §7)."""

import pytest


@pytest.mark.skip(reason="TODO(phase-1): implement Orchestrator")
def test_ingest_creates_draft_and_captures_features() -> None:
    """Features are captured at draft time from post #1 — they cannot be reconstructed later, and the
    reflection agent needs history waiting for it when Phase 2 lands."""


@pytest.mark.skip(reason="TODO(phase-1): implement Orchestrator")
def test_ingest_is_idempotent_on_content_id() -> None: ...


@pytest.mark.skip(reason="TODO(phase-1): implement Orchestrator")
def test_publish_posts_photo_then_first_comment() -> None: ...


@pytest.mark.skip(reason="TODO(phase-1): implement Orchestrator")
def test_failed_first_comment_leaves_post_recoverable_not_published() -> None:
    """A photo without its link comment is a broken post, not a partial success."""
