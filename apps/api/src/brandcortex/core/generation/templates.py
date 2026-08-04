"""Post structures per source type (spec §6.2, §6.3).

Structures are registered by `source_type` string, so a brand with different item kinds registers its
own without touching the engine. The two ThaiSwim structures the spec fixes:

**swimmer** — rotating soft intro (not the previous swimmer post's) -> name + club · team + age group ->
achievement in plain numbers (X national #1s across Y events; name the strokes) -> one warm closing
line -> "link in first comment" nudge -> hashtags. First comment: `📊 … {profile_link}`.

Note the spec calls this source type "profile"; the brand's `card_renders.kind` says "swimmer", and
the adapter passes the kind through unchanged, so "swimmer" is the value the core actually sees.

**event** — category (season, stroke + distance + course, gender, age group) ->
"10 อันดับแรกของประเทศในฤดูกาลนี้" -> personal hook "เวลาของคุณอยู่อันดับไหน?" -> link nudge ->
hashtags. First comment: `{rankings_link}`.

The event hook works because the card already shows the top names: there is nothing to withhold, so the
copy asks the reader about *their own* rank instead of teasing what the image already gave away.
"""

from collections.abc import Callable
from typing import Any

#: (source_type, locale) -> renderer. Registered by the brand's template module at bootstrap.
_TEMPLATES: dict[tuple[str, str], Callable[..., Any]] = {}


def register(source_type: str, locale: str, renderer: Callable[..., Any]) -> None:
    _TEMPLATES[(source_type, locale)] = renderer


def get(source_type: str, locale: str, *, fallback_locale: str | None = None) -> Callable[..., Any]:
    """Resolve a renderer, optionally falling back to the brand's default locale.

    Raises rather than guessing when nothing matches: silently rendering the wrong language is worse
    than a failed draft, because it reaches the audience looking deliberate.
    """
    renderer = _TEMPLATES.get((source_type, locale))
    if renderer is None and fallback_locale:
        renderer = _TEMPLATES.get((source_type, fallback_locale))
    if renderer is None:
        known = sorted(f"{s}/{l}" for s, l in _TEMPLATES)
        raise LookupError(
            f"no template registered for {source_type!r}/{locale!r}; registered: {known or '(none)'}"
        )
    return renderer


def clear() -> None:
    """Drop all registrations. For tests, so one test's brand cannot leak into another's."""
    _TEMPLATES.clear()
