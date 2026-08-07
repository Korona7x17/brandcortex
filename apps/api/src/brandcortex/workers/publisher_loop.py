"""Drives `publisher.run_once` from inside the API process, on a timer.

`publisher.main()` is cron-shaped and remains the better arrangement — one cycle per invocation,
with the platform owning the restart policy. It is not what runs today, because a cron on Railway
is a *separate service* and a Railway volume attaches to exactly one service. The captured card
PNGs live on the API's volume (`ASSET_BUCKET=/data/cards`), so a cron container cannot read the
bytes it would publish. Object storage removes that constraint; until it exists, the process that
already has the volume mounted is the one that can publish, and scheduled posts firing is worth
more than the cleaner topology.

So this is deliberately temporary. When `ASSET_BUCKET` becomes a bucket rather than a path, move
to a cron service and delete this module — `publisher.run_once` is unchanged either way, which is
the point of it taking its schedule from the database rather than from an argument.

**Only one publisher may run at a time.** Not because Railway runs more than one replica today,
but because "today" is a deployment setting and double-publishing is not recoverable — the Page
gets two photos and the audience gets two notifications. A Postgres session-level advisory lock
makes the fleet size irrelevant: whoever takes the lock runs the cycle, everyone else skips it and
tries again next interval. The lock is held on a dedicated connection because the orchestrator
commits per post, and a pooled connection that has committed may not be the one that comes back.
"""

import asyncio
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from zlib import crc32

from sqlalchemy import Engine, text

from brandcortex.config import get_settings
from brandcortex.db.session import get_engine, session_scope
from brandcortex.workers import publisher

logger = logging.getLogger(__name__)

#: Advisory lock key. Any stable integer works; deriving it from a name means a future second loop
#: (insights, ingest) picks a different one without anybody maintaining a registry of magic numbers.
LOCK_KEY = crc32(b"brandcortex.workers.publisher")


@contextmanager
def fleet_lock(engine: Engine) -> Iterator[bool]:
    """Yield whether this process may run a publish cycle.

    Postgres only. Other dialects yield True: SQLite is the test database, where the fleet is one
    process by construction and a lock would test nothing but itself.
    """
    if engine.dialect.name != "postgresql":
        yield True
        return

    connection = engine.connect()
    acquired = False
    try:
        claim = connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_KEY}
        )
        acquired = bool(claim.scalar())
        yield acquired
    finally:
        if acquired:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
        connection.close()


def cycle() -> dict[str, int] | None:
    """One publish cycle, or None if another instance is already running one."""
    engine = get_engine()
    with fleet_lock(engine) as mine:
        if not mine:
            logger.debug("publish cycle skipped: another instance holds the lock")
            return None
        with session_scope() as session:
            return publisher.run_once(session=session)


async def run(interval: float) -> None:
    """Publish due posts every `interval` seconds until cancelled.

    Runs a cycle immediately rather than sleeping first: a deploy is exactly when a slot is most
    likely to have passed unattended, and a restart should catch up rather than add its own delay.

    The cycle is synchronous (SQLAlchemy, and a Graph call per post), so it goes to a thread. On
    the event loop it would block every request for the length of an upload.
    """
    while True:
        try:
            await asyncio.to_thread(cycle)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            # A cycle that fails must not end the loop. `run_once` already absorbs per-post
            # failures, so reaching here means the database or the adapter registry is unavailable
            # — conditions that come back on their own and should be retried next interval.
            logger.exception("publish cycle failed; retrying in %ss", interval)
        await asyncio.sleep(interval)


def start() -> asyncio.Task | None:
    """Start the loop if this deployment should publish, else explain why it did not.

    Silence is what made the missing worker hard to see: posts sat scheduled, nothing was wrong in
    any log, and the queue looked like the feature was broken rather than absent. Both branches
    log.
    """
    settings = get_settings()
    if not settings.publisher_enabled:
        logger.info(
            "publisher loop off (PUBLISHER_ENABLED unset and BRANDCORTEX_ENV=%s);"
            " scheduled posts will not fire in this process",
            settings.env,
        )
        return None
    interval = settings.publisher_interval_seconds
    logger.info("publisher loop on: checking for due posts every %ss", interval)
    return asyncio.create_task(run(interval), name="publisher-loop")
