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

from brandcortex.core.generation import claims, templates, voice
from brandcortex.core.generation.intro_rotation import pick_intro
from brandcortex.schemas.content_item import ContentItem
from brandcortex.schemas.draft import GeneratedDraft


class DraftRejected(ValueError):
    """A draft that failed a hard constraint. Carries every reason, so review shows them together."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


class GenerationEngine:
    def __init__(self, brand_config: dict, playbook: dict | None = None) -> None:
        self._config = brand_config
        self._playbook = playbook or {}

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
