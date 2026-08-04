"""Content-opportunity scanner (spec §10.2).

The part of the loop that turns data into *new posts* rather than only tuning existing ones. It reads
the brand's data for high-shareability items that have not been posted yet — big margins, all-stroke
sweeps, milestone national-#1 counts — and queues them proactively.

Without this, the system can only improve how it posts what a human happened to make. With it, the
system finds the thing worth posting.

Ranking is brand-agnostic: it sorts on `wow_factor`, which the source adapter computed because judging
what is remarkable requires knowing the domain. The core stays out of that judgement.
"""

from brandcortex.schemas.content_item import ContentItem


def scan(brand: str, *, limit: int = 10) -> list[ContentItem]:
    """Return unposted, high-`wow_factor` items worth queueing.

    "Not yet posted" is determined from BrandCortex's own `posts` table — never from a flag in the
    brand DB, which we do not write.

    TODO(phase-2): implement over the source adapter's `fetch`, since a worthwhile item may not have a
    rendered card yet and will need one produced on demand.
    """
    raise NotImplementedError
