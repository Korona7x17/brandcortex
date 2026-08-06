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

#: (source_type, locale) -> [(angle, renderer)]. One structure per *angle on the same facts* — the
#: four-stroke sweep, longevity, the club, one standout event. A reviewer picks between them.
#:
#: Angles, not rewordings. Five paraphrases of one sentence is not a choice, and the thing worth
#: learning from a reviewer's pick is which framing travels — which is `hook_style`, a lever the
#: learning loop is allowed to tune. Voice is not, and no angle may vary it.
_VARIANTS: dict[tuple[str, str], list[tuple[str, Callable[..., Any]]]] = {}


def register(source_type: str, locale: str, renderer: Callable[..., Any]) -> None:
    """Register a single renderer, replacing any variant set for the same key.

    Replacing matters: "this is now the renderer for swimmer/th" has to mean it, or a test that
    registers a deliberately broken template would still be offered the good variants beside it.
    """
    _TEMPLATES[(source_type, locale)] = renderer
    _VARIANTS[(source_type, locale)] = [("default", renderer)]


def register_variants(
    source_type: str, locale: str, renderers: list[tuple[str, Callable[..., Any]]]
) -> None:
    """Register several angles on the same facts. The first is the default draft."""
    if not renderers:
        raise ValueError("at least one renderer is required")
    _VARIANTS[(source_type, locale)] = list(renderers)
    _TEMPLATES[(source_type, locale)] = renderers[0][1]


def variants(
    source_type: str, locale: str, *, fallback_locale: str | None = None
) -> list[tuple[str, Callable[..., Any]]]:
    """Every angle registered for this structure, falling back the same way `get` does."""
    found = _VARIANTS.get((source_type, locale))
    if found is None and fallback_locale:
        found = _VARIANTS.get((source_type, fallback_locale))
    if found is None:
        return [("default", get(source_type, locale, fallback_locale=fallback_locale))]
    return found


def get(source_type: str, locale: str, *, fallback_locale: str | None = None) -> Callable[..., Any]:
    """Resolve a renderer, optionally falling back to the brand's default locale.

    Raises rather than guessing when nothing matches: silently rendering the wrong language is worse
    than a failed draft, because it reaches the audience looking deliberate.
    """
    renderer = _TEMPLATES.get((source_type, locale))
    if renderer is None and fallback_locale:
        renderer = _TEMPLATES.get((source_type, fallback_locale))
    if renderer is None:
        known = sorted(f"{kind}/{loc}" for kind, loc in _TEMPLATES)
        raise LookupError(
            f"no template registered for {source_type!r}/{locale!r}; registered: {known or '(none)'}"
        )
    return renderer


def clear() -> None:
    """Drop all registrations. For tests, so one test's brand cannot leak into another's."""
    _TEMPLATES.clear()
    _VARIANTS.clear()
