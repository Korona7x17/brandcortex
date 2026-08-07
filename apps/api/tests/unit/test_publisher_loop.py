"""The in-process publisher loop: when it runs, when it refuses to, and what kills it.

The loop exists because a Railway cron cannot reach the card volume, so it is temporary by design.
What is not temporary is the pair of guarantees it has to hold while it does run: exactly one
publisher across the fleet, and a cycle failure that does not end the loop. Both are here.

The publishing itself is `publisher.run_once`, tested against a fake Graph in
`tests/integration/test_publisher_worker.py`. Nothing below reaches a channel.
"""

import asyncio

import pytest
from sqlalchemy import create_engine

from brandcortex.config import get_settings
from brandcortex.workers import publisher_loop


@pytest.fixture(autouse=True)
def clean_settings(monkeypatch):
    """Each test states its own publisher env; required-but-irrelevant settings get placeholders.

    Pinned rather than merely unset — the developer's own .env is read from the working directory
    and legitimately carries these, and only a process env var outranks it.
    """
    monkeypatch.delenv("PUBLISHER_ENABLED", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("ASSET_BUCKET", "/tmp/test-assets")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "unused")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --- when it is on -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("env", "override", "expected"),
    [
        # Unset follows the environment: a deployment publishes, a laptop does not. Neither is safe
        # as a constant — the laptop would post to a live Page, the deployment would post nothing.
        ("local", None, False),
        ("staging", None, True),
        ("production", None, True),
        # An explicit setting outranks the environment in both directions: staging needs to be able
        # to hold its posts, and a developer testing the loop needs to be able to turn it on.
        ("production", "false", False),
        ("local", "true", True),
    ],
)
def test_publishing_follows_the_environment_unless_stated(
    monkeypatch, env, override, expected
) -> None:
    monkeypatch.setenv("BRANDCORTEX_ENV", env)
    if override is not None:
        monkeypatch.setenv("PUBLISHER_ENABLED", override)
    get_settings.cache_clear()

    assert get_settings().publisher_enabled is expected


def test_a_disabled_loop_says_so(monkeypatch, caplog) -> None:
    """Silence is what made the missing worker hard to see — posts sat scheduled and no log said
    why. Off is a state worth announcing, not the absence of one."""
    monkeypatch.setenv("BRANDCORTEX_ENV", "local")
    get_settings.cache_clear()

    with caplog.at_level("INFO"):
        assert publisher_loop.start() is None
    assert "publisher loop off" in caplog.text


# --- one publisher at a time ---------------------------------------------------------------------


def test_sqlite_has_no_fleet_to_lock_against() -> None:
    """SQLite is the test database, where the fleet is one process by construction."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with publisher_loop.fleet_lock(engine) as mine:
        assert mine is True


def test_a_cycle_is_skipped_when_another_instance_holds_the_lock(monkeypatch) -> None:
    """Double-publishing is not recoverable: the Page gets two photos and the audience gets two
    notifications. A loser skips its turn rather than waiting for one."""
    ran = []
    monkeypatch.setattr(publisher_loop.publisher, "run_once", lambda **_: ran.append(1))
    monkeypatch.setattr(publisher_loop, "fleet_lock", _lock_yielding(False))

    assert publisher_loop.cycle() is None
    assert ran == []


def test_the_winner_runs_the_cycle(monkeypatch) -> None:
    monkeypatch.setattr(publisher_loop.publisher, "run_once", lambda **_: {"published": 1})
    monkeypatch.setattr(publisher_loop, "fleet_lock", _lock_yielding(True))

    assert publisher_loop.cycle() == {"published": 1}


def _lock_yielding(acquired: bool):
    from contextlib import contextmanager

    @contextmanager
    def fake(_engine):
        yield acquired

    return fake


# --- the loop itself -----------------------------------------------------------------------------


async def _run_cycles(monkeypatch, cycle, *, count: int) -> None:
    """Run the loop until `cycle` has been called `count` times, then cancel it."""
    done = asyncio.Event()
    calls = []

    def counted():
        calls.append(1)
        if len(calls) >= count:
            done.set()
        return cycle()

    monkeypatch.setattr(publisher_loop, "cycle", counted)
    task = asyncio.create_task(publisher_loop.run(0))
    try:
        await asyncio.wait_for(done.wait(), timeout=5)
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_the_loop_keeps_cycling(monkeypatch) -> None:
    await _run_cycles(monkeypatch, lambda: {"due": 0}, count=3)


async def test_a_failed_cycle_does_not_end_the_loop(monkeypatch, caplog) -> None:
    """`run_once` already absorbs per-post failures, so reaching the loop's handler means the
    database or the registry is unavailable — conditions that come back on their own. A worker that
    died on the first of them would stop publishing silently until someone redeployed."""

    def explode():
        raise RuntimeError("database is away")

    with caplog.at_level("ERROR"):
        await _run_cycles(monkeypatch, explode, count=2)
    assert "publish cycle failed" in caplog.text


async def test_cancelling_stops_the_loop(monkeypatch) -> None:
    """Shutdown must not be swallowed by the same handler that survives a database blip."""
    monkeypatch.setattr(publisher_loop, "cycle", lambda: {"due": 0})
    task = asyncio.create_task(publisher_loop.run(0))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
