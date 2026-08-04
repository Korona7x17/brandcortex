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

from brandcortex.schemas.draft import PublishRequest, PublishResult
from brandcortex.schemas.insights import InsightSnapshot


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

    def publish(self, request: PublishRequest) -> PublishResult:
        """POST /{page-id}/photos with the asset + caption, then POST /{post-id}/comments with the link.

        Scheduling uses the native mechanism: `published=false` + `scheduled_publish_time`. Note the
        first comment can only be attached once the post actually exists, so a natively scheduled post
        needs its comment posted at publish time by a follow-up job rather than up front.

        A published photo whose link comment failed is a broken post, not a partial success: report the
        failure and leave it recoverable, since the link is the entire point of the post.

        TODO(phase-1): implement via `client.GraphClient`, fetching the image through `services.assets`
        and the token from `channel_tokens`.
        """
        raise NotImplementedError

    def fetch_insights(self, channel_post_id: str) -> InsightSnapshot:
        """Read this post's own insights (spec §9) and normalize into `InsightSnapshot`.

        Reading your own Page's data is fully supported. Keep the raw payload — metric names change
        between Graph versions and the raw copy is what makes old snapshots recomputable.

        TODO(phase-2): implement alongside the insights fetcher worker.
        """
        raise NotImplementedError

    def health_check(self) -> bool:
        """Confirm the Page token is valid, unexpired, and still carries REQUIRED_PERMISSIONS."""
        raise NotImplementedError
