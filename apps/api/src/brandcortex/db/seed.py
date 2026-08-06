"""Load a brand's configuration document into the database.

    uv run python -m brandcortex.db.seed seeds/thaiswim.brand_config.json

The seed files under `seeds/` are the reviewed source of a brand's voice, intro bank, hashtags and
north-star weighting. They live in git because those are decisions, not data — a change to the voice
rules should show up in a diff with a reason attached, not as an UPDATE nobody can date.

Re-running is safe: `brand_config.save` replaces the row wholesale, so the file stays authoritative.
That is also why it replaces rather than merges — a config is reviewed as a whole document, and a
partial write is how a voice rule goes missing without anyone deciding to remove it.
"""

import argparse
import json
import sys
from pathlib import Path

from brandcortex.core import brand_config as brand_config_store
from brandcortex.db.session import session_scope


def load_document(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if "brand" not in document:
        raise ValueError(f"{path} has no `brand` key; it cannot be keyed into brand_config")
    return document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load brand config documents into the database.")
    parser.add_argument("files", nargs="+", type=Path, help="brand config JSON documents")
    args = parser.parse_args(argv)

    with session_scope() as session:
        for path in args.files:
            document = load_document(path)
            brand_config_store.save(session, document)
            print(f"seeded brand_config for {document['brand']} from {path}")
        session.commit()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
