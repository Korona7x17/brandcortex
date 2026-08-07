"""Copy captured cards from one asset store to another.

    uv run python -m brandcortex.services.migrate_assets --source /data/cards [--dry-run]

Written for one move in particular — the Railway volume to R2 — but it is not specific to it: the
source is any `ASSET_BUCKET`-shaped value and the destination is whatever this deployment is now
configured with. The key format is identical on both sides, so nothing is rewritten and no `posts`
row is touched. That is the whole reason this is a copy and not a migration.

**Order of operations.** Switch `ASSET_*` to the new bucket, redeploy, then run this with
`--source` pointing at the old one *while the volume is still mounted*. Between those two steps the
existing cards are unreadable, which is seconds of a dashboard thumbnail and no published post. The
reverse order is not available: the destination's credentials come from settings, and a deployment
only ever holds one set.

Only keys that `posts.asset_storage_key` actually names are copied. Orphans on the old volume are
captures whose draft was discarded, and carrying them into a bucket that costs money to hold is
paying to keep a mistake.

Safe to re-run: a key already present at the destination is verified by size and skipped. It reports
what it skipped rather than staying quiet, because "0 copied" reads as success and as never-ran.
"""

import argparse
import logging
import sys

from sqlalchemy import select

from brandcortex.db.models import Post
from brandcortex.db.session import session_scope
from brandcortex.services import assets

logger = logging.getLogger(__name__)


def referenced_keys() -> list[str]:
    """Every storage key a post still points at, oldest first, without duplicates."""
    with session_scope() as session:
        rows = session.scalars(
            select(Post.asset_storage_key)
            .where(Post.asset_storage_key.is_not(None))
            .order_by(Post.created_at)
        ).all()
    return list(dict.fromkeys(key for key in rows if key))


def copy_key(key: str, *, source: assets.ObjectStore, destination: assets.ObjectStore) -> str:
    """Copy one key. Returns the outcome: `copied`, `skipped`, `missing` or `mismatch`."""
    if not source.exists(key):
        # The post references bytes the old store does not have. Worth naming loudly: a published
        # post whose card is gone has lost its archive of what actually went out.
        return "missing"

    with source.open(key) as handle:
        data = handle.read()

    if destination.exists(key):
        with destination.open(key) as handle:
            existing = handle.read()
        # Same key, different bytes means two deployments wrote independently. Overwriting would
        # destroy one of them, and which one is not this script's call.
        return "skipped" if existing == data else "mismatch"

    content_type = "image/jpeg" if key.endswith((".jpg", ".jpeg")) else "image/png"
    destination.put(key, data, content_type=content_type)
    return "copied"


def run(*, source_bucket: str, dry_run: bool = False) -> dict[str, int]:
    source = assets.get_store(source_bucket)
    destination = assets.get_store()
    counts = {"copied": 0, "skipped": 0, "missing": 0, "mismatch": 0}

    keys = referenced_keys()
    logger.info("%s key(s) referenced by posts", len(keys))

    for key in keys:
        if dry_run:
            outcome = "copied" if not destination.exists(key) else "skipped"
        else:
            outcome = copy_key(key, source=source, destination=destination)
        counts[outcome] += 1
        level = logging.WARNING if outcome in ("missing", "mismatch") else logging.INFO
        logger.log(level, "%s %s", outcome, key)

    logger.info("asset migration%s: %s", " (dry run)" if dry_run else "", counts)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        required=True,
        help="the OLD ASSET_BUCKET — a path such as /data/cards, or a bucket name",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be copied without writing anything",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    counts = run(source_bucket=args.source, dry_run=args.dry_run)
    # A missing or mismatched key needs a person, so it must not exit 0 into a green deploy log.
    return 1 if counts["missing"] or counts["mismatch"] else 0


if __name__ == "__main__":
    sys.exit(main())
