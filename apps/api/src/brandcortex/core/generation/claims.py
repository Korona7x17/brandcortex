"""Numeric grounding: every number in the copy must come from the facts.

The most likely way generated copy goes wrong is not tone — it is a number the image doesn't support.
"9 national #1s" over a card showing 11 is worse than an awkward sentence, because it is a public claim
about a real person that the reader can check against the graphic in the same post.

This is a **computation, not a critic**. It cannot be argued out of a verdict, costs nothing, runs on
every draft, and is itself testable. A model asked "does this caption match the facts?" is strictly
worse at this job than set membership.

Kept separate from `voice.py` on purpose: voice is a style constraint the brand chooses and could
loosen; this is a factual constraint that no configuration should be able to switch off.

## How it works

Harvest every numeric token reachable in `facts` (recursively, including numbers embedded in strings
like `"55-59"` and `"42.06"`), harvest every numeric token in the caption, and report the difference.
URLs and hashtags are stripped first — they carry digits that assert nothing.

The check is one-directional. Copy need not use every fact; it may not invent one.
"""

import re
from dataclasses import dataclass, field
from typing import Any

#: Thai digits map to Arabic before comparison; a card's numbers may be written either way.
_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

#: A number token: digits, optionally with `.` or `:` separators (`42.06`, `1:02.35`).
_NUMBER = re.compile(r"\d+(?:[.:]\d+)*")

_URL = re.compile(r"https?://\S+")
_HASHTAG = re.compile(r"#\S+")

#: Numbers that are part of the language rather than a claim about the subject. Extend per brand via
#: `brand_config.voice.allowed_numbers` rather than editing this.
DEFAULT_ALLOWED: frozenset[str] = frozenset({"1", "2", "3"})


@dataclass
class ClaimCheck:
    ok: bool
    #: Numbers in the copy with no support in `facts`. These are the blocking failures.
    unsupported: list[str] = field(default_factory=list)
    #: Everything the facts could have supported, for debugging a false positive.
    supported: set[str] = field(default_factory=set)

    def __bool__(self) -> bool:
        return self.ok


def _canonical(token: str) -> str:
    """Normalize so `50`, `50.0` and `050` compare equal, while `42.06` stays itself."""
    token = token.translate(_THAI_DIGITS)
    try:
        return str(int(token))
    except ValueError:
        pass
    try:
        f = float(token)
    except ValueError:
        return token
    return str(int(f)) if f.is_integer() else token


def _iter_scalars(obj: Any):
    """Walk a nested facts payload, yielding every scalar leaf."""
    if isinstance(obj, dict):
        for value in obj.values():
            yield from _iter_scalars(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            yield from _iter_scalars(value)
    else:
        yield obj


def supported_numbers(facts: dict[str, Any]) -> set[str]:
    """Every number the facts can vouch for.

    Numbers embedded in strings count: an age group of `"55-59"` supports both `55` and `59`, and a
    season of `"2025-2026"` supports both years. Booleans are skipped — in Python `True` is an `int`,
    and letting it through would silently support `1`.
    """
    out: set[str] = set()
    for value in _iter_scalars(facts):
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, (int, float)):
            out.add(_canonical(str(value)))
        elif isinstance(value, str):
            for match in _NUMBER.findall(value.translate(_THAI_DIGITS)):
                out.add(_canonical(match))
    return out


def check(
    text: str,
    facts: dict[str, Any],
    *,
    allowed: frozenset[str] | set[str] = DEFAULT_ALLOWED,
    notation: tuple[str, ...] | list[str] = (),
) -> ClaimCheck:
    """Verify every number in `text` is grounded in `facts`.

    Strips URLs and hashtags first: a link's path digits and a tag like `#Top10` are not assertions
    about the subject, and scanning them produces noise that trains people to ignore this check.

    `notation` strips the brand's fixed labels too, and that one is not a nicety. ThaiSwim renders a
    long-course pool as `สระ 50 ม.` — the 50 is the *pool's* length, not a claim about the swim. On a
    50m event it happens to match the facts and passes; on a 100m event the identical, correct label
    was reported as an unsupported number. A check that rejects correct copy is worse than no check,
    because it teaches people to click through it.
    """
    scrubbed = _HASHTAG.sub(" ", _URL.sub(" ", text))
    for label in sorted(notation, key=len, reverse=True):
        if label:
            scrubbed = scrubbed.replace(label, " ")
    scrubbed = scrubbed.translate(_THAI_DIGITS)
    grounded = supported_numbers(facts)
    allow = {_canonical(a) for a in allowed}

    unsupported = [
        match
        for match in _NUMBER.findall(scrubbed)
        if _canonical(match) not in grounded and _canonical(match) not in allow
    ]
    # Preserve first-seen order, drop duplicates — one wrong number reported once.
    seen: set[str] = set()
    deduped = [m for m in unsupported if not (m in seen or seen.add(m))]

    return ClaimCheck(ok=not deduped, unsupported=deduped, supported=grounded)


# --- Claims bound to their source ---------------------------------------------------------------
#
# `check` above answers "does this number exist in the facts". That stops a caption inventing a
# medal count, and it does not stop a caption attaching a real number to the wrong thing: with
# goldCount 3 and rankedCount 12, "อันดับ 1 ของประเทศ 12 รายการ" passes, because 12 is in the facts.
# It is simply about the wrong fact.
#
# Both of the things that go wrong here are lookups, not judgments, so both are computable:
#
#   bindings   a phrase pattern names the fact it must equal — "N ท่า" is `goldStrokes`, and any
#              other number in that slot is wrong however real it is elsewhere
#   notation   a vocabulary the brand has standardised on, and the spellings that are therefore
#              forbidden — `เมตร` where the cards render `ม.`, or a raw `LCM` where they render
#              `สระ 50 ม.`
#
# Both live in `brand_config`, because both are brand-shaped. The core executes them and never
# learns what a stroke is.

_BINDING_CACHE: dict[str, re.Pattern[str]] = {}


@dataclass
class BindingViolation:
    pattern: str
    fact: str
    said: str
    expected: str


def _compiled(pattern: str) -> re.Pattern[str]:
    if pattern not in _BINDING_CACHE:
        _BINDING_CACHE[pattern] = re.compile(pattern)
    return _BINDING_CACHE[pattern]


def check_bindings(text: str, facts: dict, bindings: list[dict]) -> list[BindingViolation]:
    """Every bound phrase must carry the number its fact holds.

    A pattern that does not appear is not a violation — angles legitimately differ in what they
    mention. The check is only ever "when you said this, was it the right figure".
    """
    violations: list[BindingViolation] = []
    for binding in bindings or []:
        pattern, fact = binding.get("pattern"), binding.get("fact")
        if not pattern or not fact or fact not in facts:
            continue
        expected = _canonical(str(facts[fact]))
        for match in _compiled(pattern).finditer(text):
            said = _canonical(match.group(1))
            if said != expected:
                violations.append(
                    BindingViolation(pattern=pattern, fact=fact, said=said, expected=expected)
                )
    return violations


def check_notation(text: str, forbidden: list[str]) -> list[str]:
    """Spellings the brand has standardised away from. Found means rejected."""
    return [token for token in forbidden or [] if token and token in text]
