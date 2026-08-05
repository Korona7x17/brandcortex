"""Generation engine — content item + brand_config + playbook -> draft (spec §6).

Brand-voice aware, brand-agnostic in code. Everything specific — voice rules, the intro bank, hashtag
sets, unit labels, tag targets — is read from `brand_config`; everything learned is read from the active
`playbook`. The engine is playbook-aware from day one even while the playbook is empty, so switching the
learning loop on later changes behaviour without changing code.

Hard constraints the engine may not violate, whatever the playbook says:

* **Every number in the copy is grounded in `facts`** (`claims.check`). A caption claiming more than
  the card shows is a public assertion about a real person that the reader can check against the image
  in the same post. This is a computation, not a judgment, and it runs on every draft.
* The canonical link never appears in `post_text`. It goes in the first comment.
* The asset's own on-image tagline is never echoed in the copy.
* House voice is a fixed constraint, not an optimizable lever (spec §10.4).

The last three are style and structure; the first is factual grounding, which is why it lives in its own
module and no `brand_config` setting can switch it off.
"""

import logging
from dataclasses import dataclass

from brandcortex.core.generation import claims, templates, voice
from brandcortex.core.generation import writer as writer_module
from brandcortex.core.generation.intro_rotation import pick_intro
from brandcortex.schemas.content_item import ContentItem
from brandcortex.schemas.draft import GeneratedDraft

logger = logging.getLogger(__name__)


def _notation(config: dict) -> tuple[str, ...]:
    """The brand's fixed labels, longest first so a label is never partly matched.

    These carry digits that are not claims — `สระ 50 ม.` is the pool, not the swim.
    """
    labels: list[str] = []
    for key, value in (config.get("unit_labels") or {}).items():
        if key.startswith("_"):
            continue  # `_comment` keys explain the config; they are not notation
        if isinstance(value, str):
            labels.append(value)
        elif isinstance(value, dict):
            labels += [v for k, v in value.items() if isinstance(v, str) and not k.startswith("_")]
    return tuple(label for label in labels if any(ch.isdigit() for ch in label))


class DraftRejected(ValueError):
    """A draft that failed a hard constraint. Carries every reason, so review shows them together."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


@dataclass
class Variant:
    """One angle on the same facts, already checked.

    `rejected` variants are kept rather than dropped so the reason is visible: an angle that keeps
    failing the numeric check is a template bug, and silently offering five options instead of six
    is exactly how that stays unnoticed.
    """

    angle: str
    draft: GeneratedDraft | None
    hook_style: str | None = None
    rejected: list[str] | None = None
    source: str = "template"

    @property
    def ok(self) -> bool:
        return self.draft is not None


class GenerationEngine:
    def __init__(
        self,
        brand_config: dict,
        playbook: dict | None = None,
        *,
        writer: writer_module.Writer | None = None,
    ) -> None:
        self._config = brand_config
        self._playbook = playbook or {}
        self._writer = writer

    def draft_variants(
        self,
        item: ContentItem,
        *,
        channel: str,
        recent_intros: list[str] | None = None,
        link: str | None = None,
        limit: int = 6,
        nudge: str | None = None,
    ) -> list[Variant]:
        """Every angle registered for this structure, each independently checked.

        A reviewer is meant to choose, so the job here is to offer real alternatives and be honest
        about the ones that did not survive. An angle that does not fit the facts — a sweep for a
        swimmer with one gold — declines to render and is simply absent; an angle that renders but
        fails a hard check is returned with its reasons.

        Intros are dealt out so no two variants open the same way. Offering the same first line six
        times would make the choice look smaller than it is.
        """
        locale = item.locale
        bank = list(self._config.get("intro_bank", {}).get(locale, []))
        lookback = int(self._config.get("intro_lookback", 5))
        recent = recent_intros or []
        # Rotation is about not opening two consecutive *posts* the same way. Within one post the
        # variants must still differ from each other, so unused lines come first and the rest follow
        # rather than being excluded — otherwise a brand with a small bank offers six variants that
        # all open identically, which is the opposite of a choice.
        unused = [line for line in bank if line not in set(recent[:lookback])]
        pool = unused + [line for line in bank if line not in unused]

        url = link or str(item.canonical_link)
        results: list[Variant] = []

        written = self._write_with_model(item, locale=locale, nudge=nudge, limit=limit)
        if written:
            for angle, caption, comment_body in written:
                reasons = self._check(caption, item.facts)
                results.append(
                    Variant(
                        angle=angle,
                        source="model",
                        hook_style=angle,
                        draft=None if reasons else self._assemble(caption, comment_body, url),
                        rejected=reasons or None,
                    )
                )
            # Fall through to templates only when the model produced nothing usable at all. A model
            # that wrote five good captions and one that failed the numeric check is working; a model
            # whose every caption failed is not, and the queue should still get copy.
            if any(v.ok for v in results):
                return results
            results = []

        angles = templates.variants(
            item.source_type, locale, fallback_locale=self._config.get("default_locale")
        )[:limit]

        for index, (angle, renderer) in enumerate(angles):
            intro = ""
            if item.source_type == "swimmer" and pool:
                intro = pool[index % len(pool)]
            try:
                caption, comment_body, hook = renderer(
                    facts=item.facts, intro=intro, config=self._config
                )
            except ValueError as exc:
                # The angle does not fit these facts. Not offered, and not an error.
                results.append(Variant(angle=angle, draft=None, rejected=[str(exc)]))
                continue

            reasons = self._check(caption, item.facts)
            if reasons:
                results.append(Variant(angle=angle, draft=None, hook_style=hook, rejected=reasons))
                continue

            results.append(
                Variant(
                    angle=angle,
                    hook_style=hook,
                    draft=self._assemble(caption, comment_body, url, intro=intro, hook=hook),
                )
            )

        return results

    def _write_with_model(
        self, item: ContentItem, *, locale: str, nudge: str | None, limit: int
    ) -> list[tuple[str, str, str]]:
        """Candidates from the model, or an empty list when it is unavailable.

        Unavailable is not an error here. A missing key, an outage or a malformed answer should cost
        the brand its best copy for an hour, not its ability to draft at all — so every failure mode
        is logged and falls through to the templates below.
        """
        if self._writer is None:
            return []
        angles = writer_module.Angle.load(self._config)[:limit]
        if not angles:
            return []
        try:
            written = self._writer.write(
                facts=item.facts,
                config=self._config,
                angles=angles,
                locale=locale,
                nudge=nudge,
            )
        except writer_module.WriterUnavailable as exc:
            logger.info("model writer unavailable, falling back to templates: %s", exc)
            return []
        return [(w.angle, w.caption, w.comment_body) for w in written]

    def _assemble(
        self,
        caption: str,
        comment_body: str,
        url: str,
        *,
        intro: str | None = None,
        hook: str | None = None,
    ) -> GeneratedDraft:
        return GeneratedDraft(
            post_text=caption,
            first_comment_text=f"{comment_body}\n{url}" if comment_body else url,
            intro_line=intro or None,
            hook_style=hook,
            hashtag_set=",".join(self._config.get("hashtags", {}).get("core", [])) or None,
            playbook_versions={k: v.get("version", 1) for k, v in self._playbook.items()},
        )

    def _check(self, caption: str, facts: dict) -> list[str]:
        """The hard constraints, in one place so `draft` and `draft_variants` cannot diverge.

        Facts are passed in rather than held on the engine: one engine drafts many items, and a
        cached `self._facts` would check a caption against the previous card's numbers.
        """
        reasons: list[str] = []
        grounding = claims.check(caption, facts, notation=_notation(self._config))
        if not grounding.ok:
            reasons.append(
                "numbers not supported by the card: " + ", ".join(grounding.unsupported)
            )
        writer_cfg = self._config.get("writer") or {}
        for v in claims.check_bindings(caption, facts, writer_cfg.get("claim_bindings", [])):
            reasons.append(
                f"says {v.said} where the card's {v.fact} is {v.expected}"
            )
        for token in claims.check_notation(caption, writer_cfg.get("forbidden_notation", [])):
            reasons.append(f"uses {token!r}, which this brand has standardised away from")

        voice_result = voice.check(caption, voice.load_rules(self._config))
        if not voice_result.ok:
            reasons += [f"{v.rule}: {v.detail}" for v in voice_result.violations]
        return reasons

    def draft(
        self,
        item: ContentItem,
        *,
        channel: str,
        recent_intros: list[str] | None = None,
        link: str | None = None,
    ) -> GeneratedDraft:
        """Produce caption + first comment for one item on one channel.

        `link` is the UTM-tagged canonical link; when omitted the item's own link is used untagged,
        which is fine for previews but loses attribution on a real post.

        Both checks run before returning, and a failure raises rather than being quietly repaired. A
        caption the engine silently "fixed" hides that it invented a number in the first place — and
        that signal is worth more than the saved review click.
        """
        locale = item.locale
        lookback = int(self._config.get("intro_lookback", 5))
        bank = self._config.get("intro_bank", {}).get(locale, [])

        # Only structures that open with a rotating line need one; the event board does not.
        intro = ""
        if item.source_type == "swimmer" and bank:
            intro = pick_intro(bank=bank, recent=recent_intros or [], lookback=lookback)

        renderer = templates.get(
            item.source_type, locale, fallback_locale=self._config.get("default_locale")
        )
        caption, comment_body, hook = renderer(facts=item.facts, intro=intro, config=self._config)

        url = link or str(item.canonical_link)
        first_comment = f"{comment_body}\n{url}" if comment_body else url

        reasons: list[str] = []

        grounding = claims.check(caption, item.facts, notation=_notation(self._config))
        if not grounding.ok:
            reasons.append(
                "numbers not supported by the card: " + ", ".join(grounding.unsupported)
            )

        voice_result = voice.check(caption, voice.load_rules(self._config))
        if not voice_result.ok:
            reasons += [f"{v.rule}: {v.detail}" for v in voice_result.violations]

        if reasons:
            raise DraftRejected(reasons)

        return GeneratedDraft(
            post_text=caption,
            first_comment_text=first_comment,
            intro_line=intro or None,
            hook_style=hook,
            hashtag_set=",".join(self._config.get("hashtags", {}).get("core", [])) or None,
            playbook_versions={k: v.get("version", 1) for k, v in self._playbook.items()},
        )
