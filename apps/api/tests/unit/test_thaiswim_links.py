"""Pins the ThaiSwim URL formats the adapter derives.

The studios build canonical links in the browser and never persist them, and the card-engine query
params live only in the render routes. So the adapter duplicates both formats — which means a route
change on the ThaiSwim side would otherwise show up as posts linking to 404s, days later, in public.

These tests are the tripwire. If one fails, check `dev/thaiswim` before changing the expectation:

    apps/admin/app/tools/share-swimmer/page.tsx   profileLink, pngUrl
    apps/admin/app/tools/share-event/page.tsx     captionLink, cardQuery
    apps/web/app/api/card/{swimmer,event}/route.tsx   accepted params
"""

from datetime import UTC, datetime

import pytest

from brandcortex.adapters.source.thaiswim import mapping

SITE = "https://thaiswim.com"

SWIMMER_PARAMS = {"slug": "rin-suebsanguan", "id": "clzq8x1v40000abcd1234efgh"}
EVENT_PARAMS = {
    "stroke": "backstroke",
    "distance": 50,
    "gender": "F",
    "ageGroup": "55-59",
    "course": "LCM",
    "n": 10,
}


def test_swimmer_canonical_link() -> None:
    assert (
        mapping.canonical_link("swimmer", SWIMMER_PARAMS, site_url=SITE)
        == f"{SITE}/swimmers/rin-suebsanguan"
    )


def test_event_canonical_link() -> None:
    """Note `dist` and `age` in the query, against `distance`/`ageGroup` in the snapshot."""
    assert mapping.canonical_link("event", EVENT_PARAMS, site_url=SITE) == (
        f"{SITE}/rankings?stroke=backstroke&dist=50&gender=F&age=55-59&course=LCM"
    )


def test_swimmer_render_url_ignores_locale() -> None:
    """The swimmer route takes no `lang`, so the locale must not leak into its URL as a stray param."""
    for locale in ("th", "en"):
        assert (
            mapping.render_url("swimmer", SWIMMER_PARAMS, site_url=SITE, locale=locale)
            == f"{SITE}/api/card/swimmer?slug=rin-suebsanguan"
        )


@pytest.mark.parametrize("locale", ["th", "en"])
def test_event_render_url_carries_locale(locale: str) -> None:
    """The event engine renders either language, so the locale must reach it — no hardcoded `th`."""
    assert mapping.render_url("event", EVENT_PARAMS, site_url=SITE, locale=locale) == (
        f"{SITE}/api/card/event?stroke=backstroke&dist=50&gender=F"
        f"&age=55-59&course=LCM&n=10&lang={locale}"
    )


class TestResolveLocale:
    def test_prefers_recorded_lang(self) -> None:
        """Works the day `card-history` starts recording `lang` — no change needed here."""
        assert mapping.resolve_locale("event", {**EVENT_PARAMS, "lang": "en"}, default="th") == "en"

    def test_falls_back_to_brand_default(self) -> None:
        """Today's ThaiSwim path: `lang` is never recorded, so the brand default decides."""
        assert mapping.resolve_locale("event", EVENT_PARAMS, default="th") == "th"

    def test_default_is_not_assumed_thai(self) -> None:
        """Brand #2 is expected to be an English site."""
        assert mapping.resolve_locale("event", EVENT_PARAMS, default="en") == "en"


class TestSeasonLabel:
    """Mirrors `rankingPairLabel()` in apps/web/lib/swim-format.ts — the calendar 2-year pair off the
    UTC year, advancing each January."""

    def test_mid_season(self) -> None:
        assert mapping.season_label(datetime(2026, 8, 4, 9, 3, tzinfo=UTC)) == "2025-2026"

    def test_advances_in_january(self) -> None:
        assert mapping.season_label(datetime(2025, 12, 31, 23, 0, tzinfo=UTC)) == "2024-2025"
        assert mapping.season_label(datetime(2026, 1, 1, 1, 0, tzinfo=UTC)) == "2025-2026"

    def test_uses_utc_not_bangkok(self) -> None:
        """Bangkok is UTC+7, so 06:00 on Jan 1 local is still Dec 31 in UTC — and the card, which
        computes in UTC, would print the older season. Caption must match the image."""
        from zoneinfo import ZoneInfo

        bangkok_new_year = datetime(2026, 1, 1, 6, 0, tzinfo=ZoneInfo("Asia/Bangkok"))
        assert mapping.season_label(bangkok_new_year) == "2024-2025"
