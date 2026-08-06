"""A card becomes a persisted draft, survives review, and publishes.

`test_thaiswim_pipeline.py` proves a `card_renders` row turns into checked Thai copy. This file picks
up where that stops: the copy has to land in a database, be visible to a reviewer, keep the engine's
original next to any human edit, and record enough about itself that the learning loop has history
from post #1.

No network and no Postgres. The two seams that would need one — capturing the card and talking to a
channel — are injected, which is what the seams are for.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from brandcortex.adapters.source.thaiswim import mapping
from brandcortex.adapters.source.thaiswim import templates as thaiswim_templates
from brandcortex.core import brand_config as brand_config_store
from brandcortex.core.analytics import utm
from brandcortex.core.generation import templates
from brandcortex.core.orchestrator import (
    EditRejected,
    InvalidTransition,
    Orchestrator,
    PublishFailed,
)
from brandcortex.db.models import IntroHistory, PostStatus
from tests.conftest import FakeChannelAdapter

SEED = Path(__file__).resolve().parents[2] / "seeds" / "thaiswim.brand_config.json"
SITE = "https://thaiswim.com"
CHANNEL = FakeChannelAdapter.channel

SWIMMER_ROW = {
    "id": "clzq8x1v40000abcd1234efgh",
    "kind": "swimmer",
    "subject": "rin-suebsanguan",
    "targetId": "clsw0001",
    "label": "ริน สืบสงวน",
    "params": {"slug": "rin-suebsanguan", "id": "clsw0001"},
    "snapshot": {
        "name": "ริน สืบสงวน",
        "romanized": "Rin Suebsanguan",
        "club": "สมาคมราชกรีฑาสโมสร",
        "province": "สุราษฎร์ธานี",
        "ageGroups": ["55-59"],
        "goldCount": 9,
        "goldStrokes": 4,
        "multiGold": True,
        "rankedCount": 9,
        "topRank": 1,
        "rows": [
            {
                "stroke": "backstroke",
                "distance": 50,
                "course": "LCM",
                "rank": 1,
                "timeMs": 42060,
                "time": "42.06",
                "ageGroup": "55-59",
            },
        ],
    },
    "createdAt": datetime(2026, 8, 4, 9, 3, tzinfo=UTC),
}


@pytest.fixture(autouse=True)
def registered_templates():
    templates.clear()
    thaiswim_templates.register(templates)
    yield
    templates.clear()


@pytest.fixture
def configured(session):
    """A database with ThaiSwim's real config loaded — the document that ships in `seeds/`."""
    brand_config_store.save(session, json.loads(SEED.read_text()))
    session.commit()
    return session


@pytest.fixture
def item():
    return mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)


@pytest.fixture
def orchestrator(configured, fake_capture, fake_channel):
    return Orchestrator(
        configured,
        capture=fake_capture,
        resolve_channel=lambda channel: fake_channel,
        now=lambda: datetime(2026, 8, 5, 12, 0, tzinfo=UTC),
    )


class TestIngest:
    def test_draft_is_persisted_with_everything_review_needs(self, orchestrator, item):
        post = orchestrator.ingest(item, channel=CHANNEL)

        assert post.status is PostStatus.DRAFT
        assert post.content_id == SWIMMER_ROW["id"]
        assert "ริน สืบสงวน" in post.post_text
        assert post.asset_storage_key == f"cards/{post.id}.png"
        assert post.source_generated_at == SWIMMER_ROW["createdAt"]
        assert post.facts["goldCount"] == 9, "the card's own numbers, frozen beside the caption"

    def test_the_engines_original_is_kept_beside_the_editable_text(self, orchestrator, item):
        post = orchestrator.ingest(item, channel=CHANNEL)
        assert post.generated_post_text == post.post_text
        assert post.generated_first_comment_text == post.first_comment_text

    def test_features_are_captured_from_the_first_post(self, orchestrator, item):
        """Not for anything Phase 1 does with them. They cannot be reconstructed later, so a post
        drafted without them is permanently invisible to the learning loop."""
        features = orchestrator.ingest(item, channel=CHANNEL).features

        assert features.source_type == "swimmer"
        assert features.locale == "th"
        assert features.hook_style == "multi_gold"
        assert features.caption_length > 0
        assert float(features.wow_factor) > 0.6
        assert features.dimensions["goldStrokes"] == 4
        assert "rows" not in features.dimensions, "the card's table is not a grouping key"

    def test_timing_features_stay_empty_until_the_post_goes_out(self, orchestrator, item):
        """Draft time is a fact about the operator's afternoon, not about the audience."""
        features = orchestrator.ingest(item, channel=CHANNEL).features
        assert features.post_hour is None
        assert features.post_weekday is None

    def test_link_is_tagged_and_lives_only_in_the_first_comment(self, orchestrator, item):
        post = orchestrator.ingest(item, channel=CHANNEL)

        assert post.utm_campaign is not None
        assert post.utm_campaign.startswith("swimmer-")
        assert post.utm_campaign in post.first_comment_text
        assert "http" not in post.post_text

    def test_intro_is_recorded_so_the_next_post_rotates_away(self, orchestrator, item, configured):
        post = orchestrator.ingest(item, channel=CHANNEL)
        history = configured.scalars(
            select(IntroHistory).order_by(IntroHistory.used_at.desc())
        ).all()

        assert [row.intro_line for row in history] == [post.features.intro_line]

    def test_redelivery_returns_the_same_post(self, orchestrator, item):
        first = orchestrator.ingest(item, channel=CHANNEL)
        second = orchestrator.ingest(item, channel=CHANNEL)
        assert first.id == second.id

    def test_a_rejected_draft_is_persisted_as_failed_with_its_reasons(self, orchestrator, item):
        """One bad card must not stop the other forty, and it must not vanish either. The reviewer
        sees why it failed; nothing was repaired."""

        def invents_a_number(*, facts, intro, config):
            return "อันดับ 1 ของประเทศ 12 รายการ", "", "bad"

        templates.register("swimmer", "th", invents_a_number)
        post = orchestrator.ingest(item, channel=CHANNEL)

        assert post.status is PostStatus.FAILED
        assert "12" in post.error
        assert post.post_text is None

    def test_capture_failure_fails_the_post_rather_than_shipping_no_image(
        self, configured, item, fake_channel
    ):
        def unreachable(asset, *, post_id):
            raise RuntimeError("connection refused")

        orchestrator = Orchestrator(
            configured, capture=unreachable, resolve_channel=lambda c: fake_channel
        )
        post = orchestrator.ingest(item, channel=CHANNEL)

        assert post.status is PostStatus.FAILED
        assert "card capture failed" in post.error


class TestReview:
    def test_an_edit_keeps_the_original_and_marks_the_post_edited(self, orchestrator, item):
        post = orchestrator.ingest(item, channel=CHANNEL)
        original = post.post_text

        edited = orchestrator.edit(post.id, post_text=original + " ครับ")

        assert edited.post_text != edited.generated_post_text
        assert edited.generated_post_text == original
        assert edited.features.caption_length == len(edited.post_text)

    def test_a_reviewer_cannot_add_a_number_the_card_does_not_show(self, orchestrator, item):
        """The check does not care who typed it. A caption asserting more than the image shows is a
        claim about a real person that the reader can refute from the same post."""
        post = orchestrator.ingest(item, channel=CHANNEL)

        with pytest.raises(EditRejected) as exc:
            orchestrator.edit(post.id, post_text=post.post_text + " ทำลายสถิติ 17 รายการ")

        assert "17" in str(exc.value)

    def test_a_reviewer_cannot_move_the_link_into_the_caption(self, orchestrator, item):
        post = orchestrator.ingest(item, channel=CHANNEL)

        with pytest.raises(EditRejected):
            orchestrator.edit(post.id, post_text=f"{post.post_text} {SITE}/swimmers/x")

    def test_dropping_the_tagged_link_from_the_comment_is_rejected(self, orchestrator, item):
        """Without the campaign the post still publishes and still draws traffic — invisibly. That
        is worse than a broken link: the north star reads it as a post nobody clicked."""
        post = orchestrator.ingest(item, channel=CHANNEL)

        with pytest.raises(EditRejected) as exc:
            orchestrator.edit(post.id, first_comment_text=f"{SITE}/swimmers/rin-suebsanguan")

        assert "north star" in str(exc.value)

    def test_editing_a_failed_draft_returns_it_to_the_queue(self, orchestrator, item):
        def invents_a_number(*, facts, intro, config):
            return "อันดับ 1 ของประเทศ 12 รายการ", "", "bad"

        templates.register("swimmer", "th", invents_a_number)
        post = orchestrator.ingest(item, channel=CHANNEL)
        assert post.status is PostStatus.FAILED

        fixed = orchestrator.edit(post.id, post_text="อันดับ 1 ของประเทศ 9 รายการ")

        assert fixed.status is PostStatus.DRAFT
        assert fixed.error is None

    def test_approval_is_required_before_publishing(self, orchestrator, item):
        post = orchestrator.ingest(item, channel=CHANNEL)
        with pytest.raises(InvalidTransition):
            orchestrator.publish(post.id)

    def test_approving_with_an_edit_still_runs_every_check(self, orchestrator, item):
        """Otherwise the approve path is how every check in the file gets bypassed."""
        post = orchestrator.ingest(item, channel=CHANNEL)

        with pytest.raises(EditRejected):
            orchestrator.approve(post.id, edited_text=post.post_text + " 44 เหรียญ")

        assert orchestrator.approve(post.id).status is PostStatus.APPROVED


class TestPublish:
    def test_publishing_records_both_channel_ids(self, orchestrator, item, fake_channel):
        post = orchestrator.approve(orchestrator.ingest(item, channel=CHANNEL).id)
        published = orchestrator.publish(post.id)

        assert published.status is PostStatus.PUBLISHED
        assert published.channel_post_id == "page_1_post_1"
        assert published.channel_comment_id == "comment-1"
        assert fake_channel.requests[0].asset_storage_key == post.asset_storage_key

    def test_timing_features_use_the_audiences_clock_not_utc(self, orchestrator, item):
        """13:30 UTC is 20:30 in Bangkok. A learned "best hour" rule reads this column, so storing
        13 would make every timing rule wrong by a fixed offset."""
        post = orchestrator.approve(orchestrator.ingest(item, channel=CHANNEL).id)
        published = orchestrator.publish(post.id)

        assert published.features.post_hour == 20
        assert published.features.post_weekday == 2  # Wednesday 2026-08-05

    def test_a_post_whose_link_comment_did_not_land_is_a_failure(
        self, configured, item, fake_capture
    ):
        """The link is the entire reason the post exists. Reporting success here would file a
        delivery failure away as a content one."""
        channel = FakeChannelAdapter(comment_id=None)
        orchestrator = Orchestrator(
            configured, capture=fake_capture, resolve_channel=lambda c: channel
        )
        post = orchestrator.approve(orchestrator.ingest(item, channel=CHANNEL).id)

        with pytest.raises(PublishFailed):
            orchestrator.publish(post.id)

        assert post.status is PostStatus.FAILED
        assert "link is missing from a live post" in post.error

    def test_a_channel_error_leaves_the_post_failed_and_recoverable(
        self, configured, item, fake_capture
    ):
        channel = FakeChannelAdapter(error=RuntimeError("graph: rate limited"))
        orchestrator = Orchestrator(
            configured, capture=fake_capture, resolve_channel=lambda c: channel
        )
        post = orchestrator.approve(orchestrator.ingest(item, channel=CHANNEL).id)

        with pytest.raises(PublishFailed):
            orchestrator.publish(post.id)

        assert post.status is PostStatus.FAILED
        assert "rate limited" in post.error
        assert post.post_text and post.asset_storage_key, "everything needed to retry is still here"

    def test_links_baked_against_another_environment_refuse_to_publish(
        self, orchestrator, item, fake_channel
    ):
        """Links are derived from BRAND_SITE_URL at draft time and never re-derived, so a draft
        composed against a dev server keeps its dev links forever. The first live post shipped
        `localhost:9000` in its comment this way; the check exists so the failure repeats as a
        refusal in the queue, not as a dead link on the Page."""
        post = orchestrator.approve(orchestrator.ingest(item, channel=CHANNEL).id)
        post.first_comment_text = "http://localhost:9000/swimmers/rin-suebsanguan?utm_source=x"
        post.canonical_link = "http://localhost:9000/swimmers/rin-suebsanguan"

        with pytest.raises(InvalidTransition, match="localhost:9000"):
            orchestrator.publish(post.id)

        assert not fake_channel.requests, "the refusal must come before any channel I/O"

    def test_publishing_twice_does_not_post_twice(self, orchestrator, item, fake_channel):
        post = orchestrator.approve(orchestrator.ingest(item, channel=CHANNEL).id)
        orchestrator.publish(post.id)
        orchestrator.publish(post.id)

        assert len(fake_channel.requests) == 1


class TestCampaign:
    def test_a_campaign_is_stable_across_retagging(self):
        post_id = "4f8a2c1d-0000-4000-8000-000000000000"
        first = utm.tag_link(
            f"{SITE}/swimmers/x", brand="b", channel="c", post_id=post_id, source_type="swimmer"
        )
        again = utm.tag_link(first, brand="b", channel="c", post_id=post_id, source_type="swimmer")

        assert first == again
        assert utm.campaign_of(first) == "swimmer-4f8a2c1d"

    def test_an_existing_query_string_survives_tagging(self):
        """Event links carry the whole ranking bucket in their query. Dropping it would point the
        reader at a different board than the card shows."""
        url = f"{SITE}/rankings?stroke=backstroke&dist=50"
        tagged = utm.tag_link(
            url, brand="b", channel="c", post_id="4f8a2c1d" + "0" * 24, source_type="event"
        )

        assert "stroke=backstroke" in tagged
        assert "dist=50" in tagged
