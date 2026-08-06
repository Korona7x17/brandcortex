"""The end-to-end pipeline (spec §7).

    1. Brand renders content -> content item + asset written
    2. BrandCortex ingests (table-watch, or an admin "Queue to BrandCortex" flag)
    3. Generation engine drafts post + first comment, reading the playbook
    4. HUMAN REVIEW / approve / edit in the brandcortex.app UI
    5. Scheduler assigns a slot (alternation, spacing, preferred time)
    6. Channel adapter publishes (photo + caption)
    7. Adapter posts the first comment with the canonical link immediately
    8. Record channel_post_id, channel_comment_id, status -> published
    9. Insights fetcher snapshots performance over the next 24–48h

Step 4 is not optional in Phase 1. Human-in-the-loop first; full auto-publish only after the
generation engine has earned trust.

This module names no brand and no channel: it resolves adapters through the registry by the keys
stored on the post. That is what makes adding IG or brand #2 a config-and-adapter job.

## Two conventions worth knowing before reading further

**A rejected draft is data, not an exception.** The generation engine raises on a failed hard
constraint, and it should — silently repairing an invented number would hide that the engine invented
one. But ingest is a bulk operation over whatever the brand rendered today, and one bad row must not
stop the other forty. So ingest catches the rejection, writes a `failed` post carrying every reason,
and returns it. Nothing is repaired and nothing is hidden: the failure lands in the review queue,
where someone sees it. Single-post operations (`approve`, `publish`) raise instead, because there the
caller *is* the person waiting for an answer.

**Every method commits, including its failures.** A publish that fails must leave the post marked
`failed` even though the caller is about to see an exception — a caller who rolled back on that
exception would erase the only record of what happened.
"""

import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from brandcortex.adapters import registry
from brandcortex.config import get_settings
from brandcortex.core import brand_config as brand_config_store
from brandcortex.core.analytics import utm
from brandcortex.core.generation import claims, voice
from brandcortex.core.generation import writer as writer_module
from brandcortex.core.generation.engine import GenerationEngine
from brandcortex.core.learning import features as feature_capture
from brandcortex.core.learning import playbook
from brandcortex.db.models import IntroHistory, Post, PostFeatures, PostStatus, PostVariant
from brandcortex.schemas.content_item import AssetRef, ContentItem
from brandcortex.schemas.draft import GeneratedDraft, PublishRequest
from brandcortex.services import assets


class PostNotFound(LookupError):
    pass


class InvalidTransition(ValueError):
    """The post is not in a state this operation can act on."""


class EditRejected(ValueError):
    """A reviewer's edit failed a hard constraint. Carries every reason."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


class PublishFailed(RuntimeError):
    """Publishing did not complete. The post is left `failed` and recoverable."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


_URL = re.compile(r"https?://[^\s]+")


def _foreign_link_hosts(site_url: str, *texts: str | None) -> set[str]:
    """Hosts of any URL in `texts` that differ from the brand site's.

    Links are baked into a post at draft time from the then-current `BRAND_SITE_URL`, and nothing
    re-derives them later. A draft composed against a dev or staging environment therefore carries
    that environment's links for the rest of its life — and the first live post shipped
    `localhost:9000` in its comment before this check existed. Comparing hosts against the current
    setting catches exactly that drift without the core ever naming a brand's domain.
    """
    site_host = urlparse(site_url).netloc
    return {
        host
        for text in texts
        if text
        for host in (urlparse(match).netloc for match in _URL.findall(text))
        if host != site_host
    }


class Orchestrator:
    """Drives content through the pipeline against one database session.

    `capture` and `resolve_channel` are injected so the pipeline can be exercised end to end without
    a network. The seams are the whole point of the architecture, so they are also what makes it
    testable.
    """

    def __init__(
        self,
        session: Session,
        *,
        capture: Callable[..., str] | None = None,
        writer: writer_module.Writer | None = None,
        resolve_channel: Callable[[str], object] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        # Resolved here rather than as default arguments, which would bind at import time and put
        # the real network call out of reach of a test that patches the module afterwards.
        self._session = session
        self._capture = capture or assets.capture
        # Built once per orchestrator. Absent or unconfigured simply means the engine falls back to
        # templates, which is why nothing here raises when there is no API key.
        self._writer = writer or writer_module.from_settings(get_settings())
        self._resolve_channel = resolve_channel or registry.get_channel_adapter
        self._now = now or _utcnow

    # ------------------------------------------------------------------ steps 2–3

    def ingest(self, item: ContentItem, *, channel: str) -> Post:
        """Steps 2–3: persist a draft post, generate copy, capture the card, record features.

        Idempotent on `content_id` + channel — re-delivery from a source adapter returns the existing
        post untouched rather than drafting a second one. The database enforces that uniqueness too;
        this check is what makes re-delivery cheap rather than what makes it correct.

        Returns a post whose `status` may be `failed`. See the module docstring.
        """
        existing = self._session.scalar(
            select(Post).where(Post.content_id == item.content_id, Post.channel == channel)
        )
        if existing is not None:
            return existing

        config = brand_config_store.load(self._session, item.brand)

        post = Post(
            id=uuid.uuid4(),
            content_id=item.content_id,
            brand=item.brand,
            channel=channel,
            status=PostStatus.DRAFT,
            facts=dict(item.facts),
            canonical_link=str(item.canonical_link),
            source_generated_at=item.generated_at,
        )
        self._session.add(post)
        self._session.flush()  # the post id is what the campaign and the storage key are built from

        post.utm_campaign = utm.campaign_for_post(str(post.id), source_type=item.source_type)
        link = utm.tag_link(
            str(item.canonical_link),
            brand=item.brand,
            channel=channel,
            post_id=str(post.id),
            source_type=item.source_type,
        )

        engine = GenerationEngine(
            config, playbook.load_active(self._session, item.brand), writer=self._writer
        )
        try:
            variants = engine.draft_variants(
                item,
                channel=channel,
                recent_intros=self._recent_intros(item.brand, item.locale, config),
                link=link,
            )
        except LookupError as exc:
            # No template for this source type and locale — a configuration problem rather than a
            # bad card, but it is still this post that cannot be drafted.
            return self._fail(post, str(exc))

        offered = [v for v in variants if v.ok]
        if not offered:
            # Every angle failed. Record why each one did, not just the first — a template bug
            # usually shows up across several at once, and one reason hides that.
            reasons = [f"{v.angle}: {'; '.join(v.rejected or [])}" for v in variants]
            self._record_variants(post, variants, chosen=None)
            return self._fail(post, " | ".join(reasons) or "no caption could be written")

        draft = offered[0].draft
        post.post_text = post.generated_post_text = draft.post_text
        post.first_comment_text = post.generated_first_comment_text = draft.first_comment_text
        self._record_variants(post, variants, chosen=offered[0].angle)

        try:
            post.asset_storage_key = self._capture(item.asset, post_id=str(post.id))
        except Exception as exc:  # noqa: BLE001 — a failed capture means there is no image to ship
            return self._fail(post, f"card capture failed: {exc}")

        post.features = PostFeatures(
            **feature_capture.extract(
                item,
                draft,
                scheduled_for=None,
                timezone=config.get("timezone", "UTC"),
                tagged_partner=False,
            )
        )
        if draft.intro_line:
            self._session.add(
                IntroHistory(
                    id=uuid.uuid4(),
                    brand=item.brand,
                    source_type=item.source_type,
                    locale=item.locale,
                    intro_line=draft.intro_line,
                    used_at=self._now(),
                    post_id=post.id,
                )
            )

        self._session.commit()
        return post

    # ------------------------------------------------------------------ step 4

    def edit(
        self,
        post_id: uuid.UUID | str,
        *,
        post_text: str | None = None,
        first_comment_text: str | None = None,
    ) -> Post:
        """Apply a reviewer's edit, keeping the engine's original alongside it.

        The edit meets the same hard constraints the draft did. Not to second-guess the reviewer's
        judgment — the numbers and the link placement are not judgment. A caption asserting something
        the card does not show is wrong whoever typed it, and a link pasted into the body costs reach
        and burns a monthly allowance in a way that stays invisible until it has happened.

        Voice is checked too, and that one is closer to judgment, so it is worth being explicit: the
        rules are a ceiling on emoji and a list of phrases the brand has decided against, not a taste
        model. Getting past them is a deliberate `brand_config` change, which is the point.
        """
        post = self._get(post_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.APPROVED, PostStatus.FAILED):
            raise InvalidTransition(f"post {post.id} is {post.status} and can no longer be edited")

        caption = post_text if post_text is not None else (post.post_text or "")
        comment = (
            first_comment_text if first_comment_text is not None else (post.first_comment_text or "")
        )

        config = brand_config_store.load(self._session, post.brand)
        reasons: list[str] = []

        grounding = claims.check(caption, post.facts or {})
        if not grounding.ok:
            reasons.append("numbers not supported by the card: " + ", ".join(grounding.unsupported))

        voice_result = voice.check(caption, voice.load_rules(config))
        if not voice_result.ok:
            reasons += [f"{v.rule}: {v.detail}" for v in voice_result.violations]

        # Only meaningful once there is a comment to protect. A draft rejected before the engine
        # wrote one has nothing to strip — and it cannot reach `approve`, which requires a first
        # comment, so the guarantee still holds at the point where it matters.
        has_comment = bool(comment or post.first_comment_text)
        if post.utm_campaign and has_comment and utm.CAMPAIGN_PARAM not in comment:
            reasons.append(
                "first comment no longer carries the tagged link — without it this post's traffic "
                "is invisible to the north star"
            )

        if reasons:
            raise EditRejected(reasons)

        post.post_text = caption
        post.first_comment_text = comment
        if post.status is PostStatus.FAILED:
            # An edit is how a rejected draft gets fixed; it re-enters the queue as a normal draft.
            post.status = PostStatus.DRAFT
            post.error = None
        if post.features is not None:
            post.features.caption_length = len(caption)

        self._session.commit()
        return post

    def regenerate(self, post_id: uuid.UUID | str, *, nudge: str | None = None) -> Post:
        """Write a fresh set of angles for a post already in the queue.

        The reviewer's `nudge` steers this post only — "make it about her comeback", "shorter". It
        cannot loosen a hard rule: every candidate is checked afterwards exactly as before, so the
        nudge is direction, not permission.

        A human edit is deliberately not preserved. Regenerating is asking for different copy, and
        silently merging an old edit into new text would produce something nobody wrote.
        """
        post = self._get(post_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.FAILED, PostStatus.APPROVED):
            raise InvalidTransition(f"post {post.id} is {post.status} and can no longer be redrafted")

        config = brand_config_store.load(self._session, post.brand)
        item = self._item_from(post, config)

        engine = GenerationEngine(
            config, playbook.load_active(self._session, post.brand), writer=self._writer
        )
        variants = engine.draft_variants(
            item,
            channel=post.channel,
            recent_intros=self._recent_intros(post.brand, item.locale, config),
            # Rebuilt rather than parsed back out of the old comment: tagging is deterministic, so
            # the campaign is the same one and a redraft never splits a post's attribution.
            link=utm.tag_link(
                post.canonical_link or "",
                brand=post.brand,
                channel=post.channel,
                post_id=str(post.id),
                source_type=(post.features.source_type if post.features else "") or "",
            )
            if post.canonical_link
            else None,
            nudge=nudge,
        )
        offered = [v for v in variants if v.ok]
        if not offered:
            reasons = [f"{v.angle}: {'; '.join(v.rejected or [])}" for v in variants]
            self._record_variants(post, variants, chosen=None)
            return self._fail(post, " | ".join(reasons) or "no caption could be written")

        chosen = offered[0]
        post.post_text = post.generated_post_text = chosen.draft.post_text
        post.first_comment_text = post.generated_first_comment_text = chosen.draft.first_comment_text
        post.status = PostStatus.DRAFT
        post.error = None
        self._record_variants(post, variants, chosen=chosen.angle)
        if post.features is not None:
            post.features.hook_style = chosen.hook_style
            post.features.intro_line = chosen.draft.intro_line
            post.features.caption_length = len(chosen.draft.post_text)

        self._session.commit()
        return post

    def _item_from(self, post: Post, config: dict) -> ContentItem:
        """Rebuild the envelope from what the post froze at draft time.

        Deliberately not re-fetched from the brand: the caption must describe the image that was
        captured, and the brand's live data may have moved since.
        """
        return ContentItem(
            content_id=post.content_id,
            brand=post.brand,
            source_type=(post.features.source_type if post.features else "") or "",
            locale=(post.features.locale if post.features else None)
            or config.get("default_locale", "th"),
            asset={"kind": "image", "storage_key": post.asset_storage_key},
            canonical_link=post.canonical_link,
            facts=post.facts or {},
            generated_at=post.source_generated_at or post.created_at,
        )

    def choose_variant(self, post_id: uuid.UUID | str, angle: str) -> Post:
        """Adopt one of the offered angles as the post's copy.

        Recorded rather than merely applied: which framing a reviewer picks over the alternatives is
        a cleaner signal than an edit, and `hook_style` is a lever the learning loop may tune. The
        engine's original stays untouched in `generated_post_text`, so switching angles is not
        mistaken for a human rewrite.
        """
        post = self._get(post_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.APPROVED, PostStatus.FAILED):
            raise InvalidTransition(f"post {post.id} is {post.status} and can no longer be changed")

        chosen = next((v for v in post.variants if v.angle == angle), None)
        if chosen is None:
            offered = sorted(v.angle for v in post.variants if v.post_text)
            raise PostNotFound(f"post {post.id} has no variant {angle!r}; offered: {offered}")
        if not chosen.post_text:
            raise InvalidTransition(
                f"variant {angle!r} was not offered: {'; '.join(chosen.rejected or [])}"
            )

        now = self._now()
        for variant in post.variants:
            variant.chosen_at = now if variant is chosen else None

        post.post_text = chosen.post_text
        post.first_comment_text = chosen.first_comment_text
        if post.status is PostStatus.FAILED:
            post.status = PostStatus.DRAFT
            post.error = None
        if post.features is not None:
            post.features.hook_style = chosen.hook_style
            post.features.intro_line = chosen.intro_line
            post.features.caption_length = len(chosen.post_text)

        self._session.commit()
        return post

    def approve(self, post_id: uuid.UUID | str, *, edited_text: str | None = None) -> Post:
        """Step 4: clear a draft for publishing, keeping any human edit.

        `edited_text` is applied through `edit`, so it meets the same constraints. An approval path
        that skipped them would be the way every check in this file eventually gets bypassed.
        """
        if edited_text is not None:
            self.edit(post_id, post_text=edited_text)

        post = self._get(post_id)
        if post.status is PostStatus.APPROVED:
            return post
        if post.status is not PostStatus.DRAFT:
            raise InvalidTransition(
                f"post {post.id} is {post.status}, not a draft awaiting approval"
            )
        if not (post.post_text and post.first_comment_text and post.asset_storage_key):
            raise InvalidTransition(
                f"post {post.id} is missing caption, first comment or captured card"
            )

        post.status = PostStatus.APPROVED
        post.approved_at = self._now()
        self._session.commit()
        return post

    # ------------------------------------------------------------------ step 5

    def schedule(self, post_id: uuid.UUID | str, when: datetime) -> Post:
        """Step 5: assign a slot.

        Phase 1 takes the time from the caller; the slot *algorithm* — alternation, spacing,
        preferred windows — is `core.scheduling` and Phase 2. Open decision #5 (schedule always, or
        publish on approval) resolves either way against this method.
        """
        post = self._get(post_id)
        if post.status not in (PostStatus.APPROVED, PostStatus.SCHEDULED):
            raise InvalidTransition(f"post {post.id} is {post.status}; approve it before scheduling")

        config = brand_config_store.load(self._session, post.brand)
        post.scheduled_for = when
        post.status = PostStatus.SCHEDULED
        self._apply_timing(post, when, config)
        self._session.commit()
        return post

    # ------------------------------------------------------------------ steps 6–8

    def publish(self, post_id: uuid.UUID | str) -> Post:
        """Steps 6–8: publish the photo, then the first comment, then record both channel ids.

        The comment is part of the operation, not a follow-up: a post whose link comment failed is
        broken, since the link is the entire reason the post exists. Such a post is left `failed` and
        recoverable rather than reported as a partial success.
        """
        post = self._get(post_id)
        if post.status is PostStatus.PUBLISHED:
            return post
        if post.status not in (PostStatus.APPROVED, PostStatus.SCHEDULED):
            raise InvalidTransition(
                f"post {post.id} is {post.status}; only an approved or scheduled post may publish"
            )
        if not (post.post_text and post.first_comment_text and post.asset_storage_key):
            raise InvalidTransition(
                f"post {post.id} is missing caption, first comment or captured card"
            )
        stale = _foreign_link_hosts(
            get_settings().brand_site_url, post.canonical_link, post.first_comment_text
        )
        if stale:
            raise InvalidTransition(
                f"post {post.id} carries links on {sorted(stale)} but the brand site is"
                f" {get_settings().brand_site_url}; links are baked at draft time, so a draft"
                " composed against another environment must be regenerated, not published"
            )

        config = brand_config_store.load(self._session, post.brand)
        adapter = self._resolve_channel(post.channel)
        request = PublishRequest(
            brand=post.brand,
            asset_storage_key=post.asset_storage_key,
            draft=GeneratedDraft(
                post_text=post.post_text,
                first_comment_text=post.first_comment_text,
                intro_line=post.features.intro_line if post.features else None,
                hook_style=post.features.hook_style if post.features else None,
                hashtag_set=post.features.hashtag_set if post.features else None,
            ),
            scheduled_for=post.scheduled_for if post.status is PostStatus.SCHEDULED else None,
        )

        try:
            result = adapter.publish(request)
        except Exception as exc:  # noqa: BLE001 — every channel failure mode ends the same way here
            # An adapter may know the photo went live even though the operation failed. Recording
            # that id is what makes the post recoverable instead of merely lost: without it nobody
            # can find the card on the Page to add the comment or take it down.
            live_id = getattr(exc, "channel_post_id", None)
            if live_id:
                post.channel_post_id = str(live_id)
            self._fail(post, f"publish failed: {exc}")
            raise PublishFailed(f"post {post.id} failed to publish: {exc}") from exc

        if not result.channel_comment_id and request.scheduled_for is None:  # noqa: SIM102
            # The photo may well be live. Recording success anyway would be worse than recording
            # nothing: a published card with no link cost reach and returns no traffic, and it would
            # then sit in the analytics as a content failure rather than a delivery one.
            self._fail(
                post,
                f"published as {result.channel_post_id} but the first comment did not land — the "
                "link is missing from a live post",
            )
            raise PublishFailed(f"post {post.id} published without its link comment")

        post.channel_post_id = result.channel_post_id
        post.channel_comment_id = result.channel_comment_id
        post.published_at = result.published_at or self._now()
        post.status = PostStatus.PUBLISHED
        post.error = None
        self._apply_timing(post, post.published_at, config)
        self._session.commit()
        return post

    # ------------------------------------------------------------------ internals

    def _get(self, post_id: uuid.UUID | str) -> Post:
        key = post_id if isinstance(post_id, uuid.UUID) else uuid.UUID(str(post_id))
        post = self._session.get(Post, key)
        if post is None:
            raise PostNotFound(f"no post {post_id}")
        return post

    def _record_variants(self, post: Post, variants: list, chosen: str | None) -> None:
        """Persist every angle, offered or not, with the reason when not.

        The old set is deleted and flushed before the new one is inserted. Assigning straight over
        the collection makes SQLAlchemy insert first and delete after, which collides with the
        unique constraint on (post_id, angle) the moment a post is regenerated.
        """
        now = self._now()
        if post.variants:
            post.variants.clear()
            self._session.flush()
        post.variants = [
            PostVariant(
                id=uuid.uuid4(),
                angle=v.angle,
                position=index,
                post_text=v.draft.post_text if v.ok else None,
                first_comment_text=v.draft.first_comment_text if v.ok else None,
                intro_line=v.draft.intro_line if v.ok else None,
                hook_style=v.hook_style,
                origin=v.source,
                rejected=list(v.rejected or []),
                chosen_at=now if v.angle == chosen else None,
            )
            for index, v in enumerate(variants)
        ]

    def _fail(self, post: Post, error: str) -> Post:
        post.status = PostStatus.FAILED
        post.error = error
        self._session.commit()
        return post

    def _apply_timing(self, post: Post, at: datetime | None, config: dict) -> None:
        """Keep the timing features describing when the post actually goes out.

        Captured at draft time they would describe when someone happened to click Download, which is
        a fact about the operator's afternoon rather than about the audience.
        """
        if post.features is None:
            return
        timing = feature_capture.timing(at, timezone=config.get("timezone", "UTC"))
        post.features.post_hour = timing["post_hour"]
        post.features.post_weekday = timing["post_weekday"]

    def _recent_intros(self, brand: str, locale: str, config: dict) -> list[str]:
        """Intro lines used most recently first, for the no-repeat rotation."""
        lookback = int(config.get("intro_lookback", 5))
        rows = self._session.scalars(
            select(IntroHistory)
            .where(IntroHistory.brand == brand, IntroHistory.locale == locale)
            .order_by(IntroHistory.used_at.desc())
            .limit(lookback)
        ).all()
        return [row.intro_line for row in rows]


def asset_ref(post: Post) -> AssetRef:
    """The stored capture as an `AssetRef`. What publishes is these bytes, never a live URL."""
    if not post.asset_storage_key:
        raise ValueError(f"post {post.id} has no captured card")
    return AssetRef(storage_key=post.asset_storage_key)
