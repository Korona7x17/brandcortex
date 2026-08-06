"""Reading and writing a brand's configuration document.

The `brand_config` table is where everything brand-specific lives so the core stays neutral. The
generation engine reads it as one flat mapping — the same shape as `seeds/<brand>.brand_config.json` —
while the table gives the fields worth querying their own columns. This module is the translation
between those two views, and the only place that knows the mapping.

Round-tripping matters more than it looks. The seed documents carry `_comment` keys recording *why* a
value is what it is (why the unit label is `ม.`, why reactions are weighted zero), and dropping them
on load would leave that reasoning in git and nowhere an operator looks. They ride along in
`settings`.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from brandcortex.db.models import BrandConfig

#: Document keys with a dedicated column. Everything else goes to `settings`. Public because
#: `db.bootstrap_config` needs the same split to predict what applying a document would change.
COLUMNS = (
    "display_name",
    "timezone",
    "default_locale",
    "voice",
    "intro_bank",
    "hashtags",
    "unit_labels",
    "tag_targets",
    "north_star",
    "scheduling",
)


class BrandNotConfigured(LookupError):
    """No `brand_config` row for this brand.

    Drafting without one would silently fall back to defaults for voice, which is the one thing that
    must never be defaulted.
    """


def to_document(row: BrandConfig) -> dict[str, Any]:
    """Flatten a row back into the document shape the engine reads."""
    document: dict[str, Any] = dict(row.settings or {})
    document["brand"] = row.brand
    for key in COLUMNS:
        document[key] = getattr(row, key)
    return document


def load(session: Session, brand: str) -> dict[str, Any]:
    """The brand's configuration document. Raises when the brand has no row."""
    row = session.get(BrandConfig, brand)
    if row is None:
        known = sorted(session.scalars(select(BrandConfig.brand)).all())
        raise BrandNotConfigured(
            f"no brand_config row for {brand!r}; configured brands: {known or '(none)'}"
        )
    return to_document(row)


def save(session: Session, document: dict[str, Any]) -> BrandConfig:
    """Upsert a configuration document. Used by the seed loader and the config editor.

    Replaces rather than merges: a config is reviewed as a whole document, and a partial write is how
    a voice rule goes missing without anyone deciding to remove it.
    """
    brand = document["brand"]
    row = session.get(BrandConfig, brand) or BrandConfig(brand=brand)

    for key in COLUMNS:
        if key in document:
            setattr(row, key, document[key])
    row.settings = {
        key: value for key, value in document.items() if key not in COLUMNS and key != "brand"
    }

    session.add(row)
    return row
