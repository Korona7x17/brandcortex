"""Publishes approved and due posts (spec §7 steps 6–8).

Picks up posts that are approved (publish now) or scheduled with a slot that has arrived, then hands
them to the channel adapter.

Retry policy matters here: a transient Graph error deserves a retry, an expired token does not — it
needs a human. Retrying a permission failure only delays that. And a post whose photo landed but whose
link comment failed must not be retried from the top, or the Page gets a duplicate photo.
"""


def run_once() -> int:
    """Publish everything currently due. Returns the count published. TODO(phase-1)."""
    raise NotImplementedError
