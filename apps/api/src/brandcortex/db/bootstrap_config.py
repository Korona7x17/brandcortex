"""Apply `seeds/*.brand_config.json` at start-up, without ever clobbering an operator's edits.

## Why this exists

A brand's voice lives in two places that look like one: the reviewed JSON document in git, and the
`brand_config` row the engine actually reads. The file is the source; the row is the authority, because
`/settings/voice` writes to the row. Nothing connected them, so a voice change shipped as a commit
changed nothing in production until somebody remembered to run the seed loader by hand.

On 2026-08-06 nobody did, for several hours, across several deploys. The symptom was a rule that was
present in the code, present in the file, passing its tests, and absent from every post the product
made — which is the worst shape a bug can take, because everything you look at says it is fixed.

## The rule

Seeding on boot is only safe if it can tell these two apart:

* the **file** changed (a reviewed commit) -> apply it, that is the whole point;
* the **row** changed (someone edited the voice in the app) -> leave it alone, that edit is the
  authority and silently reverting it on the next deploy would be worse than the drift.

So each seeded row records a fingerprint of the document it was written from. At boot:

    file unchanged since the last seed          -> nothing to do
    file changed, row still matches its seed    -> apply; the row was never hand-edited
    unstamped row, applying would change nothing-> adopt it and stamp it
    file changed, row no longer matches         -> REFUSE, and log both fingerprints

The last case is a genuine conflict — a reviewed change and a live edit, both wanting the same field —
and a machine picking a winner is exactly how someone's tuning disappears without a trace. It stays
for a human, and `db.seed` can still force it.

The adopt case exists because of what production actually looked like the first time this ran. Its
row had been seeded by hand minutes earlier, so it carried no stamp — and refusing an unstamped row
outright is caution with no object when the row already holds exactly what the file says. It would
have meant boot-seeding sat inert until someone ran the manual command it was built to replace. The
deployment log read `file=34b942d201fc row=34b942d201fc expected=(none)`: identical content, refused
on provenance alone.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from brandcortex.core import brand_config as store
from brandcortex.db.models import BrandConfig

logger = logging.getLogger(__name__)

#: Where the applied-document fingerprint rides. Inside `settings`, so it round-trips with the
#: `_comment` keys and needs no migration.
STAMP_KEY = "_seeded_from"


def fingerprint(document: dict[str, Any]) -> str:
    """A stable hash of a config document, ignoring the stamp itself.

    Sorted keys and compact separators so formatting changes — a reindented seed file, a key moved —
    are not mistaken for a change of meaning.
    """
    payload = {k: v for k, v in document.items() if k != STAMP_KEY}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def write_stamped(session: Session, document: dict[str, Any], file_hash: str) -> BrandConfig:
    """Save the document and stamp it with **two** fingerprints.

    Two, not one, because a row does not round-trip to the file that made it: `to_document` returns
    every column, including defaults (`timezone`, `intro_bank`, `unit_labels`…) that a seed file may
    never mention. Comparing a row against its file's hash therefore always differs, which would make
    every untouched row look hand-edited and every reviewed change get refused — the very bug this
    module exists to close, reintroduced one layer down. A test caught it; the logic alone read fine.

        file_sha256   the seed document -> "has the file changed since we applied it?"
        row_sha256    the row as stored -> "has anyone written to this row since we wrote it?"
    """
    row = store.save(session, {**document, STAMP_KEY: {"file_sha256": file_hash}})
    session.flush()

    stored = store.to_document(row)  # what the row actually holds, defaults and all
    settings = dict(row.settings or {})
    settings[STAMP_KEY] = {
        "file_sha256": file_hash,
        "row_sha256": fingerprint(stored),
        "_comment": (
            "Written by db.bootstrap_config. `file_sha256` detects a reviewed change to the seed "
            "file; `row_sha256` detects an edit made through /settings/voice. A deploy applies the "
            "file only when the row still matches `row_sha256` — that is how a live edit protects "
            "itself from the next deploy."
        ),
    }
    row.settings = settings
    return row


def _projected(current: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    """What the row would hold if `document` were applied — computed, not written.

    Mirrors `store.save`: a column named in the document is overwritten, a column the document omits
    keeps its current value, and `settings` is replaced wholesale. Comparing against this rather than
    against the raw document is what makes "would applying this change anything?" answerable for a
    partial seed file, whose omissions are not the same thing as deletions.
    """
    projected = {
        key: value for key, value in document.items() if key not in store.COLUMNS and key != "brand"
    }
    projected["brand"] = current.get("brand", document.get("brand"))
    for column in store.COLUMNS:
        projected[column] = document[column] if column in document else current.get(column)
    return projected


def apply_seed(session: Session, path: Path) -> str:
    """Apply one seed file if it is safe to. Returns what happened, for the log.

    Outcomes: `created`, `updated`, `unchanged`, `skipped-edited`.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    brand = document.get("brand")
    if not brand:
        return f"ignored {path.name}: no `brand` key"

    file_hash = fingerprint(document)
    row = session.get(BrandConfig, brand)

    if row is None:
        write_stamped(session, document, file_hash)
        return f"created {brand} from {path.name}"

    current = store.to_document(row)
    raw_stamp = current.get(STAMP_KEY)
    stamp = raw_stamp if isinstance(raw_stamp, dict) else {}

    if stamp.get("file_sha256") == file_hash:
        return f"unchanged {brand}"

    expected_row = stamp.get("row_sha256")

    # An unstamped row predates this module — seeded by hand, or by a deploy before boot-seeding
    # existed. Refusing it outright would be safe but useless: the first such row is production's,
    # and it would need a manual seed before boot-seeding ever did anything. So adopt it when
    # applying the file would change nothing. Nothing is overwritten, there is no conflict to
    # arbitrate, and the stamp it gains is what arms every deploy after this one.
    if expected_row is None and fingerprint(current) == fingerprint(_projected(current, document)):
        write_stamped(session, document, file_hash)
        return f"adopted {brand} (identical to {path.name}, now stamped)"

    # Otherwise the row and the file disagree and the row is the authority: someone wrote to it
    # through `/settings/voice` or a hand-run `db.seed`, or its provenance is unknown. A deploy does
    # not get to revert either of those.
    if expected_row is None or fingerprint(current) != expected_row:
        logger.warning(
            "brand_config for %r has been edited since it was seeded (or predates boot-seeding); "
            "NOT overwriting it from %s. file=%s row=%s expected=%s. This is a real conflict — a "
            "reviewed change and a live edit both want these fields. Reconcile deliberately: "
            "`python -m brandcortex.db.seed %s` forces the file to win.",
            brand, path.name, file_hash[:12], fingerprint(current)[:12],
            (expected_row or "(none)")[:12], path,
        )
        return f"skipped-edited {brand}"

    write_stamped(session, document, file_hash)
    return f"updated {brand} from {path.name}"


def apply_all(session: Session, seed_dir: Path) -> list[str]:
    """Apply every `*.brand_config.json` in `seed_dir`. Never raises for one bad file."""
    if not seed_dir.is_dir():
        logger.info("no seed directory at %s; skipping config bootstrap", seed_dir)
        return []

    results = []
    for path in sorted(seed_dir.glob("*.brand_config.json")):
        try:
            results.append(apply_seed(session, path))
        except Exception:  # noqa: BLE001 — one malformed file must not stop the API booting
            logger.exception("could not apply seed %s", path)
            results.append(f"failed {path.name}")
    return results
