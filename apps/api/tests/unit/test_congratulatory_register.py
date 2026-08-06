"""The congratulatory register (spec §6.2).

Two registers are in use and the reviewer picks between them: the reporting angles state the fact and
leave it alone, and these two congratulate. The warm shape is the owner's own, copied from a post
they wrote by hand, so these tests pin its structure rather than its prose — the wording is theirs to
change, the shape is what makes generated posts sit beside hand-written ones without a seam.

The emoji ceiling was raised from one to two to admit it — 🏆 on the headline, 👏 on the achievement,
and nothing on the nudge. That is the only voice rule this register relaxes, and this file exists
partly to make it obvious if a third creeps into a caption that isn't paying for it.
"""

import json
from pathlib import Path

import pytest

from brandcortex.adapters.source.thaiswim import templates
from brandcortex.core.generation import claims, voice

CONFIG_PATH = Path(__file__).resolve().parents[2] / "seeds" / "thaiswim.brand_config.json"

WARM_ANGLES = ("sweep", "club")

FACTS = {
    "name": "ดวง คงเจริญ",
    "club": "สโมสรกีฬาทางน้ำสระจุฬาภรณ์ Chulabhorn Aquatic Club",
    "province": "กรุงเทพมหานคร",
    "ageGroups": ["80-84"],
    "goldCount": 10,
    "goldStrokes": 4,
    "rankedCount": 12,
    "rows": [{"stroke": "freestyle", "distance": 50, "course": "LCM", "rank": 1, "time": "45.10"}],
}


@pytest.fixture(scope="module")
def config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _render(angle: str, config: dict) -> tuple[str, str]:
    renderer = dict(templates.SWIMMER_ANGLES_TH)[angle]
    caption, comment, _hook = renderer(facts=FACTS, intro="อีกหนึ่งชื่อ", config=config)
    return caption, comment


def test_sweep_shape(config: dict) -> None:
    """The owner's own five-line shape: headline -> congratulation -> achievement -> nudge -> tags."""
    caption, _ = _render("sweep", config)
    lines = caption.split("\n")
    assert len(lines) == 5
    assert lines[0].startswith("🏆")
    assert lines[1].startswith("ขอแสดงความยินดีกับ คุณ")
    assert lines[2].endswith("👏")
    assert lines[3] == "ดูสถิติและโปรไฟล์ทั้งหมดได้จากลิงก์ในคอมเมนต์แรก"
    assert lines[4].startswith("#")


def test_club_shape(config: dict) -> None:
    """Four lines, and the club is named before the swimmer — the whole point of the angle."""
    caption, _ = _render("club", config)
    lines = caption.split("\n")
    assert len(lines) == 4
    assert lines[0].startswith("🏆") and FACTS["club"] in lines[0]
    assert lines[1].startswith("ขอแสดงความยินดีกับ คุณ") and lines[1].endswith("👏")
    assert lines[3].startswith("#")


def test_the_two_warm_angles_are_not_the_same_post(config: dict) -> None:
    """`longevity` used to be a second trophy-headline congratulation, which made it `sweep` with
    different words. The reviewer is meant to be choosing between shapes, not paraphrases."""
    sweep, _ = _render("sweep", config)
    club, _ = _render("club", config)
    assert sweep.split("\n")[0] != club.split("\n")[0]
    assert len(sweep.split("\n")) != len(club.split("\n"))


@pytest.mark.parametrize("angle", WARM_ANGLES)
def test_stays_inside_the_raised_emoji_ceiling(angle: str, config: dict) -> None:
    """Two, and the ceiling is two. A third means the register is drifting into decoration."""
    caption, _ = _render(angle, config)
    assert voice.check(caption, voice.load_rules(config)).ok
    assert sum(caption.count(e) for e in ("🏆", "👏")) == 2


@pytest.mark.parametrize("angle", WARM_ANGLES)
def test_numbers_are_still_grounded(angle: str, config: dict) -> None:
    """Warmth changes the register, not the rule that every figure comes off the card."""
    caption, _ = _render(angle, config)
    assert claims.check(caption, FACTS, notation=("สระ 50 ม.", "สระ 25 ม.")).ok


@pytest.mark.parametrize("angle", WARM_ANGLES)
def test_first_comment_matches_the_caption_register(angle: str, config: dict) -> None:
    """A warm caption over a flat first comment reads as two people writing one post."""
    _, comment = _render(angle, config)
    assert comment in [
        line.format(person=templates._person(FACTS, config)) for line in templates.COMMENTS_WARM_TH
    ]


@pytest.mark.parametrize("angle", WARM_ANGLES)
def test_ignores_the_dealt_intro(angle: str, config: dict) -> None:
    """These open on the achievement. The engine records `intro_line` only when the caption used it,
    so an unused line is not retired from the rotation without a reader ever seeing it."""
    caption, _ = _render(angle, config)
    assert "อีกหนึ่งชื่อ" not in caption


def test_reporting_angles_stayed_plain(config: dict) -> None:
    """The point of raising the ceiling was one register, not all of them."""
    for angle in ("plain", "breadth", "standout", "longevity"):
        caption, _ = _render(angle, config)
        assert "🏆" not in caption and "👏" not in caption
