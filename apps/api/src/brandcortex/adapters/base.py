"""Adapter protocols — the two seams the whole architecture rests on (spec §3, §4).

Two axes of pluggability sit around a fixed core:

* **Source adapters** feed content *in*. They know one brand's data and emit content items.
* **Channel adapters** push content *out* and read performance back. They know one channel's API.

The core imports these protocols and nothing else from `adapters`. Concrete adapters are resolved at
runtime through `adapters/registry.py`, which is what keeps "add brand #2 / channel #2" a
config-and-adapter job rather than a rewrite.

Implementations are structural — no base class to inherit. A `Protocol` keeps adapters free of core
imports beyond the shared schemas.
"""

from datetime import datetime
from typing import Protocol, runtime_checkable

from brandcortex.schemas.content_item import ContentItem
from brandcortex.schemas.draft import PublishRequest, PublishResult
from brandcortex.schemas.insights import InsightSnapshot


@runtime_checkable
class SourceAdapter(Protocol):
    """Produces content items for one brand.

    Two intake mechanisms (spec §4.3), and open decision #1 is which is primary — the spec leans
    table-watch, keeping the direct API for on-demand renders:

    * **table-watch** — the brand writes rows to `content_items`; `poll` reads them.
    * **direct API** — BrandCortex asks the brand to render a specific item; `fetch` gets it back.

    Either way the adapter reads the brand DB and never writes to it.
    """

    brand: str

    def poll(self, since: datetime | None = None, limit: int = 50) -> list[ContentItem]:
        """Return items ready for ingest, oldest first. Must be idempotent — the ingest worker
        deduplicates on `content_id`, but re-delivery should be cheap and harmless."""
        ...

    def fetch(self, content_id: str) -> ContentItem | None:
        """Render or retrieve one item on demand."""
        ...

    def mark_ingested(self, content_id: str) -> None:
        """Acknowledge intake **in BrandCortex's own state**, never by writing a flag into the brand DB.

        The brand's engine history means "content generated / available"; whether something was posted
        is ours to know and ours alone to store (spec §4.4).
        """
        ...


@runtime_checkable
class ChannelAdapter(Protocol):
    """Publishes to one channel and reads its performance back."""

    channel: str

    def publish(self, request: PublishRequest) -> PublishResult:
        """Publish the asset with its caption, then post the first comment carrying the canonical link.

        The two steps are one operation on purpose: a photo post whose link comment failed to land is a
        broken post, not a partial success. Implementations should surface that as a failure and leave
        the post recoverable rather than reporting success.
        """
        ...

    def fetch_insights(self, channel_post_id: str) -> InsightSnapshot:
        """Snapshot current performance for one published post.

        Reading your *own* Page's insights is fully supported; none of the feed-monitoring restrictions
        apply. Monitoring anyone else's content is out of scope (spec §12).
        """
        ...

    def health_check(self) -> bool:
        """Verify credentials and required permissions before a scheduled run leans on them."""
        ...
