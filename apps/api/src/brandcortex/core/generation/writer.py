"""Writing captions with a model (spec §6).

The engine asks a `Writer` for candidate captions; a `Writer` knows nothing about brands, channels
or swimming. Two implementations: this one calls a model, and the template registry is the fallback.

## Why a model belongs here and not in the learning loop

CLAUDE.md's rule is that nothing grades its own work, and it names the caption path as the place
*not* to add a reviewing agent. That is not an exception to the rule, it is the rule applied: the
checks that matter here are computations, and a person reads the output before it ships.

    claims.check   every number in the caption exists in `facts` — arithmetic, not opinion
    voice.check    emoji ceiling, banned phrasings, no link in the body
    the reviewer   picks one of six and can edit it

So the model writes and is checked; it is never asked whether its own caption is good. A rejected
caption is dropped with its reason, never repaired — repairing would hide that it was invented.

## What the model is given, and what it is not

Given: the card's facts, the brand's voice rules, the brand's own example captions, and one
instruction per angle. Not given: anything from the channel, any performance data, any freedom over
voice. The voice rules go in the prompt *and* are enforced afterwards, because a model told to be
understated will drift and a validator will not.

Examples do most of the work. A brand's voice is far better conveyed by five captions its owner
wrote than by any description of a tone — particularly when the copy is Thai and the description
would be in English.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)

DEFAULT_MAX_VARIANTS = 6


@dataclass(frozen=True)
class Angle:
    """One framing to write toward. Data, not code — brands edit these."""

    key: str
    instruction: str

    @staticmethod
    def load(config: dict[str, Any]) -> list["Angle"]:
        raw = (config.get("writer") or {}).get("angles") or []
        return [
            Angle(key=a["key"], instruction=a["instruction"])
            for a in raw
            if a.get("key") and a.get("instruction")
        ]


@dataclass
class Written:
    """One candidate, before any check has run."""

    angle: str
    caption: str
    comment_body: str = ""


class WriterUnavailable(RuntimeError):
    """The model could not be reached or is not configured. Callers fall back to templates."""


class Writer(Protocol):
    def write(
        self,
        *,
        facts: dict[str, Any],
        config: dict[str, Any],
        angles: list[Angle],
        locale: str,
        nudge: str | None = None,
    ) -> list[Written]: ...


SYSTEM = """You write social captions for a brand, in the brand's own voice.

Hard rules. These are checked mechanically after you answer, and a caption that breaks one is thrown
away rather than corrected:

1. Every number you write MUST appear in the FACTS given to you. Never compute, estimate, round or
   infer a figure. If a number is not in FACTS, do not use it.
2. Never put a URL or a link in the caption. The link goes in a separate first comment.
3. Respect the voice rules exactly, including the emoji ceiling.
4. Write in the requested locale. Copy in that language is first-class, not a translation.

Style. Understated, factual, warm. Recognition, not advertising. No superlative drumroll, no stacked
emoji, no cheesy lines. Let the facts speak. When in doubt, say less.

You will be given several ANGLES. Write one caption per angle. They must differ in what they notice,
not merely in wording — two captions that say the same thing with different openings are one caption.

Answer with JSON only: {"captions": [{"angle": "<key>", "caption": "...", "comment_body": "..."}]}
`comment_body` is a short line introducing the link; it may be empty."""


class AnthropicWriter:
    """Writes candidates with a Claude model.

    One request for all angles rather than one per angle: it costs less, and it lets the model see
    its own alternatives so they come back genuinely different instead of six paraphrases.
    """

    def __init__(self, *, api_key: str | None, model: str, max_tokens: int = 4096) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def write(
        self,
        *,
        facts: dict[str, Any],
        config: dict[str, Any],
        angles: list[Angle],
        locale: str,
        nudge: str | None = None,
    ) -> list[Written]:
        if not self._api_key:
            raise WriterUnavailable("ANTHROPIC_API_KEY is not configured")
        if not angles:
            raise WriterUnavailable("no angles configured for this brand")

        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise WriterUnavailable("the anthropic package is not installed") from exc

        client = anthropic.Anthropic(api_key=self._api_key)
        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=_system_prompt(config),
                messages=[{"role": "user", "content": _user_prompt(facts, angles, locale, nudge)}],
            )
        except Exception as exc:  # noqa: BLE001 — every failure mode ends as a fallback to templates
            raise WriterUnavailable(f"model request failed: {exc}") from exc

        text = "".join(block.text for block in response.content if block.type == "text")
        return _parse(text, angles)


def _system_prompt(config: dict[str, Any]) -> str:
    """The brand's brief, appended to the fixed rules.

    Everything below the fixed rules is editable by the brand. Nothing editable can remove a hard
    rule — those are enforced after the model answers, so the prompt is guidance and the validator is
    the guarantee.
    """
    voice = config.get("voice") or {}
    writer = config.get("writer") or {}
    parts = [SYSTEM, "", "BRAND VOICE RULES:"]

    parts.append(f"- At most {voice.get('max_emoji', 1)} emoji per caption.")
    if voice.get("banned_phrases"):
        parts.append("- Never use these phrasings: " + "; ".join(voice["banned_phrases"]))
    if voice.get("forbidden_echoes"):
        parts.append(
            "- Never repeat the card's own on-image lines: " + "; ".join(voice["forbidden_echoes"])
        )
    if voice.get("max_caption_length"):
        parts.append(f"- Keep captions under {voice['max_caption_length']} characters.")

    # Notation is a lookup, not a judgment. The card engines render one form; a caption using
    # another disagrees with the image in the same post. It goes in the prompt so the model writes it
    # correctly, and `claims.check` rejects the alternatives so it is not left to hope.
    units = config.get("unit_labels") or {}
    vocabulary = [f"{k}: {v}" for k, v in units.items() if isinstance(v, str) and not k.startswith("_")]
    vocabulary += [
        f"{k}: {v}"
        for group in units.values()
        if isinstance(group, dict)
        for k, v in group.items()
        if not k.startswith("_")
    ]
    if vocabulary:
        parts += [
            "",
            "REQUIRED NOTATION — write these exactly, never a synonym, never the raw code:",
            *[f"- {v}" for v in vocabulary],
        ]

    if writer.get("guidance"):
        parts += ["", "BRAND GUIDANCE:", writer["guidance"]]

    examples = writer.get("examples") or []
    if examples:
        parts += ["", "CAPTIONS THIS BRAND HAS APPROVED — match this register:"]
        parts += [f"---\n{example}" for example in examples]

    hashtags = (config.get("hashtags") or {}).get("core") or []
    if hashtags:
        parts += ["", f"End every caption with these hashtags on one line: {' '.join(hashtags)}"]

    return "\n".join(parts)


def _user_prompt(
    facts: dict[str, Any], angles: list[Angle], locale: str, nudge: str | None
) -> str:
    lines = [
        f"LOCALE: {locale}",
        "",
        "FACTS (the card displays exactly these — every number you write must be here):",
        json.dumps(facts, ensure_ascii=False, indent=2),
        "",
        "ANGLES — one caption each:",
    ]
    lines += [f"- {a.key}: {a.instruction}" for a in angles]
    if nudge:
        # The reviewer's steer for this post only. It cannot loosen a hard rule; those are checked
        # after the fact regardless of what anyone asks for.
        lines += ["", f"ADDITIONAL DIRECTION FOR THIS POST: {nudge}"]
    return "\n".join(lines)


def _parse(text: str, angles: list[Angle]) -> list[Written]:
    """Read the model's JSON, tolerating a code fence.

    Unknown angle keys are dropped rather than guessed at: a caption whose framing we cannot name is
    a caption the learning loop cannot attribute, which makes it worth less than the slot it fills.
    """
    body = text.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[-1].rsplit("```", 1)[0]

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise WriterUnavailable(f"model did not return JSON: {exc}") from exc

    known = {a.key for a in angles}
    written: list[Written] = []
    for row in payload.get("captions", []):
        angle = row.get("angle")
        caption = (row.get("caption") or "").strip()
        if not caption:
            continue
        if angle not in known:
            logger.warning("model returned unknown angle %r; dropping", angle)
            continue
        written.append(
            Written(angle=angle, caption=caption, comment_body=(row.get("comment_body") or "").strip())
        )
    return written


def from_settings(settings: Any) -> AnthropicWriter:
    return AnthropicWriter(
        api_key=getattr(settings, "anthropic_api_key", None),
        model=getattr(settings, "generation_model", "claude-sonnet-5"),
    )
