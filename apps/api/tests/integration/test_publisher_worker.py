"""The worker that publishes scheduled posts, and the failures it has to survive.

Everything here is about what happens when a cycle goes wrong at three in the morning. The happy
path is one test; the rest are the reasons a human can still fix things afterwards.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from brandcortex.adapters.source.thaiswim import mapping
from brandcortex.adapters.source.thaiswim import templates as thaiswim_templates
from brandcortex.core import brand_config as brand_config_store
from brandcortex.core.generation import templates
from brandcortex.core.orchestrator import Orchestrator
from brandcortex.db.models import PostStatus
from brandcortex.workers import publisher
from tests.conftest import FakeChannelAdapter
from tests.integration.test_persistence_pipeline import SWIMMER_ROW

SEED = Path(__file__).resolve().parents[2] / "seeds" / "thaiswim.brand_config.json"
SITE = "https://thaiswim.com"
CHANNEL = FakeChannelAdapter.channel
SLOT = datetime(2026, 8, 6, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def registered_templates():
    templates.clear()
    thaiswim_templates.register(templates)
    yield
    templates.clear()


@pytest.fixture
def scheduled(session, fake_capture, fake_channel):
    brand_config_store.save(session, json.loads(SEED.read_text()))
    session.commit()

    driver = Orchestrator(
        session, capture=fake_capture, resolve_channel=lambda _c: fake_channel,
        now=lambda: SLOT - timedelta(days=1),
    )
    item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
    post = driver.schedule(driver.approve(driver.ingest(item, channel=CHANNEL).id).id, SLOT)
    return session, post, driver


def test_nothing_publishes_before_its_slot(scheduled) -> None:
    session, post, driver = scheduled
    counts = publisher.run_once(
        now=SLOT - timedelta(minutes=1), session=session, orchestrator=driver
    )
    assert counts["due"] == 0
    assert post.status is PostStatus.SCHEDULED


def test_a_due_post_publishes(scheduled) -> None:
    session, post, driver = scheduled
    counts = publisher.run_once(now=SLOT, session=session, orchestrator=driver)

    assert counts == {"due": 1, "published": 1, "failed": 0, "skipped_late": 0}
    assert post.status is PostStatus.PUBLISHED
    assert post.channel_post_id


def test_a_long_outage_does_not_dump_a_backlog_on_the_audience(scheduled) -> None:
    """A worker down since yesterday should not wake and publish yesterday's post into an audience
    that has moved on. Left scheduled, so a person picks the new moment."""
    session, post, driver = scheduled
    counts = publisher.run_once(
        now=SLOT + timedelta(hours=publisher.MAX_LATENESS_HOURS + 1),
        session=session,
        orchestrator=driver,
    )

    assert counts["skipped_late"] == 1
    assert counts["published"] == 0
    assert post.status is PostStatus.SCHEDULED, "still publishable once someone reschedules it"


def test_a_preflight_refusal_does_not_stop_the_cycle(scheduled) -> None:
    """The stale-link guard raises InvalidTransition before any channel I/O. A worker cycle must
    absorb that exactly like a channel failure — one bad post, not a dead cycle — while the post
    itself stays scheduled and visible for a person to fix."""
    session, post, driver = scheduled
    post.first_comment_text = "http://localhost:9000/swimmers/rin-suebsanguan"

    counts = publisher.run_once(now=SLOT, session=session, orchestrator=driver)

    assert counts["failed"] == 1
    assert post.status is PostStatus.SCHEDULED


def test_a_failure_leaves_the_post_recoverable(session, fake_capture) -> None:
    brand_config_store.save(session, json.loads(SEED.read_text()))
    session.commit()

    channel = FakeChannelAdapter(error=RuntimeError("graph: rate limited"))
    driver = Orchestrator(
        session, capture=fake_capture, resolve_channel=lambda _c: channel,
        now=lambda: SLOT - timedelta(days=1),
    )
    item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
    post = driver.schedule(driver.approve(driver.ingest(item, channel=CHANNEL).id).id, SLOT)

    counts = publisher.run_once(now=SLOT, session=session, orchestrator=driver)

    assert counts["failed"] == 1
    assert post.status is PostStatus.FAILED
    assert post.post_text and post.asset_storage_key, "everything needed to retry is still there"


def test_a_live_photo_with_no_comment_records_its_id(session, fake_capture) -> None:
    """The one failure the design exists to prevent, and the one that must stay findable: the card
    is on the Page, so its id has to be stored or nobody can fix or delete it."""
    brand_config_store.save(session, json.loads(SEED.read_text()))
    session.commit()

    class PhotoLiveCommentDead:
        channel = CHANNEL

        def publish(self, request):
            raise _CommentFailed("comment rejected", channel_post_id="live_post_42")

    from brandcortex.adapters.channel.facebook.adapter import CommentFailed as _CommentFailed

    driver = Orchestrator(
        session, capture=fake_capture, resolve_channel=lambda _c: PhotoLiveCommentDead(),
        now=lambda: SLOT - timedelta(days=1),
    )
    item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
    post = driver.schedule(driver.approve(driver.ingest(item, channel=CHANNEL).id).id, SLOT)

    publisher.run_once(now=SLOT, session=session, orchestrator=driver)

    assert post.status is PostStatus.FAILED
    assert post.channel_post_id == "live_post_42", "the photo is live; it must stay findable"
    assert "comment" in (post.error or "")
