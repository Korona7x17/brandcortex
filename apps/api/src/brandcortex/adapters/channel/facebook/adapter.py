"""Facebook channel adapter — channel #1 (spec §8).

Publishing is always: **photo post + caption, then immediately a comment carrying the canonical link.**

That shape is not a style choice. Photo posts out-reach link posts, and Meta is testing a ~2-links per
month cap on links in the post body unless the Page subscribes (~$15–500/mo) — comments are exempt from
the cap. Putting the link in the body would cost reach and burn a monthly allowance at the same time.

## App mode

Development mode grants these permissions in full to anyone holding a role on the app, acting on a Page
they administer. That is exactly this deployment's shape — one Page, owned by the app admin — so App
Review may never be on the critical path. Verify by publishing end to end in dev mode before spending
time on a review submission.

App Review and business verification only become gates when the app goes Live, i.e. acts for people
outside its own roles. Either way they attach to BrandCortex alone: the brand's own site carries no Meta
permissions.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from brandcortex.adapters.channel.facebook import tokens
from brandcortex.adapters.channel.facebook.client import GraphAuthError, GraphClient, GraphError
from brandcortex.config import get_settings
from brandcortex.db.models import BrandConfig
from brandcortex.db.session import session_scope
from brandcortex.schemas.draft import PublishRequest, PublishResult
from brandcortex.schemas.insights import InsightSnapshot
from brandcortex.services import assets

logger = logging.getLogger(__name__)


class CommentFailed(RuntimeError):
    """The photo published and the link comment did not.

    Carries the live post id, because the caller must record it: the photo is on the Page whatever
    happens next, and a post whose id we failed to store is one nobody can find to fix or delete.
    """

    def __init__(self, message: str, *, channel_post_id: str) -> None:
        super().__init__(message)
        self.channel_post_id = channel_post_id


class FacebookChannelAdapter:
    """Implements `ChannelAdapter` structurally; see `adapters/base.py`."""

    channel = "facebook"

    #: Verify against the pinned Graph version before any App Review submission — Meta's permission
    #: names and requirements shift between versions.
    REQUIRED_PERMISSIONS = (
        "pages_manage_posts",  # publish the photo
        "pages_manage_engagement",  # post the first comment — the link, so non-negotiable
        "pages_read_engagement",  # read the Page's own content back
        "pages_show_list",  # locate the Page and mint its token
        "read_insights",  # per-post reach/shares/saves — the Y side of the learning loop
    )

    #: Granted but unused. `business_management` covers Business-portfolio assets, which a single-tenant
    #: tool posting to one Page it administers has no need of; `public_profile` is granted to every app
    #: automatically. Listed so a permission audit can tell "deliberately unused" from "forgotten".
    UNUSED_PERMISSIONS = ("business_management", "public_profile")

    #: Wanted later, deliberately not requested yet — each widens any future App Review.
    #:   Page Mentions          -> tag a club or provincial team Page (`brand_config.tag_targets`, §6.5)
    #:   pages_read_user_content-> read follower comments  (Phase 3 inbox triage, §11)
    #:   pages_manage_metadata  -> webhook subscriptions   (Phase 3 inbox triage, §11)
    FUTURE_PERMISSIONS = ("pages_read_user_content", "pages_manage_metadata")

    def __init__(
        self,
        *,
        page_id: str | None = None,
        session_factory=session_scope,
        client_factory=None,
    ) -> None:
        settings = get_settings()
        self._page_id = page_id or settings.facebook_page_id or ""
        self._version = settings.facebook_graph_version
        self._app_secret = settings.facebook_app_secret
        self._session_factory = session_factory
        self._client_factory = client_factory

    def _client(self, session: Session) -> GraphClient:
        if self._client_factory is not None:
            return self._client_factory(session)
        token = tokens.get_page_token(session, self.brand_for(session), self._page_id)
        return GraphClient(token, version=self._version, app_secret=self._app_secret)

    @staticmethod
    def brand_for(session: Session) -> str:
        """Which brand owns the stored token.

        Single-tenant today, so this reads the one configured brand rather than inventing a mapping
        the system has no second case for. When brand #2 arrives it becomes a parameter, which is a
        smaller change than a tenancy layer nobody needs yet.
        """
        return session.scalars(select(BrandConfig.brand).order_by(BrandConfig.brand)).first() or ""

    def publish(self, request: PublishRequest) -> PublishResult:
        """Photo + caption, then immediately the first comment carrying the link.

        Two calls, one operation. The photo is uploaded as multipart `source` rather than handed to
        Meta as a URL: passing a URL would put the render timing in their hands, and the whole point
        of capturing at draft time is that the reviewer approved these exact bytes.

        A published photo whose comment failed raises `CommentFailed` carrying the live post id. It
        is not a partial success — the link is the entire reason the post exists — but the id still
        has to reach the caller, because the photo is on the Page either way.

        Native scheduling is deliberately not used. `published=false` + `scheduled_publish_time`
        would show the post in Business Suite, but the comment cannot be attached until the post
        exists, so the link would depend on a second job firing later. Publishing at the moment keeps
        the pair atomic.
        """
        with self._session_factory() as session:
            client = self._client(session)

            with assets.open_stored(request.asset_storage_key) as image:
                photo = client.post(
                    f"{self._page_id}/photos",
                    data={"caption": request.draft.post_text, "published": "true"},
                    files={"source": ("card.png", image, "image/png")},
                )

            # `post_id` is the Page-scoped id analytics needs; `id` alone is the photo object.
            post_id = photo.get("post_id") or photo.get("id")
            if not post_id:
                raise GraphError("photo published but Graph returned no id")

            try:
                comment = client.post(
                    f"{post_id}/comments", data={"message": request.draft.first_comment_text}
                )
            except (GraphError, GraphAuthError) as exc:
                raise CommentFailed(
                    f"photo {post_id} is live but its link comment failed: {exc}",
                    channel_post_id=str(post_id),
                ) from exc

            return PublishResult(
                channel_post_id=str(post_id),
                channel_comment_id=str(comment.get("id")) if comment.get("id") else None,
                published_at=datetime.now(UTC),
            )

    def fetch_insights(self, channel_post_id: str) -> InsightSnapshot:
        """Read this post's own insights (spec §9) and normalize into `InsightSnapshot`.

        Reading your own Page's data is fully supported; none of the feed-monitoring restrictions
        apply. Two calls, because Meta splits the numbers: reach and clicks live under `/insights`,
        while shares and comment counts are fields on the post object itself.

        The raw payload is kept whole. Meta renames insight metrics between Graph versions, and the
        raw copy is the only thing that makes an old snapshot recomputable after a rename.

        `saves` stays None on purpose. There is no reliable public Page-post metric for it, and a
        plausible-looking proxy would be worse than a gap: the learning loop would weight it.
        """
        with self._session_factory() as session:
            client = self._client(session)

            insights = client.get(
                f"{channel_post_id}/insights",
                {"metric": ",".join(INSIGHT_METRICS)},
            )
            post = client.get(
                channel_post_id,
                {"fields": "shares,comments.summary(true),created_time"},
            )

        values = _flatten(insights)
        reactions = values.get("post_reactions_by_type_total")
        return InsightSnapshot(
            channel_post_id=channel_post_id,
            captured_at=datetime.now(UTC),
            reach=_int(values.get("post_impressions_unique")),
            impressions=_int(values.get("post_impressions")),
            reactions=sum(reactions.values()) if isinstance(reactions, dict) else _int(reactions),
            comments=_int((post.get("comments") or {}).get("summary", {}).get("total_count")),
            shares=_int((post.get("shares") or {}).get("count")),
            saves=None,
            link_clicks=_int(values.get("post_clicks")),
            raw={"insights": insights, "post": post},
        )

    def health_check(self) -> bool:
        """Is the stored token valid, unexpired, and still carrying every permission we publish with?

        Checked before a scheduled run leans on it, so a revoked scope surfaces while someone is
        awake rather than when a post was due to go out.
        """
        return not self.health_problems()

    def health_problems(self) -> list[str]:
        """What is wrong with the token, in words. Empty when it is fine."""
        try:
            with self._session_factory() as session:
                brand = self.brand_for(session)
                if not self._page_id:
                    return ["FACEBOOK_PAGE_ID is not configured"]
                tokens.get_page_token(session, brand, self._page_id)
                client = self._client(session)
                debug = client.debug_token().get("data", {})
        except tokens.TokenMissing:
            return ["no Page token stored — authorize the Page"]
        except tokens.TokenExpired as exc:
            return [str(exc)]
        except GraphAuthError as exc:
            return [f"the Page token was rejected: {exc}"]
        except GraphError as exc:  # pragma: no cover - network-shaped
            return [f"could not reach Graph: {exc}"]

        problems: list[str] = []
        if not debug.get("is_valid", False):
            problems.append("Graph reports the token is not valid")
        granted = set(debug.get("scopes") or [])
        missing = [scope for scope in self.REQUIRED_PERMISSIONS if scope not in granted]
        if missing:
            problems.append("missing permissions: " + ", ".join(missing))
        expires = debug.get("expires_at")
        if expires:
            when = datetime.fromtimestamp(expires, UTC)
            if when <= datetime.now(UTC):
                problems.append(f"the token expired on {when:%Y-%m-%d}")
        return problems


#: What we ask Graph for. Names are version-specific — this list is pinned to the version in
#: settings, and the raw payload is stored so a rename does not orphan old snapshots.
INSIGHT_METRICS = (
    "post_impressions",
    "post_impressions_unique",
    "post_reactions_by_type_total",
    "post_clicks",
)


def _flatten(insights: dict) -> dict:
    """Graph returns a list of metrics each holding a list of periods. Take the first value of each."""
    out: dict = {}
    for row in insights.get("data") or []:
        values = row.get("values") or []
        if values:
            out[row.get("name")] = values[0].get("value")
    return out


def _int(value) -> int | None:
    """Missing stays missing. A metric coerced to zero is a claim that nothing happened."""
    if value is None or isinstance(value, dict):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
