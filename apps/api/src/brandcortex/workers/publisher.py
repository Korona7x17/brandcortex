"""Publishes posts whose slot has arrived (spec §7 steps 6–8).

Retry policy matters here: a transient Graph error deserves a retry, an expired token does not — it
needs a human. Retrying a permission failure only delays that. And a post whose photo landed but
whose link comment failed must not be retried from the top, or the Page gets a duplicate photo.

That last case is why this worker does not simply catch and retry. `Orchestrator.publish` records
`channel_post_id` even when the comment fails, so a retry has something to reconcile against rather
than a blank row that looks like nothing happened.

BrandCortex holds the schedule rather than handing it to Meta. Native scheduling would show the post
in Business Suite, but a comment cannot be attached to a post that does not exist yet, so the link
would depend on a second job firing later — and a live card with no link is the one failure the whole
design exists to prevent.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from brandcortex.core.orchestrator import InvalidTransition, Orchestrator, PublishFailed
from brandcortex.db.models import Post, PostStatus
from brandcortex.db.session import session_scope

logger = logging.getLogger(__name__)

#: How late a slot may be before it is skipped rather than published. A worker that was down for two
#: days should not wake up and publish two days of backlog at once into an audience that has moved on.
MAX_LATENESS_HOURS = 6


def due(session: Session, *, now: datetime, brand: str | None = None) -> list[Post]:
    """Scheduled posts whose time has come and has not long gone."""
    query = (
        select(Post)
        .where(Post.status == PostStatus.SCHEDULED, Post.scheduled_for <= now)
        .order_by(Post.scheduled_for)
    )
    if brand:
        query = query.where(Post.brand == brand)
    return list(session.scalars(query).all())


def run_once(
    *,
    brand: str | None = None,
    now: datetime | None = None,
    session: Session | None = None,
    orchestrator: Orchestrator | None = None,
) -> dict[str, int]:
    """Publish everything currently due.

    Returns counts by outcome. One post failing does not stop the rest: a rate limit on the first
    should not hold up the second, and a stale token will fail all of them identically anyway.
    """
    at = now or datetime.now(UTC)
    counts = {"due": 0, "published": 0, "failed": 0, "skipped_late": 0}

    with session_scope(session) as db:
        pending = due(db, now=at, brand=brand)
        counts["due"] = len(pending)
        driver = orchestrator or Orchestrator(db)

        for post in pending:
            scheduled = post.scheduled_for
            if scheduled and scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=UTC)
            lateness = (at - scheduled).total_seconds() / 3600 if scheduled else 0

            if lateness > MAX_LATENESS_HOURS:
                # Left scheduled on purpose rather than failed: nothing is wrong with the post, its
                # moment simply passed, and a person should choose the new one.
                counts["skipped_late"] += 1
                logger.warning(
                    "post %s is %.1fh past its slot — skipping rather than publishing late",
                    post.id,
                    lateness,
                )
                continue

            try:
                driver.publish(post.id)
                counts["published"] += 1
            except (PublishFailed, InvalidTransition) as exc:
                # InvalidTransition here is a pre-flight refusal (stale links, missing pieces): the
                # post stays scheduled and visible rather than failed, but it must not take the rest
                # of the cycle down with it.
                counts["failed"] += 1
                logger.error("publish failed for %s: %s", post.id, exc)

    logger.info("publish cycle: %s", counts)
    return counts


def main() -> int:
    """`python -m brandcortex.workers.publisher` — one cycle, for a cron schedule.

    A loop with a sleep would also work, but a cron running one cycle is the same behaviour with
    the platform owning the restart policy — and a crash loses one cycle, not the schedule.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    from brandcortex.adapters import registry

    registry.bootstrap()
    counts = run_once()
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
