"""Capturing and storing the image to publish.

The card engines render on demand from a deterministic, CORS-open URL. **Fetch the PNG once at draft
time and store the bytes**, then publish those bytes. This mirrors exactly what the studio's Download
button already does — the admin saves a file and posts that file — so the image is frozen the moment
the draft exists, and what the reviewer approves is byte-for-byte what ships.

Doing it this way removes a question rather than answering one. Fetching at publish instead — or
handing Facebook a `url` and letting Meta fetch it — would re-render from whatever the data said at
that moment while the caption was written from the draft-time snapshot. Capturing once costs a single
HTTP GET, so there is no reason to carry the question.

The stored copy is also the archive of what was actually published, which the dashboard wants anyway.

Storage is BrandCortex's own bucket. There is no shared bucket and no write path from the brand.
"""

from typing import BinaryIO

from brandcortex.schemas.content_item import AssetRef


def capture(asset: AssetRef, *, post_id: str) -> str:
    """Fetch the image at draft time and store it. Returns BrandCortex's storage key.

    Recorded on the post as `asset_storage_key`.

    TODO(phase-1): GET `render_url` via httpx (retry 5xx only), write to the configured store. Append a
    cache-buster the way the studios do — the card endpoints set a browser TTL, so a plain URL can
    return a stale PNG.
    """
    raise NotImplementedError


def open_stored(storage_key: str) -> BinaryIO:
    """Open the captured image for upload to a channel.

    Facebook's `POST /{page-id}/photos` takes either a `url` or multipart `source`. Use `source` with
    these bytes: passing a URL would hand the render timing back to Meta.
    """
    raise NotImplementedError
