"""UTM tagging — how the north star becomes measurable (spec §9).

Every canonical link is tagged before it goes into the first comment. This is the only way to know
real traffic: the channel's link-click number is not the site's truth, and the link lives in a comment
rather than the post, so nothing in the channel's own reporting maps cleanly to arrivals.

The campaign parameter must be unique per post and reversible back to a post id, since that join is
what turns site analytics into per-post attribution.

Site analytics is the source of truth for traffic. The two numbers will not match, by design; the gap
between them is itself the anti-reward-hacking signal (§10.4).

## Why the campaign is short

The obvious way to make a campaign reversible is to embed the whole post id. That works, and it puts
a 32-character hex string in a URL that a reader sees in full, because a channel comment renders the
link as plain text. A Page whose every link ends in a wall of hex reads as tooling, which cuts against
the one voice rule this whole system is built to protect.

So the campaign is `{source_type}-{first 8 hex of the post id}` — short enough to sit quietly in a
comment, readable in an analytics dashboard, and reversed by an exact lookup against
`posts.utm_campaign` rather than by parsing. That column carries a unique index, so a collision is a
write error at draft time instead of two posts silently sharing attribution.
"""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

#: Constant across channels. `utm_source` carries which channel; medium describes the kind of place,
#: and every channel this system will publish to is social.
MEDIUM = "social"

CAMPAIGN_PARAM = "utm_campaign"


def campaign_for_post(post_id: str, *, source_type: str) -> str:
    """Deterministic campaign identifier for a post.

    Reversed by looking the value up in `posts.utm_campaign`, not by parsing it — see the module
    docstring. Deterministic so that re-tagging during a redraft produces the same campaign rather
    than splitting one post's traffic across two rows.
    """
    compact = post_id.replace("-", "")
    if len(compact) < 8:
        raise ValueError(f"post id {post_id!r} is too short to derive a campaign from")
    return f"{source_type}-{compact[:8]}"


def tag_link(url: str, *, brand: str, channel: str, post_id: str, source_type: str) -> str:
    """Append UTM parameters to a canonical link.

    Preserves any query string already on the URL — event links carry the whole ranking bucket in
    theirs, so dropping it would point the reader at a different board than the card shows.

    Idempotent: a URL that already carries a campaign comes back unchanged. Tagging twice would
    otherwise leave two campaign values on one link, and which one analytics reports would be a
    property of the query parser rather than of this system.
    """
    parts = urlparse(url)
    existing = parse_qsl(parts.query, keep_blank_values=True)
    if any(key == CAMPAIGN_PARAM for key, _ in existing):
        return url

    tagged = existing + [
        ("utm_source", channel),
        ("utm_medium", MEDIUM),
        (CAMPAIGN_PARAM, campaign_for_post(post_id, source_type=source_type)),
    ]
    return urlunparse(parts._replace(query=urlencode(tagged)))


def campaign_of(url: str) -> str | None:
    """Read the campaign back off a tagged link. Used when reconciling a published comment."""
    for key, value in parse_qsl(urlparse(url).query, keep_blank_values=True):
        if key == CAMPAIGN_PARAM:
            return value
    return None
