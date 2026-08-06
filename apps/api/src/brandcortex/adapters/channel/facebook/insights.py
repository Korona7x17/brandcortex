"""Mapping Graph insight payloads into the normalized `InsightSnapshot`.

Metric names are version-specific and Meta renames them; keep this mapping in one place and pin the
Graph version so a rename is a one-file fix rather than a hunt.

The mapping is also where the north-star discipline gets enforced downstream: `link_clicks` is recorded
but is *not* the traffic number. Real arrivals come from site analytics via UTM (`TrafficSnapshot`), and
the two will not match — the gap between them is the anti-reward-hacking cross-check (spec §10.4).
"""

from brandcortex.schemas.insights import InsightSnapshot

#: Graph metric name -> InsightSnapshot field. Verify against the pinned version on every upgrade.
METRIC_MAP: dict[str, str] = {
    "post_impressions_unique": "reach",
    "post_impressions": "impressions",
    "post_reactions_by_type_total": "reactions",
    "post_clicks_by_type": "link_clicks",
}


def to_snapshot(channel_post_id: str, payload: dict) -> InsightSnapshot:
    """Normalize a Graph insights payload, retaining the original in `raw`.

    **A metric absent from the payload must stay `None`.** Never default it to `0`. After a Meta rename
    the mapping silently misses, and a zero would tell the learning loop that every post since that date
    performed catastrophically — a fabricated collapse it would then confidently explain. `None` flows
    through to `outcomes.build_observations`, which excludes the post and counts the exclusion.

    TODO(phase-2): implement, including comments/shares/saves which come from separate edges rather
    than the insights edge.
    """
    raise NotImplementedError


def unmapped_metrics(payload: dict) -> list[str]:
    """Metric names present in the payload that `METRIC_MAP` doesn't know.

    The early warning for a Graph-version rename: a metric appearing here that used to map is a signal
    to update the map, before the drop rate in every comparison quietly climbs.
    """
    raise NotImplementedError
