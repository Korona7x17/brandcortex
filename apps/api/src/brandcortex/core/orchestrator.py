"""The end-to-end pipeline (spec §7).

    1. Brand renders content -> content item + asset written
    2. BrandCortex ingests (table-watch, or an admin "Queue to BrandCortex" flag)
    3. Generation engine drafts post + first comment, reading the playbook
    4. HUMAN REVIEW / approve / edit in the brandcortex.app UI
    5. Scheduler assigns a slot (alternation, spacing, preferred time)
    6. Channel adapter publishes (FB: photo + caption)
    7. Adapter posts the first comment with the canonical link immediately
    8. Record channel_post_id, channel_comment_id, status -> published
    9. Insights fetcher snapshots performance over the next 24–48h

Step 4 is not optional in Phase 1. Human-in-the-loop first; full auto-publish only after the generation
engine has earned trust.

This module names no brand and no channel: it resolves adapters through the registry by the keys stored
on the post. That is what makes adding IG or brand #2 a config-and-adapter job.
"""

from brandcortex.schemas.content_item import ContentItem


class Orchestrator:
    def ingest(self, item: ContentItem) -> None:
        """Steps 2–3: persist a draft post, generate copy, capture features.

        Idempotent on `content_id` + channel — re-delivery from a source adapter must not create a
        second draft.

        TODO(phase-1): implement.
        """
        raise NotImplementedError

    def approve(self, post_id: str, *, edited_text: str | None = None) -> None:
        """Step 4: mark a draft approved, keeping any human edit.

        Human edits are the most valuable training signal in the system — what a reviewer changed is a
        direct statement about what the engine got wrong — so record the delta rather than only the
        final text.

        TODO(phase-1): implement.
        """
        raise NotImplementedError

    def schedule(self, post_id: str) -> None:
        """Step 5: assign a slot. TODO(phase-2); open decision #5 covers whether Phase 1 uses it."""
        raise NotImplementedError

    def publish(self, post_id: str) -> None:
        """Steps 6–8: publish the photo, then the first comment, then record both channel ids.

        The comment is part of the operation, not a follow-up: a post whose link comment failed is
        broken, since the link is the entire reason the post exists. Leave such a post recoverable and
        surface the failure.

        TODO(phase-1): implement.
        """
        raise NotImplementedError
