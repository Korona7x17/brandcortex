"""The content-item envelope — the one interface to keep stable (spec §4.2).

Python mirror of `packages/contracts/schemas/content-item.schema.json`. The two must change together.
Evolve by adding a v2 model and accepting both at ingest; never edit v1 in a way that could break a
producing brand.

Everything the generation engine needs is denormalized here. The core never reads a brand's raw tables.
For ThaiSwim, `facts` is `card_renders.snapshot` verbatim — resolved server-side from the same builders
the PNG engine uses, so it is by construction what the image displayed rather than a re-derivation that
can disagree with it. See `docs/thaiswim-integration.md`.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class AssetRef(BaseModel):
    """How to obtain the image. Exactly one of `render_url` or `storage_key`.

    ThaiSwim renders cards on demand from a deterministic, CORS-open URL and keeps no bucket, so
    `render_url` is the live path. `storage_key` stays in the contract for a future brand that persists
    rendered images instead.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["image"] = "image"

    render_url: HttpUrl | None = Field(
        default=None,
        description="Fetched at publish time. A live render reflects data at fetch time, so it can "
        "drift from the facts captured at draft time — compare before publishing.",
    )
    storage_key: str | None = Field(
        default=None, description="Key within a shared asset bucket, for brands that persist images."
    )

    width: int | None = None
    height: int | None = Field(
        default=None,
        description="Omitted when the render height is variable. ThaiSwim swimmer cards are a fixed "
        "1080x1350; event cards are 1080 x (452 + rows*130 + 176).",
    )

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "AssetRef":
        if bool(self.render_url) == bool(self.storage_key):
            raise ValueError("asset requires exactly one of render_url or storage_key")
        return self


class ContentItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_id: str = Field(
        description="Stable id owned by the brand; BrandCortex never mints one. For ThaiSwim this is "
        "the `card_renders.id` cuid — not a UUID, hence a plain string."
    )
    brand: str
    source_type: str = Field(
        description="Brand-defined kind (ThaiSwim: 'swimmer' | 'event', mirroring `card_renders.kind`)."
        " Opaque to the core, used for alternation and feature attribution."
    )
    locale: str
    asset: AssetRef
    canonical_link: HttpUrl = Field(
        description="Goes in the FIRST COMMENT, never the post body. UTM params are appended by the "
        "core at draft time, not by the source adapter."
    )
    facts: dict[str, Any] = Field(
        default_factory=dict,
        description="Denormalized brand-shaped facts. Free-form by design; the core passes them to "
        "the brand's voice templates without interpreting the keys.",
    )
    generated_at: datetime = Field(
        description="When the brand rendered the item. Means 'content generated / available' — never "
        "'posted to channel', which is BrandCortex's own state."
    )

    @property
    def wow_factor(self) -> float:
        """The one generic hint the core reads, for opportunity scanning and ranking (spec §10.2)."""
        try:
            return float(self.facts.get("wow_factor", 0.0))
        except (TypeError, ValueError):
            return 0.0
