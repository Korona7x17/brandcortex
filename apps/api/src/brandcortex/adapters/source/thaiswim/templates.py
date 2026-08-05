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

    Swimmer posts register several angles so a reviewer picks between framings; the event board
    registers one, because the card already lists the leaders and there is little left to frame.
    """
    templates_module.register_variants("swimmer", "th", SWIMMER_ANGLES_TH)
    templates_module.register("event", "th", event_th)



# --- Angles on the same facts ------------------------------------------------------------------
#
# Six ways to open a swimmer post, and the reviewer picks. Each is a different *thing to notice*,
# not a rewording: the sweep across strokes, staying at national level at this age, the club, the
# breadth of ranked events, one standout swim, and the plain-numbers version already in use.
#
# Every one obeys the same rules the original does. `goldStrokes` is stated as a count, never by
# naming which four — the snapshot's `rows` cap at sixteen events, so naming them could describe a
# fifteen-event swimmer wrongly. No number appears that is not in `facts`; `claims.check` enforces
# that afterwards regardless of what is written here.
#
# The closing lines vary too. One hardcoded sign-off across every post is the same form-letter
# problem the intro rotation exists to solve.

CLOSINGS_TH: tuple[str, ...] = (
    "สถิติที่สะสมมาทีละรายการ ไม่ได้มาในวันเดียว",
    "เบื้องหลังคือการซ้อมที่ไม่มีใครเห็น",
    "ระยะทางในสระวัดกันที่ความสม่ำเสมอ",
    "ชื่อที่คนในวงการว่ายน้ำรู้จักกันดี",
    "ผลงานที่พูดแทนตัวเองได้",
)


def _identity(facts: dict[str, Any]) -> str:
    """Name · club · provincial team, exactly as the card presents them."""
    name = facts.get("name") or facts.get("romanized") or "—"
    club = facts.get("club")
    province = facts.get("province")
    # "ทีม{province}" so the province doesn't read as an address — the card's own treatment.
    return " · ".join(
        x for x in [name, club, f"ทีม{province}" if province else None] if x
    )


def _age_line(facts: dict[str, Any]) -> str | None:
    ages = facts.get("ageGroups") or []
    return f"รุ่น {_age(ages[0])}" if ages else None


def _assemble(parts: list[str | None], config: dict[str, Any]) -> str:
    return "\n\n".join(x for x in [*parts, "สถิติทั้งหมดอยู่ในคอมเมนต์แรก", _hashtags(config)] if x)


def _swimmer_comment(facts: dict[str, Any]) -> str:
    return "📊 สถิติและอันดับทั้งหมด"


def _sweep_th(*, facts, intro, config, closing=0):
    """Across four strokes — the rarest thing on most of these cards."""
    golds = facts.get("goldCount") or 0
    strokes = facts.get("goldStrokes") or 0
    if strokes < 2:
        raise _NotApplicable("only one stroke won")
    return (
        _assemble(
            [
                intro,
                " · ".join(x for x in [_identity(facts), _age_line(facts)] if x),
                # Deliberately a different sentence from the `plain` angle, which leads with the
                # count. Two variants that differ only by their opening line are one variant.
                f"ครบ {strokes} ท่า แต่ละท่าคืออันดับ 1 ของประเทศ",
                CLOSINGS_TH[closing % len(CLOSINGS_TH)],
            ],
            config,
        ),
        _swimmer_comment(facts),
        "multi_gold",
    )


def _longevity_th(*, facts, intro, config, closing=1):
    """Still at national level in this age group. The angle that travels furthest with masters."""
    ages = facts.get("ageGroups") or []
    if not ages:
        raise _NotApplicable("no age group on the card")
    golds = facts.get("goldCount") or 0
    ranked = facts.get("rankedCount") or 0
    claim = (
        f"รุ่น {_age(ages[0])} ยังครองอันดับ 1 ของประเทศ {golds} รายการ"
        if golds
        else f"รุ่น {_age(ages[0])} ติดอันดับประเทศ {ranked} รายการ"
    )
    return (
        _assemble([intro, _identity(facts), claim, CLOSINGS_TH[closing % len(CLOSINGS_TH)]], config),
        _swimmer_comment(facts),
        "longevity",
    )


def _breadth_th(*, facts, intro, config, closing=2):
    """How many events, not how many wins — the swimmer who shows up in everything."""
    ranked = facts.get("rankedCount") or 0
    if ranked < 3:
        raise _NotApplicable("too few ranked events to call it breadth")
    golds = facts.get("goldCount") or 0
    claim = (
        f"ติดอันดับประเทศ {ranked} รายการ และเป็นอันดับ 1 ถึง {golds} รายการ"
        if golds
        else f"ติดอันดับประเทศ {ranked} รายการ"
    )
    return (
        _assemble(
            [intro, " · ".join(x for x in [_identity(facts), _age_line(facts)] if x), claim,
             CLOSINGS_TH[closing % len(CLOSINGS_TH)]],
            config,
        ),
        _swimmer_comment(facts),
        "ranked_breadth",
    )


def _standout_th(*, facts, intro, config, closing=3):
    """One swim, named. The concrete version — a distance, a stroke and a time."""
    rows = facts.get("rows") or []
    best = next((r for r in rows if r.get("rank") == 1), rows[0] if rows else None)
    if not best or not best.get("time"):
        raise _NotApplicable("no timed row to lead with")
    stroke = STROKE_TH.get(best.get("stroke", ""), best.get("stroke", ""))
    course = COURSE_TH.get(best.get("course", ""), "")
    unit = (config.get("unit_labels") or {}).get("metre_short", "ม.")
    line = f"{stroke} {best['distance']} {unit} · {course} · {best['time']}"
    rank_line = (
        f"อันดับ {best['rank']} ของประเทศ" if best.get("rank") else "หนึ่งในสถิติที่ทำไว้"
    )
    return (
        _assemble(
            [intro, " · ".join(x for x in [_identity(facts), _age_line(facts)] if x),
             f"{line}\n{rank_line}", CLOSINGS_TH[closing % len(CLOSINGS_TH)]],
            config,
        ),
        _swimmer_comment(facts),
        "standout_swim",
    )


def _club_th(*, facts, intro, config, closing=4):
    """Lead with the club or provincial team — the version a club Page will share."""
    club = facts.get("club") or facts.get("province")
    if not club:
        raise _NotApplicable("no club or province on the card")
    golds = facts.get("goldCount") or 0
    ranked = facts.get("rankedCount") or 0
    name = facts.get("name") or facts.get("romanized") or "—"
    claim = (
        f"อันดับ 1 ของประเทศ {golds} รายการ" if golds else f"ติดอันดับประเทศ {ranked} รายการ"
    )
    return (
        _assemble(
            [intro, club, " · ".join(x for x in [name, _age_line(facts)] if x), claim,
             CLOSINGS_TH[closing % len(CLOSINGS_TH)]],
            config,
        ),
        _swimmer_comment(facts),
        "club_first",
    )


class _NotApplicable(ValueError):
    """This angle does not fit these facts. Not an error — the variant is simply not offered.

    A swimmer with one gold has no sweep to describe, and a card with no club cannot lead with one.
    Offering a hollow version of an angle is worse than offering fewer angles.
    """


SWIMMER_ANGLES_TH: list[tuple[str, Any]] = [
    ("plain", swimmer_th),
    ("sweep", _sweep_th),
    ("longevity", _longevity_th),
    ("breadth", _breadth_th),
    ("standout", _standout_th),
    ("club", _club_th),
]
