"""Shared fixtures.

Tests never reach the Graph API or a brand's real database. Channel adapters are exercised against
fakes that satisfy the protocol; the seam is the whole point of the architecture, so it is also what
makes the system testable.

The database fixtures build in-memory SQLite straight from the models, not from the migration. That
is a deliberate trade: it keeps the suite fast and dependency-free, and it means these tests do
**not** prove the migration matches the models. `alembic check` is what proves that, and it is the
thing to run when a model changes.
"""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from brandcortex.db.base import Base
from brandcortex.db.models import Post  # noqa: F401 — registers every model on Base.metadata
from brandcortex.schemas.draft import PublishRequest, PublishResult


@pytest.fixture
def brand_config() -> dict:
    """Minimal brand config. Deliberately not ThaiSwim's real one — core tests must pass for any
    brand, and a test that only passes for ThaiSwim would hide a leaked assumption."""
    return {
        "brand": "testbrand",
        "timezone": "Asia/Bangkok",
        "default_locale": "th",
        "voice": {"max_emoji": 1, "banned_phrases": [], "forbidden_echoes": []},
        "intro_bank": {"th": ["intro-a", "intro-b", "intro-c"]},
        "hashtags": {"core": ["#Test"]},
        "unit_labels": {"metre": "ม."},
        "north_star": {"utm_sessions": 1.0, "shares": 0.5, "reactions": 0.0},
        "scheduling": {"min_spacing_hours": 6, "alternate_source_types": True},
    }


@pytest.fixture
def session() -> Iterator[Session]:
    """A session against a fresh in-memory database.

    `expire_on_commit=False` matches the application's factory. It also matters here: SQLite has no
    timezone-aware column type, so a datetime that survives a round trip comes back naive, and a test
    asserting on a local hour would then be asserting about the test runner's clock.

    `StaticPool` plus `check_same_thread=False` keep one connection — and therefore one in-memory
    database — shared across threads, which is what lets `TestClient` (it serves the app on its own
    thread) see rows the test just wrote.
    """
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with factory() as session:
        yield session
    engine.dispose()


class FakeChannelAdapter:
    """Implements `ChannelAdapter` structurally, in memory.

    Named after nothing real on purpose: a fake called "facebook" would be a channel assumption in
    the test suite, and the suite would then agree with it.
    """

    channel = "testchannel"

    def __init__(
        self,
        *,
        comment_id: str | None = "comment-1",
        error: Exception | None = None,
        published_at: datetime | None = None,
    ) -> None:
        self.comment_id = comment_id
        self.error = error
        self.published_at = published_at
        self.requests: list[PublishRequest] = []

    def publish(self, request: PublishRequest) -> PublishResult:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return PublishResult(
            channel_post_id="page_1_post_1",
            channel_comment_id=self.comment_id,
            published_at=self.published_at or datetime(2026, 8, 5, 13, 30, tzinfo=UTC),
        )

    def fetch_insights(self, channel_post_id: str):  # pragma: no cover - not exercised here
        raise NotImplementedError

    def health_check(self) -> bool:
        return True


@pytest.fixture
def fake_channel() -> FakeChannelAdapter:
    return FakeChannelAdapter()


@pytest.fixture
def fake_capture():
    """Stands in for `services.assets.capture`, the one network call the draft path makes."""
    captured: list[str] = []

    def capture(asset, *, post_id: str) -> str:
        captured.append(post_id)
        return f"cards/{post_id}.png"

    capture.captured = captured  # type: ignore[attr-defined]
    return capture
