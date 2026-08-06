"""ThaiSwim post structures, in Thai (spec §6.2, §6.3).

These live with the adapter, not in `core/`, because they are this brand's writing. The core owns the
registry and the constraints; the brand owns the words. Brand #2 registers its own and touches nothing
here.

Three rules shape every line below:

* **No number appears that isn't in `facts`.** `claims.check` enforces it, and these templates are
  written to pass by construction — every figure is read from the snapshot rather than counted, phrased
  or rounded in the copy.
* **The link never appears in the caption.** It goes in the first comment, which is a separate return
  value, not a formatting choice.
* **A person's name is never written bare.** Everything here goes through `_person`, which carries the
  honorific from `brand_config`; `core.generation.voice` rejects a draft that drops it. These are
  masters swimmers, most of them older than the reader, and in Thai an unadorned name is a slight
  aimed at exactly the audience the post is for.

Two registers, and the reviewer picks: the reporting angles state the fact and leave it alone, and
`_sweep_th` / `_longevity_th` congratulate, in the shape of a post the owner wrote by hand. Register
is carried through both halves of a variant — a warm caption over a flat first comment reads as two
people writing one post.

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


def _person(facts: dict[str, Any], config: dict[str, Any]) -> str:
    """The swimmer's name with the brand's honorific, or "" when the card has no usable name.

    Never a bare name. These are masters swimmers, most of them older than whoever is reading — Thai
    does not let you write such a person's name unadorned and stay polite, and the reader who notices
    is exactly the reader the post is for. The prefix comes from `brand_config.voice.honorific` and
    `core.generation.voice` rejects a caption that drops it, so this is the convenience, not the
    guarantee.

    The empty string is deliberate: a card with no name should fall back to a line that needs none,
    not print the honorific on its own or on a placeholder dash.
    """
    name = facts.get("name") or facts.get("romanized") or ""
    if not name:
        return ""
    prefix = ((config.get("voice") or {}).get("honorific") or {}).get("prefix", "")
    return f"{prefix}{name}"


def swimmer_th(*, facts: dict[str, Any], intro: str, config: dict[str, Any]) -> tuple[str, str, str]:
    """Swimmer card caption (§6.2), plainest form. Returns (caption, first_comment_body, hook_style).

    Who, then what they did, then where the link is. Three lines and the hashtags.

    `intro` is accepted and unused, like every swimmer angle here. The rotating opener and the warm
    sign-off that used to wrap this shape were the brand's advertising voice leaking back in — "every
    season there is a swimmer who makes us stop and look" is a line written to sell the post, and the
    owner's own hand-written posts carry nothing like it. See the note above `SWIMMER_ANGLES_TH`.

    `goldStrokes` is stated as a count rather than by naming the strokes. Naming them would mean the
    copy asserting which four, and the snapshot's `rows` only carry the top sixteen events — so a
    fifteen-event swimmer could be described wrongly. The count is always true.
    """
    golds = facts.get("goldCount") or 0
    strokes = facts.get("goldStrokes") or 0
    ranked = facts.get("rankedCount") or 0

    if golds and strokes >= 2:
        achievement = f"อันดับ 1 ของประเทศไทย {golds} รายการ ครบ {strokes} ท่า"
        hook = "multi_gold"
    elif golds:
        achievement = f"อันดับ 1 ของประเทศไทย {golds} รายการ จาก {ranked} รายการที่ติดอันดับ"
        hook = "gold_count"
    else:
        achievement = f"ติดอันดับประเทศไทย {ranked} รายการ"
        hook = "ranked_breadth"

    caption = _lines(
        [" · ".join(x for x in [_identity(facts, config), _age_line(facts)] if x), achievement],
        config,
        nudge=0,
    )
    return caption, _swimmer_comment(facts, config), hook


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
# The first two are written in the congratulatory register and the rest report; the choice of what to
# notice and the choice of how warmly to say it are independent, so the reviewer gets both.
#
# Every one obeys the same rules the original does. `goldStrokes` is stated as a count, never by
# naming which four — the snapshot's `rows` cap at sixteen events, so naming them could describe a
# fifteen-event swimmer wrongly. No number appears that is not in `facts`; `claims.check` enforces
# that afterwards regardless of what is written here.
#
# **No rotating intro, and no sign-off line.** Both were removed on the owner's judgement that the
# copy read as promotion. They were also the reason four of six variants were the same post: one
# skeleton — opener, identity chain, one claim, sign-off, nudge — with a single line swapped. The
# lines themselves ("ทุกฤดูกาลมีนักว่ายน้ำที่ทำให้เราต้องหยุดมอง", "เบื้องหลังคือการซ้อมที่ไม่มีใครเห็น") are
# advertising copy: they tell the reader how to feel about a fact the card already shows them.
#
# What replaced them is the shape of the owner's own posts — a fact, a person, a nudge, and stop.
# The angles now differ in FORM as well as content: a record-card chain, a congratulation, a single
# prose sentence, a counts headline, a swim, a club-first line. Lengths run 3 to 5 lines. Two carry
# the congratulatory frame; the rest report.
#
# `intro_bank` and `intro_rotation` are therefore unused by swimmer posts. Left in place: the event
# structures may want them, the mechanism is sound, and the engine only records an `intro_line` when
# the caption actually opens with it.

#: The link nudge, plainly. Three phrasings so six variants don't close on one identical sentence —
#: but none of them sells anything, which is the whole point of the rewrite.
NUDGES_TH: tuple[str, ...] = (
    "สถิติทั้งหมดอยู่ในคอมเมนต์แรก",
    "โปรไฟล์และสถิติทั้งหมดอยู่ในคอมเมนต์แรก",
    "ดูสถิติและโปรไฟล์ทั้งหมดได้จากลิงก์ในคอมเมนต์แรก",
)


def _identity(facts: dict[str, Any], config: dict[str, Any]) -> str:
    """Name · club · provincial team, exactly as the card presents them — the name never bare."""
    club = facts.get("club")
    province = facts.get("province")
    # "ทีม{province}" so the province doesn't read as an address — the card's own treatment.
    return " · ".join(
        x for x in [_person(facts, config), club, f"ทีม{province}" if province else None] if x
    )


def _age_line(facts: dict[str, Any]) -> str | None:
    ages = facts.get("ageGroups") or []
    return f"รุ่น {_age(ages[0])}" if ages else None


def _lines(parts: list[str | None], config: dict[str, Any], *, nudge: int = 0) -> str:
    """Content lines, then the nudge, then the hashtags — single newlines throughout.

    Single rather than blank lines because that is how the owner writes these by hand, and because a
    three-line post separated by blank lines occupies a screen it hasn't earned.
    """
    return "\n".join(
        x for x in [*parts, NUDGES_TH[nudge % len(NUDGES_TH)], _hashtags(config)] if x
    )


#: Openers for the first comment, the line that sits above the link. Rotated with the closings so six
#: variants don't all end in the same sentence — the link nudge is as visible as the caption and
#: repeating it verbatim across every post is what makes a feed read as automated.
#:
#: Named and general lines alternate on purpose. The named ones carry the honorific through
#: `_person`, so the name is never bare here either; the general ones are the right choice when the
#: caption has already named the swimmer twice, and the only choice when the card has no name.
COMMENTS_TH: tuple[str, ...] = (
    "📊 สถิติทั้งหมดของ{person} อยู่ที่นี่",
    "📊 สถิติทั้งหมดอยู่ที่นี่",
    "📊 ดูสถิติและผลงานทั้งหมดของ{person} ได้ที่นี่",
    "📊 ดูโปรไฟล์และสถิติทั้งหมดได้ที่นี่",
    "📊 สถิติและอันดับทั้งหมดอยู่ที่นี่",
)


#: The same bank in the warm register, for the angles that congratulate rather than report. A warm
#: caption above a flat "📊 สถิติทั้งหมดอยู่ที่นี่" reads as two people writing one post, so register
#: is chosen per variant and carried through both halves.
COMMENTS_WARM_TH: tuple[str, ...] = (
    "👉 ดูสถิติและโปรไฟล์ทั้งหมดของ{person} ได้ที่นี่",
    "👉 สถิติและอันดับทั้งหมดอยู่ที่นี่",
    "🏆 ผลงานและสถิติทั้งหมดของ{person} อยู่ที่นี่",
    "👉 ดูโปรไฟล์และสถิติทั้งหมดได้ที่นี่",
)


def _swimmer_comment(
    facts: dict[str, Any], config: dict[str, Any], index: int = 0, *, warm: bool = False
) -> str:
    """One line from the bank. Falls back to a general line when the card carries no name."""
    bank = COMMENTS_WARM_TH if warm else COMMENTS_TH
    person = _person(facts, config)
    line = bank[index % len(bank)]
    if "{person}" in line and not person:
        line = next(x for x in bank if "{person}" not in x)
    return line.format(person=person)


def _from(facts: dict[str, Any]) -> str | None:
    """"จาก {club}" — the affiliation as an attribution, the way the owner's own posts write it.

    Falls back to the provincial team, and to nothing at all: "จาก" with no one to name reads worse
    than a line that simply doesn't mention a club.
    """
    club = facts.get("club") or (f"ทีม{facts['province']}" if facts.get("province") else None)
    return f"จาก {club}" if club else None


def _assemble_warm(headline: str, claim: str, facts: dict[str, Any], config: dict[str, Any]) -> str:
    """The congratulatory shape: headline -> who -> what they did -> link nudge -> hashtags.

    Single newlines rather than blank lines between them. This is the owner's own register, kept in
    shape so the generated posts sit next to the hand-written ones without a seam.

    Two emoji, and the ceiling is two: 🏆 on the headline and 👏 on the achievement. The reference
    post carried arrows on the nudge as well; they were the first thing to go when the ceiling came
    down, because they decorate a line that already says where the link is, while the other two carry
    the congratulation itself.

    Every rule the factual templates obey still applies here: no number that isn't in `facts`, no
    link in the body, and never a bare name — `ขอแสดงความยินดีกับ` is followed by `_person`, which
    carries the honorific.
    """
    person = _person(facts, config)
    congratulation = " ".join(
        x for x in ["ขอแสดงความยินดีกับ", person or None, _from(facts)] if x
    )
    return "\n".join(
        x
        for x in [
            headline,
            congratulation if person else _from(facts),
            claim,
            "ดูสถิติและโปรไฟล์ทั้งหมดได้จากลิงก์ในคอมเมนต์แรก",
            _hashtags(config),
        ]
        if x
    )


def _sweep_th(*, facts, intro, config, closing=0):
    """Across four strokes — the rarest thing on most of these cards. Written warm (see `_assemble_warm`).

    The intro is not used here. This shape opens on the achievement itself, which is what makes it
    read as a congratulation rather than a bulletin; a rotating soft line above the trophy would put
    two openings on one post.
    """
    strokes = facts.get("goldStrokes") or 0
    if strokes < 2:
        raise _NotApplicable("only one stroke won")
    golds = facts.get("goldCount") or 0
    ages = facts.get("ageGroups") or []
    age = f" ในรุ่นอายุ {_age(ages[0])} ปี" if ages else ""
    claim = (
        f"ครองอันดับ 1 ของประเทศไทยถึง {golds} รายการ ครบ {strokes} ท่า{age} 👏"
        if golds
        else f"อันดับ 1 ของประเทศไทย ครบ {strokes} ท่า{age} 👏"
    )
    headline = (
        f"🏆 {golds} รายการ อันดับ 1 ของประเทศไทย"
        if golds
        else f"🏆 อันดับ 1 ของประเทศไทย ครบ {strokes} ท่า"
    )
    return (
        _assemble_warm(headline, claim, facts, config),
        _swimmer_comment(facts, config, closing, warm=True),
        "multi_gold",
    )


def _longevity_th(*, facts, intro, config, closing=1):
    """Still at national level in this age group — the angle that travels furthest with masters.

    One sentence, no headline, no emoji. The shortest variant on offer and the only one written as
    prose: `sweep` already congratulates from a trophy line, and a second post in that shape would be
    the sameness the reviewer is meant to be choosing away from.
    """
    ages = facts.get("ageGroups") or []
    if not ages:
        raise _NotApplicable("no age group on the card")
    golds = facts.get("goldCount") or 0
    ranked = facts.get("rankedCount") or 0
    person = _person(facts, config)
    if not person:
        raise _NotApplicable("a prose sentence needs a name to be about")
    achievement = (
        f"ยังครองอันดับ 1 ของประเทศไทย {golds} รายการ"
        if golds
        else f"ยังติดอันดับประเทศไทย {ranked} รายการ"
    )
    who = " ".join(x for x in [person, _from(facts)] if x)
    return (
        _lines([f"ในรุ่นอายุ {_age(ages[0])} ปี {who} {achievement}"], config, nudge=1),
        _swimmer_comment(facts, config, closing),
        "longevity",
    )


def _breadth_th(*, facts, intro, config, closing=2):
    """How many events, not how many wins — the swimmer who shows up in everything."""
    ranked = facts.get("rankedCount") or 0
    if ranked < 3:
        raise _NotApplicable("too few ranked events to call it breadth")
    golds = facts.get("goldCount") or 0
    # Counts first, person second — the inverse of `plain`, so the two read differently even though
    # both are three lines of fact.
    headline = (
        f"ติดอันดับประเทศไทย {ranked} รายการ · เป็นอันดับ 1 ถึง {golds} รายการ"
        if golds
        else f"ติดอันดับประเทศไทย {ranked} รายการ"
    )
    return (
        _lines(
            [headline, " · ".join(x for x in [_identity(facts, config), _age_line(facts)] if x)],
            config,
            nudge=2,
        ),
        _swimmer_comment(facts, config, closing),
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
    rank = f"อันดับ {best['rank']} ของประเทศไทย" if best.get("rank") else None
    # The swim is the headline: a stroke, a distance, a pool and a time, in the card's own notation.
    swim = " · ".join(x for x in [f"{stroke} {best['distance']} {unit}", course, best["time"], rank] if x)
    return (
        _lines(
            [swim, " · ".join(x for x in [_identity(facts, config), _age_line(facts)] if x)],
            config,
            nudge=0,
        ),
        _swimmer_comment(facts, config, closing),
        "standout_swim",
    )


def _club_th(*, facts, intro, config, closing=4):
    """The version a club Page will share — but the post is still about the swimmer.

    The only angle whose headline carries the swimmer's own name, which is what distinguishes it from
    `sweep`. The club sits on the second line, named plainly and in full: prominent enough that the
    club has a reason to repost, without the post reading as though the club did the swimming. That
    ordering is the owner's call — an earlier version led with the club and was wrong about whose
    achievement this is.
    """
    club = facts.get("club") or (f"ทีม{facts['province']}" if facts.get("province") else None)
    if not club:
        raise _NotApplicable("no club or province on the card")
    person = _person(facts, config)
    if not person:
        raise _NotApplicable("nobody to congratulate")
    golds = facts.get("goldCount") or 0
    ranked = facts.get("rankedCount") or 0
    achievement = (
        f"อันดับ 1 ของประเทศไทย {golds} รายการ" if golds else f"ติดอันดับประเทศไทย {ranked} รายการ"
    )
    ages = facts.get("ageGroups") or []
    age = f"รุ่นอายุ {_age(ages[0])} ปี" if ages else None
    return (
        "\n".join(
            x
            for x in [
                f"🏆 {person} · {achievement}",
                " · ".join(x for x in [club, age] if x) + " 👏",
                NUDGES_TH[2],
                _hashtags(config),
            ]
            if x
        ),
        _swimmer_comment(facts, config, closing, warm=True),
        "club_share",
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
