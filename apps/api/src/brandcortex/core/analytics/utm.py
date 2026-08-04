"""UTM tagging — how the north star becomes measurable (spec §9).

Every canonical link is tagged before it goes into the first comment. This is the only way to know real
traffic: the channel's link-click number is not the site's truth, and the link lives in a comment rather
than the post, so nothing in the channel's own reporting maps cleanly to arrivals.

The campaign parameter must be unique per post and reversible back to a post id, since that join is what
turns site analytics into per-post attribution.

Site analytics is the source of truth for traffic. The two numbers will not match, by design; the gap
between them is itself the anti-reward-hacking signal (§10.4).
"""


def tag_link(url: str, *, brand: str, channel: str, post_id: str, source_type: str) -> str:
    """Append UTM parameters to a canonical link.

    Preserves any query string already on the URL, and must be idempotent — tagging an already-tagged
    link twice would corrupt attribution.

    TODO(phase-2): implement, keeping `utm_campaign` reversible to `post_id`.
    """
    raise NotImplementedError


def campaign_for_post(post_id: str) -> str:
    """Deterministic campaign identifier for a post. TODO(phase-2)."""
    raise NotImplementedError
