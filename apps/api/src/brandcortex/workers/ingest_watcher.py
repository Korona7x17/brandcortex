"""Watches source adapters for new content items (spec §4.3, §7 step 2).

Primary intake per the spec's recommendation is table-watch: the brand writes to `content_items` and
this worker polls. Open decision #1 has not been settled — keep the direct-API path available for
on-demand renders either way.

Polling must be idempotent: `Orchestrator.ingest` deduplicates on content_id + channel, so re-delivery
is harmless and the worker never needs exactly-once semantics.
"""


def run_once(brand: str) -> int:
    """Poll one brand's source adapter and ingest what it returns. Returns the count ingested.

    TODO(phase-1): implement via adapters.registry.get_source_adapter.
    """
    raise NotImplementedError
