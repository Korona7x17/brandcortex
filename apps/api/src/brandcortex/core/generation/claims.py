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
    text: str, facts: dict[str, Any], *, allowed: frozenset[str] | set[str] = DEFAULT_ALLOWED
) -> ClaimCheck:
    """Verify every number in `text` is grounded in `facts`.

    Strips URLs and hashtags first: a link's path digits and a tag like `#Top10` are not assertions
    about the subject, and scanning them produces noise that trains people to ignore this check.
    """
    scrubbed = _HASHTAG.sub(" ", _URL.sub(" ", text)).translate(_THAI_DIGITS)
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
