"""ThaiSwim post structures, in Thai (spec §6.2, §6.3).

These live with the adapter, not in `core/`, because they are this brand's writing. The core owns the
registry and the constraints; the brand owns the words. Brand #2 registers its own and touches nothing
here.

Two rules shape every line below:

* **No number appears that isn't in `facts`.** `claims.check` enforces it, and these templates are
  written to pass by construction — every figure is read from the snapshot rather than counted, phrased
  or rounded in the copy.
* **The link never appears in the caption.** It goes in the first comment, which is a separate return
  value, not a formatting choice.

The event hook works because the card already lists the top names. There is nothing to withhold, so the
copy asks readers about *their own* rank rather than teasing what the image has already shown them.
"""

from typing import Any

STROKE_TH: dict[str, str] = {
    "freestyle": "ฟรีสไตล์",
    "backstroke": "กรรเชียง",
    "breaststroke": "กบ",
    "butterfly": "ผีเสื้อ",
    "im": "เดี่ยวผสม",
    "medley": "ผสม",
}
GENDER_TH: dict[str, str] = {"M": "ชาย", "F": "หญิง"}
COURSE_TH: dict[str, str] = {"LCM": "สระ 50 ม.", "SCM": "สระ 25 ม."}

#: En dash for ranges, matching how the cards render age groups ("55–59").
def _age(group: str) -> str:
    return str(group).replace("-", "–")


def _hashtags(config: dict[str, Any]) -> str:
    return " ".join(config.get("hashtags", {}).get("core", []))


def swimmer_th(*, facts: dict[str, Any], intro: str, config: dict[str, Any]) -> tuple[str, str, str]:
    """Swimmer card caption (§6.2). Returns (caption, first_comment_body, hook_style).

    Structure: rotating intro -> name + club · team + age group -> the achievement in plain numbers
    -> one warm closing line -> link nudge -> hashtags.

    `goldStrokes` is stated as a count rather than by naming the strokes. Naming them would mean the
    copy asserting which four, and the snapshot's `rows` only carry the top sixteen events — so a
    fifteen-event swimmer could be described wrongly. The count is always true.
    """
    name = facts.get("name") or facts.get("romanized") or "—"
    club = facts.get("club")
    province = facts.get("province")
    # The province is a provincial TEAM affiliation, shown as "ทีม{province}" so it doesn't read as a
    # location — the same treatment the card itself uses.
    identity = " · ".join(x for x in [name, club, f"ทีม{province}" if province else None] if x)

    ages = facts.get("ageGroups") or []
    age_line = f"รุ่น {_age(ages[0])}" if ages else None

    golds = facts.get("goldCount") or 0
    strokes = facts.get("goldStrokes") or 0
    ranked = facts.get("rankedCount") or 0

    if golds and strokes >= 2:
        achievement = f"อันดับ 1 ของประเทศ {golds} รายการ ครบ {strokes} ท่า"
        hook = "multi_gold"
    elif golds:
        achievement = f"อันดับ 1 ของประเทศ {golds} รายการ จาก {ranked} รายการที่ติดอันดับ"
        hook = "gold_count"
    else:
        achievement = f"ติดอันดับประเทศ {ranked} รายการ"
        hook = "ranked_breadth"

    closing = "สถิติที่สะสมมาทีละรายการ ไม่ได้มาในวันเดียว"

    caption = "\n\n".join(
        x
        for x in [
            intro,
            " · ".join(x for x in [identity, age_line] if x),
            achievement,
            closing,
            "สถิติทั้งหมดอยู่ในคอมเมนต์แรก",
            _hashtags(config),
        ]
        if x
    )
    return caption, f"📊 สถิติและอันดับทั้งหมดของ {name}", hook


def event_th(*, facts: dict[str, Any], intro: str, config: dict[str, Any]) -> tuple[str, str, str]:
    """Event board caption (§6.3). Returns (caption, first_comment_body, hook_style).

    Structure: category -> how many places the board shows -> personal hook -> link nudge -> hashtags.

    The count comes from `rowCount`, never from the requested `n`. A thin age group can return eight
    swimmers for a top-ten request, and a caption promising ten over a card showing eight is the exact
    failure `claims.check` exists to catch.
    """
    stroke = STROKE_TH.get(facts.get("stroke", ""), facts.get("stroke", ""))
    distance = facts.get("distance")
    unit = config.get("unit_labels", {}).get("metre_short", "ม.")
    gender = GENDER_TH.get(facts.get("gender", ""), "")
    course = COURSE_TH.get(facts.get("course", ""), facts.get("course", ""))
    age = _age(facts.get("ageGroup", ""))
    season = facts.get("season", "")
    shown = facts.get("rowCount") or 0

    category = " · ".join(
        x for x in [f"{stroke} {distance} {unit}", gender, f"รุ่น {age}" if age else None, course] if x
    )
    headline = f"{shown} อันดับแรกของประเทศในฤดูกาล {season}" if season else f"{shown} อันดับแรกของประเทศ"

    caption = "\n\n".join(
        x
        for x in [
            category,
            headline,
            "เวลาของคุณอยู่อันดับไหน?",
            "ตารางเต็มอยู่ในคอมเมนต์แรก",
            _hashtags(config),
        ]
        if x
    )
    return caption, "", "personal_rank_question"


def register(templates_module: Any) -> None:
    """Register ThaiSwim's structures with the core registry.

    Called from `adapters/registry.bootstrap`. The core never imports this module.
    """
    templates_module.register("swimmer", "th", swimmer_th)
    templates_module.register("event", "th", event_th)
