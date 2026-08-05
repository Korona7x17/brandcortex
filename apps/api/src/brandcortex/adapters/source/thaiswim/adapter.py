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

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

import httpx
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

#: Enumerations the event board is bucketed by. Brand knowledge, so it lives here rather than in the
#: core. Sourced from ThaiSwim's own `swim-format` constants and masters age groups.
STROKES = ("freestyle", "backstroke", "breaststroke", "butterfly", "medley")
DISTANCES = ("50", "100", "200", "400", "800", "1500")
GENDERS = ("M", "F")
COURSES = ("LCM", "SCM")
AGE_GROUPS = (
    "18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
    "60-64", "65-69", "70-74", "75-79", "80-84", "85-89", "90-94", "95-99",
)

COMPOSE_TIMEOUT_SECONDS = 45.0


def compose_content_id(kind: str, params: dict[str, Any]) -> str:
    """A stable id for a card the brand has no row for.

    `poll` gets ids from `card_renders`; a composed card has no row there, and BrandCortex does not
    write to the brand's database. So the id is derived from the params rather than minted at random,
    which is what keeps `Orchestrator.ingest` idempotent for composed cards too — composing the same
    board twice is one draft, not two. Prefixed so a composed id is never mistaken for a brand cuid.
    """
    digest = hashlib.sha256(
        json.dumps({"kind": kind, "params": params}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return f"bc-{kind}-{digest[:20]}"



class ThaiSwimSourceAdapter:
    """Implements `SourceAdapter` structurally; see `adapters/base.py`."""

    brand = "thaiswim"

    #: `card_renders.kind` values. These become `source_type` unchanged, so alternation in the
    #: scheduler is literally profile-card <-> event-card.
    KINDS = ("swimmer", "event")

    #: What an operator can compose here, and the shape of each. The dashboard builds its composer
    #: from this rather than from a hardcoded list — brand #2 declares its own kinds.
    SOURCE_TYPES = [
        {
            "key": "swimmer",
            "label": "Swimmer profile",
            "searchable": True,
            "search_hint": "Type a name in Thai or English",
            "fields": [],
        },
        {
            "key": "event",
            "label": "Event ranking board",
            "searchable": False,
            "fields": [
                {"name": "stroke", "label": "Stroke", "options": list(STROKES)},
                {"name": "distance", "label": "Distance", "options": list(DISTANCES)},
                {"name": "gender", "label": "Gender", "options": list(GENDERS)},
                {"name": "ageGroup", "label": "Age group", "options": list(AGE_GROUPS)},
                {"name": "course", "label": "Course", "options": list(COURSES)},
                {"name": "n", "label": "Places", "options": [str(v) for v in range(3, 11)]},
            ],
        },
    ]

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
    def site_url(self) -> str:
        return self._site

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

    # --- composing a card nobody has downloaded yet ---------------------------------------------

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Swimmers matching a name, best national rank first.

        Calls ThaiSwim's own search route — the one the Share-Card Studio uses — rather than querying
        the database, so "which swimmers are worth a card" stays one definition on the brand side.
        """
        response = httpx.get(
            f"{self._site}/api/card/swimmer/search",
            params={"q": query},
            timeout=COMPOSE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json().get("results", [])[:limit]
        return [
            {
                "source_type": "swimmer",
                "key": r["slug"],
                "label": r["name"],
                "sublabel": " · ".join(x for x in (r.get("club"), r.get("province")) if x),
                "hint": f"best national rank {r['bestRank']}" if r.get("bestRank") else None,
                "params": {"slug": r["slug"]},
            }
            for r in results
        ]

    def preview_url(self, source_type: str, params: dict[str, Any]) -> str:
        """The live render URL, for looking at before committing. Not what gets published — publishing
        uses the bytes captured at draft time."""
        return mapping.render_url(
            source_type, params, site_url=self._site,
            locale=mapping.resolve_locale(source_type, params, default=self._default_locale),
        )

    def compose(self, source_type: str, params: dict[str, Any]) -> ContentItem:
        """Build a content item for a card the brand has no row for.

        The numbers come from ThaiSwim's payload route, which resolves them with the same builders
        the PNG engine calls. Deriving them here instead would put a second implementation of every
        figure in the caption one step away from the image that has to agree with it.
        """
        if source_type not in self.KINDS:
            raise ValueError(f"unknown source type {source_type!r}; expected one of {self.KINDS}")

        response = httpx.get(
            f"{self._site}/api/card/{source_type}/payload",
            params=_payload_query(source_type, params),
            timeout=COMPOSE_TIMEOUT_SECONDS,
        )
        if response.status_code == 404:
            raise LookupError(f"no {source_type} card for {params}")
        response.raise_for_status()
        payload = response.json()

        resolved = payload["params"]
        return self._to_item(
            {
                "id": compose_content_id(source_type, resolved),
                "kind": payload["kind"],
                "subject": payload["subject"],
                "targetId": None,
                "label": payload["label"],
                "params": resolved,
                "snapshot": payload["snapshot"],
                # Composed now, so "when the brand rendered it" is now.
                "createdAt": datetime.now(UTC),
            }
        )

    def _to_item(self, row: dict) -> ContentItem:
        return mapping.row_to_content_item(
            row, site_url=self._site, default_locale=self._default_locale
        )


def _payload_query(source_type: str, params: dict) -> dict:
    """Query names the payload route takes.

    The event engine takes `dist` and `age` where the snapshot says `distance` and `ageGroup` — the
    same trap `mapping.render_url` documents. Sending the snapshot's names would silently resolve the
    default bucket instead of the requested one.
    """
    if source_type == "swimmer":
        return {"slug": params.get("slug") or params.get("id")}
    return {
        "stroke": params["stroke"],
        "dist": params.get("distance", params.get("dist")),
        "gender": params["gender"],
        "age": params.get("ageGroup", params.get("age")),
        "course": params["course"],
        "n": params.get("n", 8),
    }
