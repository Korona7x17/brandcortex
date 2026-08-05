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

from dataclasses import dataclass

from brandcortex.core.generation import claims, templates, voice
from brandcortex.core.generation.intro_rotation import pick_intro
from brandcortex.schemas.content_item import ContentItem
from brandcortex.schemas.draft import GeneratedDraft


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
    def __init__(self, brand_config: dict, playbook: dict | None = None) -> None:
        self._config = brand_config
        self._playbook = playbook or {}

    def draft_variants(
        self,
        item: ContentItem,
        *,
        channel: str,
        recent_intros: list[str] | None = None,
        link: str | None = None,
        limit: int = 6,
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
        fresh = [line for line in bank if line not in set(recent[:lookback])] or bank

        angles = templates.variants(
            item.source_type, locale, fallback_locale=self._config.get("default_locale")
        )[:limit]

        url = link or str(item.canonical_link)
        results: list[Variant] = []

        for index, (angle, renderer) in enumerate(angles):
            intro = ""
            if item.source_type == "swimmer" and fresh:
                intro = fresh[index % len(fresh)]
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
                    draft=GeneratedDraft(
                        post_text=caption,
                        first_comment_text=f"{comment_body}\n{url}" if comment_body else url,
                        intro_line=intro or None,
                        hook_style=hook,
                        hashtag_set=",".join(self._config.get("hashtags", {}).get("core", []))
                        or None,
                        playbook_versions={
                            k: v.get("version", 1) for k, v in self._playbook.items()
                        },
                    ),
                )
            )

        return results

    def _check(self, caption: str, facts: dict) -> list[str]:
        """The hard constraints, in one place so `draft` and `draft_variants` cannot diverge.

        Facts are passed in rather than held on the engine: one engine drafts many items, and a
        cached `self._facts` would check a caption against the previous card's numbers.
        """
        reasons: list[str] = []
        grounding = claims.check(caption, facts)
        if not grounding.ok:
            reasons.append(
                "numbers not supported by the card: " + ", ".join(grounding.unsupported)
            )
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

        grounding = claims.check(caption, item.facts)
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
