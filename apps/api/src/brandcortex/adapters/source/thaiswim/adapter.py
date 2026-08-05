"""ThaiSwim source adapter — the only tenant (spec §2, §4.3).

ThaiSwim's admin already contains **Share-Card Studio**, and this adapter builds nothing new on the
brand side. It reads what the studios already record.

The seam is one table:

    card_renders(id, kind, subject, targetId, label, params JSONB,
                 snapshot JSONB, fileName, createdBy, createdAt)

Two properties of that table make it the right seam, and both were already true before BrandCortex
existed:

* **A row means "published from the studio", not "previewed".** `apps/admin/app/api/card-history` writes
  only when the admin clicks Download, because previews re-render on every selector change and would
  otherwise bury the cards that were actually used. That is exactly the "content generated / available"
  semantic §4.4 asks for — nothing to split, and no `posted` flag to avoid writing back, because the
  brand never had one.
* **`snapshot` cannot lie.** The studio POSTs only *which* card; the route resolves the numbers with the
  same `card-payload.ts` builders the PNG engine calls. So `snapshot` is by construction what the image
  displayed, which is what makes it safe to write copy from without re-deriving anything.

Read-only in the strict sense: SELECT only, against a role that should itself be read-only.

See `docs/thaiswim-integration.md` for the full mapping and the gaps still open on the brand side.
"""

import logging
from datetime import datetime

from sqlalchemy import Engine, text

from brandcortex.adapters.source.thaiswim import mapping
from brandcortex.db.session import get_brand_engine
from brandcortex.schemas.content_item import ContentItem

logger = logging.getLogger(__name__)

#: Every column the envelope needs, and no more. Quoted where Prisma camel-cased the name.
_COLUMNS = 'id, kind, subject, "targetId", label, params, snapshot, "createdAt"'

#: `createdAt` alone is not a total order — two cards downloaded in the same millisecond would let
#: the cursor skip one — so `id` breaks the tie and the cursor is really the pair.
_POLL = text(
    f"SELECT {_COLUMNS} FROM card_renders "
    'WHERE (:since IS NULL OR "createdAt" > :since) '
    'ORDER BY "createdAt" ASC, id ASC LIMIT :limit'
)

_FETCH = text(f"SELECT {_COLUMNS} FROM card_renders WHERE id = :id")


class ThaiSwimSourceAdapter:
    """Implements `SourceAdapter` structurally; see `adapters/base.py`."""

    brand = "thaiswim"

    #: `card_renders.kind` values. These become `source_type` unchanged, so alternation in the
    #: scheduler is literally profile-card <-> event-card.
    KINDS = ("swimmer", "event")

    def __init__(
        self,
        site_url: str = "https://thaiswim.com",
        *,
        default_locale: str = "th",
        engine: Engine | None = None,
    ) -> None:
        self._site = site_url.rstrip("/")
        self._default_locale = default_locale
        self._engine = engine

    @property
    def engine(self) -> Engine:
        """The brand seam. Resolved lazily, so constructing the adapter never needs a database."""
        if self._engine is None:
            self._engine = get_brand_engine()
        return self._engine

    def poll(self, since: datetime | None = None, limit: int = 50) -> list[ContentItem]:
        """Read `card_renders` newer than `since`, oldest first, mapping each row to an envelope.

        No `queued` flag exists on the brand side and none is proposed: taking every published card
        and letting the review queue be the filter is simpler than asking an admin to opt cards in
        twice. Add one only if the volume makes the queue noisy.

        A row that fails to map is logged and skipped rather than aborting the batch. The brand owns
        that data and can grow a `kind` this adapter has not been taught yet; when it does, the right
        outcome is the other forty cards still reaching the review queue.
        """
        with self.engine.connect() as conn:
            rows = conn.execute(_POLL, {"since": since, "limit": limit}).mappings().all()

        items: list[ContentItem] = []
        for row in rows:
            try:
                items.append(self._to_item(dict(row)))
            except (ValueError, KeyError):
                logger.warning(
                    "skipping unmappable card_renders row %s", row.get("id"), exc_info=True
                )
        return items

    def fetch(self, content_id: str) -> ContentItem | None:
        """Load one `card_renders` row by id.

        Note this returns an already-published card, not a fresh render. The opportunity scanner
        (Phase 2) needs something different — cards for swimmers nobody has made a card for yet — and
        that requires either a render-on-demand endpoint in the admin app or the scanner calling the
        card engine URL directly and POSTing to `card-history` itself.
        """
        with self.engine.connect() as conn:
            row = conn.execute(_FETCH, {"id": content_id}).mappings().first()
        return self._to_item(dict(row)) if row else None

    def mark_ingested(self, content_id: str) -> None:
        """Record intake in BrandCortex's own state.

        Deliberately a no-op against the brand DB, and it stays one: intake is already recorded by
        the existence of a `posts` row keyed on `content_id`, and the poll cursor advances on
        `createdAt`. Writing a flag back into `card_renders` would break the read-only contract and
        overload a table whose rows mean "generated", not "posted" (spec §4.4).
        """
        return None

    def _to_item(self, row: dict) -> ContentItem:
        return mapping.row_to_content_item(
            row, site_url=self._site, default_locale=self._default_locale
        )
