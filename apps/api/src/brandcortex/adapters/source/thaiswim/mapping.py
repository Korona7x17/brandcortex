"""`card_renders` rows -> content-item envelope.

Every ThaiSwim-shaped detail belongs in this file. Once a row leaves here it is a generic `ContentItem`
and the core stops knowing what a stroke is.

**The card engines are not modified.** Anything the post structures need that the snapshot doesn't carry
is derived here.

## The two snapshots, as actually written

**kind = "swimmer"** (`params`: `{slug, id}`)

    name          Thai name              romanized     English name
    club          club (Thai preferred)  province      provincial TEAM, rendered "ทีม{province}"
    ageGroups[]   e.g. ["55-59"]         goldCount     national #1s
    goldStrokes   distinct strokes won   multiGold     goldCount >= 2 and topRank == 1
    rankedCount   nationally-ranked      topRank       best rank held
    rows[<=16]    {stroke, distance, course, rank, timeMs, time, ageGroup}

**kind = "event"** (`params`: `{stroke, distance, gender, ageGroup, course, n}`)

    stroke distance gender ageGroup course n   the bucket
    rowCount                                   rows actually returned (can be < n)
    rows[]        {rank, timeMs, time, name, club, province, isRelayLeadoff}

Field names differ from the architecture doc's §4.2 sketch, which predates reading the code:
`first_rank_count` is `goldCount`, `strokes_covered` is `goldStrokes`, and the champion is `rows[0]`.

## Derived here, not read

* **`season`** — absent from the event snapshot; computed by `season_label` (see its docstring).
* **`event_count`** — `resultCount` isn't written to the snapshot. Use `rankedCount`: "9 national #1s
  across 9 ranked events" is the more precise claim anyway.
* **`locale`** — resolved by `resolve_locale`, not hardcoded. See its docstring for why ThaiSwim
  currently yields `"th"` and what would change that.
* **`canonical_link`** — built by `canonical_link`, since the studios construct links in the browser and
  never persist them.
"""

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

from brandcortex.schemas.content_item import ContentItem

#: Fixed canvas of the swimmer card. Event cards are 1080 x (452 + rows*130 + 176) — variable, so their
#: height is left unset in the envelope rather than guessed.
SWIMMER_CARD_SIZE = (1080, 1350)

def resolve_locale(kind: str, params: dict[str, Any], *, default: str) -> str:
    """Locale for one card, resolved rather than assumed: `params.lang` if present, else `default`
    (from `brand_config.default_locale`).

    What ThaiSwim yields today, and why:

    * **event** — the card engine takes `?lang=th|en` and the studio has a working toggle, but
      `card-history` doesn't include `lang` in its POST body, so recorded rows carry no language. Falls
      back to the default. Recording `lang` is a one-line change to the history route (not the card
      engine) and English event posts start working with no change here.
    * **swimmer** — the render route has no `lang` param at all, so the image is Thai whatever this
      returns. An English caption over a Thai card is a product decision, not a bug this can prevent.

    Neither limit belongs in the core, and neither should be baked in as a constant: brand #2 is
    expected to be English, and the resolution order above already handles that.
    """
    lang = params.get("lang")
    return str(lang) if lang else default


def row_to_content_item(row: dict[str, Any], *, site_url: str, default_locale: str = "th") -> ContentItem:
    """Map one `card_renders` row into the envelope."""
    kind = row["kind"]
    if kind not in ("swimmer", "event"):
        raise ValueError(f"unknown card_renders.kind {kind!r}")

    params = dict(row.get("params") or {})
    facts = dict(row.get("snapshot") or {})
    generated_at = row["createdAt"]
    locale = resolve_locale(kind, params, default=default_locale)

    # Derived, because the snapshot does not carry them and the card engines are not being changed.
    if kind == "event":
        facts.setdefault("season", season_label(generated_at))
    facts["wow_factor"] = compute_wow_factor(kind, facts)

    asset: dict[str, Any] = {
        "kind": "image",
        "render_url": render_url(kind, params, site_url=site_url, locale=locale),
    }
    if kind == "swimmer":
        asset["width"], asset["height"] = SWIMMER_CARD_SIZE
    else:
        # Event cards are 1080 x (452 + rows*130 + 176). Width is fixed; height is left unset rather
        # than computed, so nothing downstream mistakes an estimate for a measurement.
        asset["width"] = 1080

    return ContentItem(
        content_id=row["id"],
        brand="thaiswim",
        source_type=kind,
        locale=locale,
        asset=asset,
        canonical_link=canonical_link(kind, params, site_url=site_url),
        facts=facts,
        generated_at=generated_at,
    )


def render_url(kind: str, params: dict[str, Any], *, site_url: str, locale: str) -> str:
    """Rebuild the exact card-engine URL a row was rendered from.

        swimmer -> {site}/api/card/swimmer?slug={slug}
        event   -> {site}/api/card/event?stroke=&dist=&gender=&age=&course=&n=&lang={locale}

    Two traps, both from the engine's query names differing from the snapshot's keys: the event engine
    takes `dist` where the snapshot says `distance`, and `age` where it says `ageGroup`. The swimmer
    route takes no `lang` at all, so `locale` is ignored there rather than appended as a stray param.
    """
    site = site_url.rstrip("/")
    if kind == "swimmer":
        key = params.get("slug") or params.get("id")
        if not key:
            raise ValueError("swimmer card params carry neither slug nor id")
        return f"{site}/api/card/swimmer?" + urlencode({"slug": key})
    query = urlencode(
        {
            "stroke": params["stroke"],
            "dist": params["distance"],
            "gender": params["gender"],
            "age": params["ageGroup"],
            "course": params["course"],
            "n": params["n"],
            "lang": locale,
        }
    )
    return f"{site}/api/card/event?{query}"


def canonical_link(kind: str, params: dict[str, Any], *, site_url: str) -> str:
    """Derive the link that goes in the first comment.

        swimmer -> {site}/swimmers/{slug}
        event   -> {site}/rankings?stroke=&dist=&gender=&age=&course=

    Both studios build these in the browser and never persist them, so the format is duplicated here.
    `tests/unit/test_thaiswim_links.py` pins both shapes so a route change on the ThaiSwim side breaks a
    test rather than quietly publishing dead links.
    """
    site = site_url.rstrip("/")
    if kind == "swimmer":
        key = params.get("slug") or params.get("id")
        if not key:
            raise ValueError("swimmer card params carry neither slug nor id")
        return f"{site}/swimmers/{key}"
    query = urlencode(
        {
            "stroke": params["stroke"],
            "dist": params["distance"],
            "gender": params["gender"],
            "age": params["ageGroup"],
            "course": params["course"],
        }
    )
    return f"{site}/rankings?{query}"


def season_label(at: datetime) -> str:
    """The national-ranking window a card belongs to, e.g. "2025-2026".

    Mirrors `rankingPairLabel()` in the web app: the calendar 2-year pair off the **UTC** year,
    advancing each January.

    UTC deliberately, even though the brand runs in Asia/Bangkok. The card itself prints the season
    using the web app's UTC rule, so matching that is what keeps caption and image agreeing. The two
    differ only for the first 7 hours of January 1st Bangkok time, and there the card is the one the
    reader can see.
    """
    y = at.astimezone(UTC).year
    return f"{y - 1}-{y}"


def compute_wow_factor(kind: str, snapshot: dict[str, Any]) -> float:
    """Score 0..1 for how remarkable an item is — feeds ranking and the opportunity scanner (§10.2).

    A **hand-authored prior**, not a learned model. The spec is explicit that meaningful learning takes
    weeks to months at a few posts a day (§10.5), so this encodes what someone who knows the sport would
    say is striking, and gets recalibrated against observed amplification once there is history.

    Swimmer signals, in rough order of how much they impress a reader:

    * `goldStrokes` — a four-stroke sweep is rarer and harder than four wins in one stroke
    * `goldCount`   — national #1s, saturating around ten
    * age           — an older masters swimmer still holding national rank is the story people share
    * `rankedCount` — breadth of events, a weaker signal on its own

    Event signals:

    * margin between first and second — a dominant swim reads as a result, a close one as a race
    * `rowCount` — a full board means a genuinely contested group rather than a thin bucket
    * age group — same reasoning as above
    """
    def clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    def age_bonus(groups: Any) -> float:
        """Oldest age-group boundary, scaled so 40 is unremarkable and 80+ is the top of the range."""
        ages: list[int] = []
        for g in groups if isinstance(groups, list) else [groups]:
            if isinstance(g, str) and g[:2].isdigit():
                ages.append(int(g[:2]))
        return clamp((max(ages) - 40) / 40) if ages else 0.0

    if kind == "swimmer":
        golds = float(snapshot.get("goldCount") or 0)
        strokes = float(snapshot.get("goldStrokes") or 0)
        ranked = float(snapshot.get("rankedCount") or 0)
        score = (
            0.35 * clamp(strokes / 4)
            + 0.30 * clamp(golds / 10)
            + 0.20 * age_bonus(snapshot.get("ageGroups"))
            + 0.15 * clamp(ranked / 12)
        )
        return round(clamp(score), 3)

    rows = snapshot.get("rows") or []
    margin = 0.0
    if len(rows) >= 2:
        first, second = rows[0].get("timeMs"), rows[1].get("timeMs")
        if first and second and first > 0:
            # Relative gap; 5% clear of the field is already commanding.
            margin = clamp(((second - first) / first) / 0.05)
    depth = clamp(float(snapshot.get("rowCount") or 0) / 10)
    score = 0.45 * margin + 0.30 * depth + 0.25 * age_bonus(snapshot.get("ageGroup"))
    return round(clamp(score), 3)
