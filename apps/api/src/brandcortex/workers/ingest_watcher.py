"""Watches source adapters for new content items (spec §4.3, §7 step 2).

Primary intake per the spec's recommendation is table-watch: the brand writes to `card_renders` and
this worker polls. Open decision #1 has not been settled — keep the direct-API path available for
on-demand renders either way.

Polling must be idempotent: `Orchestrator.ingest` deduplicates on content_id + channel, so
re-delivery is harmless and the worker never needs exactly-once semantics.

## The cursor

`max(posts.source_generated_at)` for the brand, not a stored watermark. Two reasons. It cannot drift
out of step with what was actually drafted, because it *is* what was actually drafted. And it
survives a restart, a redeploy and a database restore with no separate piece of state to restore
alongside it.

The cost is that the boundary row gets re-polled every cycle, since the filter is strictly-greater
and the newest drafted row keeps matching nothing new. Re-delivery is free — ingest returns the
existing post — so paying that beats owning a watermark.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from brandcortex.adapters import registry
from brandcortex.core.orchestrator import Orchestrator
from brandcortex.db.models import Post, PostStatus
from brandcortex.db.session import session_scope

logger = logging.getLogger(__name__)

POLL_LIMIT = 50


def cursor_for(session: Session, brand: str):
    """The newest `generated_at` this brand has drafted, or None to start from the beginning."""
    return session.scalar(select(func.max(Post.source_generated_at)).where(Post.brand == brand))


def run_once(
    brand: str,
    *,
    channel: str | None = None,
    limit: int = POLL_LIMIT,
    session: Session | None = None,
) -> dict[str, int]:
    """Poll one brand's source adapter and ingest what it returns.

    Returns counts by outcome — drafted, failed, already seen. A cycle that drafts nothing and fails
    forty times looks identical to a quiet one if you only return a total, and that is the exact
    shape of an outage nobody notices.
    """
    adapter = registry.get_source_adapter(brand)
    channels = [channel] if channel else registry.registered_channels()
    counts = {"polled": 0, "drafted": 0, "failed": 0, "seen": 0}

    with session_scope(session) as db:
        items = adapter.poll(since=cursor_for(db, brand), limit=limit)
        counts["polled"] = len(items)
        orchestrator = Orchestrator(db)

        for item in items:
            for target in channels:
                already = db.scalar(
                    select(Post.id).where(
                        Post.content_id == item.content_id, Post.channel == target
                    )
                )
                post = orchestrator.ingest(item, channel=target)
                if already is not None:
                    counts["seen"] += 1
                elif post.status is PostStatus.FAILED:
                    counts["failed"] += 1
                    logger.warning("draft rejected for %s: %s", item.content_id, post.error)
                else:
                    counts["drafted"] += 1
                adapter.mark_ingested(item.content_id)

    logger.info("ingest cycle for %s: %s", brand, counts)
    return counts
