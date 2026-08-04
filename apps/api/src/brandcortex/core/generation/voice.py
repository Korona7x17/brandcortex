"""Voice constraints and the check that enforces them (spec §6.1, §10.4).

House voice for ThaiSwim: understated, factual, warm. Recognition, not advertising. No superlative
drumroll, no stacked emojis, no cheesy lines, 0–1 emoji. Let the facts speak.

Two things make this module load-bearing rather than decorative:

1. **Voice is a fixed constraint, not an optimizable lever.** The reflection agent may tune timing,
   formats, and hooks; it may never propose loosening these rules. Hype wins short-term reactions, so
   an unconstrained loop would rediscover exactly the voice the owner rejected.
2. **The check runs after generation, not just in the prompt.** A model told to be understated will
   drift; a validator will not.

The rules themselves live in `brand_config.voice` — this module holds the mechanism, not ThaiSwim's
particular settings.
"""

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VoiceRules:
    max_emoji: int = 1
    banned_phrases: tuple[str, ...] = ()
    #: Taglines printed on the card art. Repeating them in the caption reads as a stutter — the reader
    #: sees the same line twice in one post.
    forbidden_echoes: tuple[str, ...] = ()
    max_caption_length: int | None = None
    require_no_links_in_body: bool = True


@dataclass
class VoiceViolation:
    rule: str
    detail: str


@dataclass
class VoiceCheck:
    ok: bool
    violations: list[VoiceViolation] = field(default_factory=list)


def load_rules(brand_config: dict) -> VoiceRules:
    """Build `VoiceRules` from a brand's `voice` block."""
    v = (brand_config or {}).get("voice", {})
    return VoiceRules(
        max_emoji=int(v.get("max_emoji", 1)),
        banned_phrases=tuple(v.get("banned_phrases", ())),
        forbidden_echoes=tuple(v.get("forbidden_echoes", ())),
        max_caption_length=v.get("max_caption_length"),
        require_no_links_in_body=bool(v.get("require_no_links_in_body", True)),
    )


#: Emoji ranges, deliberately coarse. Counting precisely means a Unicode table; counting roughly is
#: enough to catch a caption that has drifted into decoration.
_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002190-\U000021FF]"
)
_URL_IN_TEXT = re.compile(r"https?://|www\.", re.IGNORECASE)


def check(post_text: str, rules: VoiceRules) -> VoiceCheck:
    """Validate a draft against the voice constraints.

    Runs after generation, not only in the prompt. A model told to be understated will drift; a
    validator will not.
    """
    violations: list[VoiceViolation] = []

    emoji = _EMOJI.findall(post_text)
    if len(emoji) > rules.max_emoji:
        violations.append(
            VoiceViolation("max_emoji", f"{len(emoji)} emoji, limit is {rules.max_emoji}")
        )

    if rules.require_no_links_in_body and _URL_IN_TEXT.search(post_text):
        violations.append(
            VoiceViolation(
                "no_links_in_body",
                "a link in the caption costs photo reach and burns Meta's monthly link allowance — "
                "it belongs in the first comment",
            )
        )

    lowered = post_text.lower()
    for phrase in rules.banned_phrases:
        if phrase.lower() in lowered:
            violations.append(VoiceViolation("banned_phrase", f"contains {phrase!r}"))

    for echo in rules.forbidden_echoes:
        if echo.lower() in lowered:
            violations.append(
                VoiceViolation("tagline_echo", f"repeats the card's own line {echo!r}")
            )

    if rules.max_caption_length and len(post_text) > rules.max_caption_length:
        violations.append(
            VoiceViolation(
                "length", f"{len(post_text)} chars, limit is {rules.max_caption_length}"
            )
        )

    return VoiceCheck(ok=not violations, violations=violations)
