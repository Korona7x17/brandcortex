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

from datetime import datetime

from brandcortex.schemas.content_item import ContentItem


class ThaiSwimSourceAdapter:
    """Implements `SourceAdapter` structurally; see `adapters/base.py`."""

    brand = "thaiswim"

    #: `card_renders.kind` values. These become `source_type` unchanged, so alternation in the
    #: scheduler is literally profile-card <-> event-card.
    KINDS = ("swimmer", "event")

    def __init__(self, site_url: str = "https://thaiswim.com") -> None:
        self._site = site_url.rstrip("/")

    def poll(self, since: datetime | None = None, limit: int = 50) -> list[ContentItem]:
        """Read `card_renders` newer than `since`, oldest first, mapping each row to an envelope.

        No `queued` flag exists on the brand side and none is proposed: taking every published card and
        letting the review queue be the filter is simpler than asking an admin to opt cards in twice.
        Add one only if the volume makes the queue noisy.

        TODO(phase-1): SELECT id, kind, subject, "targetId", label, params, snapshot, "createdAt"
        FROM card_renders WHERE "createdAt" > :since ORDER BY "createdAt" ASC LIMIT :limit,
        over the read-only brand engine, then map through `mapping.row_to_content_item`.
        """
        raise NotImplementedError

    def fetch(self, content_id: str) -> ContentItem | None:
        """Load one `card_renders` row by id.

        Note this returns an already-published card, not a fresh render. The opportunity scanner
        (Phase 2) needs something different — cards for swimmers nobody has made a card for yet — and
        that requires either a render-on-demand endpoint in the admin app or the scanner calling the
        card engine URL directly and POSTing to `card-history` itself.

        TODO(phase-1).
        """
        raise NotImplementedError

    def mark_ingested(self, content_id: str) -> None:
        """Record intake in BrandCortex's own state.

        Deliberately a no-op against the brand DB. Intake is tracked by the existence of a `posts` row
        keyed on `content_id`, and the poll cursor advances on `createdAt`.

        TODO(phase-1).
        """
        raise NotImplementedError
