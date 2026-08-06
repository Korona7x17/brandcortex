"""The honorific rule: a person's name is never written bare (spec §6.1, §6.6).

This is a voice rule with a sharper edge than the others. An extra emoji is a lapse of taste; a
masters swimmer's name printed without คุณ is a public discourtesy to a real person, in front of the
audience most likely to know them. So it is enforced the same way the numeric grounding is — after
generation, on the caption *and* on the first comment, rather than trusted to a prompt.

The mechanism is brand-agnostic: the prefix, the locales it applies to and the `facts` keys that hold
a name all come from `brand_config.voice.honorific`. These tests use ThaiSwim's settings because that
is the brand that has the convention, not because the core knows about it.
"""

import json
from pathlib import Path

import pytest

from brandcortex.adapters.source.thaiswim import templates
from brandcortex.core.generation import voice

CONFIG_PATH = Path(__file__).resolve().parents[2] / "seeds" / "thaiswim.brand_config.json"

NAME = "ไกรศรี บุตรวงษ์"

FACTS = {
    "name": NAME,
    "romanized": "Kraisri Butrawong",
    "club": "สมาคมราชกรีฑาสโมสร",
    "province": "สุราษฎร์ธานี",
    "ageGroups": ["55-59"],
    "goldCount": 9,
    "goldStrokes": 4,
    "rankedCount": 11,
    "rows": [{"stroke": "freestyle", "distance": 50, "course": "LCM", "rank": 1, "time": "31.24"}],
}


@pytest.fixture(scope="module")
def config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rules(config: dict) -> voice.VoiceRules:
    return voice.load_rules(config)


def test_seed_config_declares_the_honorific(rules: voice.VoiceRules) -> None:
    """Without this block the rule silently does nothing, which is the failure mode worth pinning."""
    assert rules.honorific is not None
    assert rules.honorific.prefix == "คุณ"
    assert "th" in rules.honorific.locales


def test_rejects_a_bare_name(rules: voice.VoiceRules) -> None:
    result = voice.check(
        f"{NAME} · สโมสร\n\nอันดับ 1 ของประเทศ", rules, names=(NAME,), locale="th"
    )
    assert [v.rule for v in result.violations] == ["honorific"]


def test_accepts_the_prefixed_name(rules: voice.VoiceRules) -> None:
    result = voice.check(
        f"คุณ{NAME} · สโมสร\n\nอันดับ 1 ของประเทศ", rules, names=(NAME,), locale="th"
    )
    assert result.ok


def test_a_second_bare_mention_is_still_caught(rules: voice.VoiceRules) -> None:
    """One polite mention does not license the rest. Prefixed mentions are removed before looking."""
    result = voice.check(f"คุณ{NAME} ... {NAME}", rules, names=(NAME,), locale="th")
    assert [v.rule for v in result.violations] == ["honorific"]


def test_rule_is_scoped_to_the_declared_locales(rules: voice.VoiceRules) -> None:
    """English copy carries no คุณ; scoping is what keeps the rule from being wrong in the other half
    of a bilingual brand."""
    assert voice.check(f"{NAME} holds nine national titles", rules, names=(NAME,), locale="en").ok


def test_first_comment_is_held_to_the_rule_and_nothing_else(rules: voice.VoiceRules) -> None:
    """`check_names` exists because the first comment is the one place a link belongs — the caption
    rules would reject it for the very thing it is for."""
    assert not voice.check_names(f"📊 สถิติทั้งหมดของ{NAME}", rules, names=(NAME,), locale="th").ok
    assert voice.check_names(
        f"📊 สถิติทั้งหมดของคุณ{NAME} อยู่ที่นี่", rules, names=(NAME,), locale="th"
    ).ok


def test_names_in_reads_the_declared_fields(rules: voice.VoiceRules) -> None:
    assert voice.names_in(FACTS, rules) == (NAME,)
    assert voice.names_in({}, rules) == ()


@pytest.mark.parametrize("angle", [a for a, _ in templates.SWIMMER_ANGLES_TH])
def test_every_swimmer_angle_passes_the_rule(angle: str, config: dict, rules: voice.VoiceRules) -> None:
    """Caption and first comment both. The templates are meant to pass by construction — a variant
    that only passes because the validator was never pointed at it is the bug this catches."""
    renderer = dict(templates.SWIMMER_ANGLES_TH)[angle]
    caption, comment, _hook = renderer(facts=FACTS, intro="อีกหนึ่งชื่อ", config=config)
    names = voice.names_in(FACTS, rules)
    assert voice.check(caption, rules, names=names, locale="th").ok
    assert voice.check_names(comment, rules, names=names, locale="th").ok


def test_first_comment_falls_back_to_a_general_line_without_a_name(config: dict) -> None:
    """A card with no name gets a line that needs none, never a lone honorific or a placeholder."""
    line = templates._swimmer_comment({}, config, index=0)
    assert "{person}" not in line
    assert "คุณ" not in line
