"""End-to-end: a `card_renders` row becomes a finished, checked draft.

No database, no network, no Facebook. This is the core product path — brand row in, publishable Thai
copy out — and it runs offline so it can be trusted while the channel credentials are still being sorted
out.

Rows below are shaped exactly as `apps/admin/app/api/card-history/route.ts` writes them.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from brandcortex.adapters.source.thaiswim import mapping, templates as thaiswim_templates
from brandcortex.core.generation import templates
from brandcortex.core.generation.engine import DraftRejected, GenerationEngine

SEED = Path(__file__).resolve().parents[2] / "seeds" / "thaiswim.brand_config.json"
SITE = "https://thaiswim.com"


@pytest.fixture(autouse=True)
def registered_templates():
    """Register ThaiSwim's structures, and clear afterwards so brands can't leak between tests."""
    templates.clear()
    thaiswim_templates.register(templates)
    yield
    templates.clear()


@pytest.fixture
def config() -> dict:
    """The real seed file — if it drifts out of shape, these tests should be what says so."""
    return json.loads(SEED.read_text())


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
            {"stroke": "backstroke", "distance": 50, "course": "LCM", "rank": 1,
             "timeMs": 42060, "time": "42.06", "ageGroup": "55-59"},
        ],
    },
    "createdAt": datetime(2026, 8, 4, 9, 3, tzinfo=UTC),
}

EVENT_ROW = {
    "id": "clzq8x1v40001abcd5678ijkl",
    "kind": "event",
    "subject": "backstroke-50-F-55-59-LCM",
    "targetId": None,
    "label": "50m backstroke · F 55-59 LCM",
    "params": {"stroke": "backstroke", "distance": 50, "gender": "F",
               "ageGroup": "55-59", "course": "LCM", "n": 10},
    "snapshot": {
        "stroke": "backstroke", "distance": 50, "gender": "F", "ageGroup": "55-59",
        "course": "LCM", "n": 10, "rowCount": 8,
        "rows": [
            {"rank": 1, "timeMs": 42060, "time": "42.06", "name": "ริน สืบสงวน",
             "club": "สมาคมราชกรีฑาสโมสร", "province": "สุราษฎร์ธานี", "isRelayLeadoff": False},
            {"rank": 2, "timeMs": 44180, "time": "44.18", "name": "สุดา วงศ์ทอง",
             "club": None, "province": None, "isRelayLeadoff": False},
        ],
    },
    "createdAt": datetime(2026, 8, 4, 9, 5, tzinfo=UTC),
}


class TestSwimmerCard:
    def test_row_becomes_a_content_item(self) -> None:
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        assert item.content_id == SWIMMER_ROW["id"]
        assert item.source_type == "swimmer"
        assert item.locale == "th"
        assert str(item.canonical_link) == f"{SITE}/swimmers/rin-suebsanguan"
        assert str(item.asset.render_url) == f"{SITE}/api/card/swimmer?slug=rin-suebsanguan"
        assert (item.asset.width, item.asset.height) == (1080, 1350)
        assert item.wow_factor > 0.6, "nine national #1s across four strokes should score high"

    def test_produces_publishable_copy(self, config) -> None:
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        draft = GenerationEngine(config).draft(item, channel="facebook")

        assert "ริน สืบสงวน" in draft.post_text
        assert "9 รายการ" in draft.post_text
        assert "ครบ 4 ท่า" in draft.post_text
        assert "รุ่น 55–59" in draft.post_text
        assert "#ThaiSwim" in draft.post_text
        assert draft.intro_line in config["intro_bank"]["th"]
        assert draft.hook_style == "multi_gold"

    def test_province_reads_as_a_team_not_a_location(self, config) -> None:
        """The card shows "ทีม{province}" because it's a provincial team affiliation, not an address.
        The caption has to match, or the two disagree in the same post."""
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        assert "ทีมสุราษฎร์ธานี" in GenerationEngine(config).draft(item, channel="facebook").post_text

    def test_link_is_only_ever_in_the_first_comment(self, config) -> None:
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        draft = GenerationEngine(config).draft(item, channel="facebook")
        assert "http" not in draft.post_text
        assert f"{SITE}/swimmers/rin-suebsanguan" in draft.first_comment_text

    def test_utm_tagged_link_is_used_when_given(self, config) -> None:
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        tagged = f"{SITE}/swimmers/rin-suebsanguan?utm_source=facebook&utm_campaign=bc-a3f8e1"
        draft = GenerationEngine(config).draft(item, channel="facebook", link=tagged)
        assert tagged in draft.first_comment_text

    def test_intro_rotates_away_from_recent_lines(self, config) -> None:
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        bank = config["intro_bank"]["th"]
        draft = GenerationEngine(config).draft(
            item, channel="facebook", recent_intros=bank[:2]
        )
        assert draft.intro_line not in bank[:2]


class TestEventCard:
    def test_row_becomes_a_content_item(self) -> None:
        item = mapping.row_to_content_item(EVENT_ROW, site_url=SITE)
        assert str(item.canonical_link) == (
            f"{SITE}/rankings?stroke=backstroke&dist=50&gender=F&age=55-59&course=LCM"
        )
        assert item.asset.height is None, "event card height is variable — must not be guessed"
        assert item.facts["season"] == "2025-2026", "derived, since the snapshot has no season"

    def test_states_rows_shown_not_rows_requested(self, config) -> None:
        """The bucket returned 8 of the 10 requested. Saying "10" would be a claim the card refutes —
        the exact case the numeric check exists for."""
        item = mapping.row_to_content_item(EVENT_ROW, site_url=SITE)
        draft = GenerationEngine(config).draft(item, channel="facebook")
        assert "8 อันดับแรก" in draft.post_text
        assert "10 อันดับ" not in draft.post_text

    def test_uses_thai_stroke_names_and_the_configured_unit(self, config) -> None:
        item = mapping.row_to_content_item(EVENT_ROW, site_url=SITE)
        draft = GenerationEngine(config).draft(item, channel="facebook")
        assert "กรรเชียง 50 ม." in draft.post_text
        assert "หญิง" in draft.post_text and "สระ 50 ม." in draft.post_text

    def test_asks_the_reader_about_their_own_rank(self, config) -> None:
        """The card already lists the leaders, so there is nothing to tease — the hook turns outward."""
        item = mapping.row_to_content_item(EVENT_ROW, site_url=SITE)
        draft = GenerationEngine(config).draft(item, channel="facebook")
        assert "เวลาของคุณอยู่อันดับไหน?" in draft.post_text
        assert draft.hook_style == "personal_rank_question"

    def test_no_intro_line_on_event_posts(self, config) -> None:
        item = mapping.row_to_content_item(EVENT_ROW, site_url=SITE)
        assert GenerationEngine(config).draft(item, channel="facebook").intro_line is None


class TestHardConstraints:
    def test_ungrounded_number_is_rejected_not_repaired(self, config) -> None:
        """A template that invents a figure must fail loudly. Silently fixing it would hide that the
        engine fabricated something."""
        def bad(*, facts, intro, config):
            return "อันดับ 1 ของประเทศ 12 รายการ", "", "bad"

        templates.register("swimmer", "th", bad)
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        with pytest.raises(DraftRejected) as exc:
            GenerationEngine(config).draft(item, channel="facebook")
        assert "12" in str(exc.value)

    def test_link_in_caption_is_rejected(self, config) -> None:
        def bad(*, facts, intro, config):
            return f"ดูสถิติได้ที่ {SITE}/swimmers/x", "", "bad"

        templates.register("swimmer", "th", bad)
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        with pytest.raises(DraftRejected) as exc:
            GenerationEngine(config).draft(item, channel="facebook")
        assert "first comment" in str(exc.value)

    def test_stacked_emoji_is_rejected(self, config) -> None:
        def bad(*, facts, intro, config):
            return "อันดับ 1 ของประเทศ 🔥🔥🔥", "", "bad"

        templates.register("swimmer", "th", bad)
        item = mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE)
        with pytest.raises(DraftRejected):
            GenerationEngine(config).draft(item, channel="facebook")

    def test_unregistered_locale_fails_rather_than_guessing(self, config) -> None:
        """Rendering the wrong language reaches the audience looking deliberate."""
        item = mapping.row_to_content_item({**SWIMMER_ROW, "params": {**SWIMMER_ROW["params"], "lang": "fr"}}, site_url=SITE)
        cfg = {**config, "default_locale": "fr"}
        with pytest.raises(LookupError):
            GenerationEngine(cfg).draft(item, channel="facebook")
