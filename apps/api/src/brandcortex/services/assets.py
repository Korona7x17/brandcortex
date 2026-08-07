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

Storage is BrandCortex's own bucket. There is no shared bucket and no write path from the brand. Two
backends, chosen by what `ASSET_BUCKET` looks like: a filesystem path (or `file://`) for local work,
S3-compatible object storage otherwise. The key format is identical either way, so moving a
deployment from one to the other does not rewrite a single stored key.
"""

import shutil
from pathlib import Path
from typing import BinaryIO, Protocol
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from brandcortex.config import get_settings
from brandcortex.schemas.content_item import AssetRef

#: Cache-buster parameter. The card routes set a browser TTL, so a plain URL can hand back a PNG
#: rendered before the data the caption was written from. The studios do the same thing.
CACHE_BUSTER = "_bc"

CAPTURE_TIMEOUT_SECONDS = 30.0


class AssetCaptureError(RuntimeError):
    """The card could not be captured. The draft has no image, so it is not publishable."""


class ObjectStore(Protocol):
    def put(self, key: str, data: bytes, *, content_type: str) -> None: ...

    def open(self, key: str) -> BinaryIO: ...

    def exists(self, key: str) -> bool: ...

    def problems(self) -> list[str]:
        """What is wrong with this store right now, in words, or an empty list.

        Separate from `exists` on purpose: `exists` answers about one object and cannot tell a
        missing key from missing credentials, which is the distinction that matters when a
        deployment has just been pointed at a new bucket.

        These strings are served by `/health/assets`, which is unauthenticated. Name the
        *condition*, never the bucket, endpoint, path or key — whoever is reading already knows
        what `ASSET_BUCKET` is set to, and nobody else should learn it from us.
        """
        ...


class FilesystemStore:
    """Local directory backing. For development and tests; keys are paths under `root`."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self, key: str) -> Path:
        # Keys are built by this module and never by a caller, but a traversal here would write
        # outside the store — cheaper to rule out than to reason about.
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root.resolve()):
            raise ValueError(f"storage key escapes the asset root: {key!r}")
        return path

    def put(self, key: str, data: bytes, *, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def open(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def problems(self) -> list[str]:
        """Conditions, not paths — see the note on the Protocol about who reads these."""
        root = self._root.expanduser()
        if not root.exists():
            # Not an error by itself — `put` creates it. It is worth saying, because on a container
            # it usually means the volume did not mount and the next capture writes to a disk that
            # disappears on redeploy.
            return ["asset root does not exist yet (on a container: the volume did not mount)"]
        if not root.is_dir():
            return ["asset root is not a directory"]
        import os

        if not os.access(root, os.W_OK):
            return ["asset root is not writable"]
        return []


class S3Store:
    """S3-compatible object storage — AWS, R2, Spaces, anything with an endpoint URL."""

    def __init__(self, bucket: str) -> None:
        import boto3  # imported lazily: local deployments never need it

        settings = get_settings()
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.asset_endpoint_url,
            aws_access_key_id=settings.asset_access_key_id,
            aws_secret_access_key=settings.asset_secret_access_key,
            region_name=settings.asset_region,
        )

    def put(self, key: str, data: bytes, *, content_type: str) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)

    def open(self, key: str) -> BinaryIO:
        import io

        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return io.BytesIO(response["Body"].read())

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError:
            return False
        return True

    def problems(self) -> list[str]:
        """`HeadBucket` — one cheap, read-only call that exercises endpoint, credentials and grant.

        Read-only deliberately: `/health/assets` is unauthenticated, and a probe that wrote an
        object would let anyone run up storage operations on the bucket.
        """
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            code = exc.response.get("Error", {}).get("Code", "unknown")
            # Three distinct wrong turns — wrong bucket, wrong token, wrong endpoint — and each
            # sends the reader somewhere different, which is the only reason to separate them.
            if status == 404:
                return ["bucket does not exist at this endpoint"]
            if status in (401, 403):
                return [f"credentials rejected ({code})"]
            return [f"bucket unreachable ({code})"]
        except BotoCoreError as exc:
            # Endpoint typo, DNS, TLS. The exception's own text carries the endpoint URL, so only
            # its type crosses out.
            return [f"cannot reach the object store: {type(exc).__name__}"]
        return []


def get_store(bucket: str | None = None) -> ObjectStore:
    """Resolve a store. A path-shaped bucket means local disk; anything else is S3-compatible.

    `bucket` defaults to `ASSET_BUCKET`. It is an argument at all so a migration can hold the old
    store and the new one at once — the S3 credentials still come from settings, since a deployment
    only ever has one set.
    """
    bucket = bucket if bucket is not None else get_settings().asset_bucket
    if bucket.startswith("file://"):
        return FilesystemStore(Path(bucket[len("file://") :]))
    if bucket.startswith(("/", "./", "../", "~")):
        return FilesystemStore(Path(bucket).expanduser())
    return S3Store(bucket)


def storage_key(post_id: str, *, extension: str = "png") -> str:
    """Where one post's captured card lives.

    Keyed by post rather than by content id: re-drafting the same card produces a different image,
    and overwriting the published one would destroy the archive of what actually went out.
    """
    return f"cards/{post_id}.{extension}"


def bust_cache(url: str, *, token: str) -> str:
    """Append the cache-buster, replacing any existing one so repeat captures stay idempotent."""
    parts = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != CACHE_BUSTER]
    query.append((CACHE_BUSTER, token))
    return urlunparse(parts._replace(query=urlencode(query)))


@retry(
    # 5xx and transport errors only. A 404 means the card route rejected these params, and retrying
    # just delays a failure the reviewer needs to see.
    retry=retry_if_exception_type((httpx.TransportError, AssetCaptureError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=4),
    reraise=True,
)
def _fetch(url: str) -> tuple[bytes, str]:
    response = httpx.get(url, timeout=CAPTURE_TIMEOUT_SECONDS, follow_redirects=True)
    if response.status_code >= 500:
        raise AssetCaptureError(f"card render returned {response.status_code} for {url}")
    if response.status_code != 200:
        # Deliberately not an AssetCaptureError — see the retry predicate above.
        raise ValueError(f"card render returned {response.status_code} for {url}")
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise ValueError(
            f"card render returned {content_type!r}, not an image — the route most likely rendered "
            f"an error page for {url}"
        )
    return response.content, content_type


def capture(asset: AssetRef, *, post_id: str) -> str:
    """Fetch the image at draft time and store it. Returns BrandCortex's storage key.

    Recorded on the post as `asset_storage_key`. An asset that already carries a `storage_key` — a
    brand that persists its own renders — is passed through untouched rather than copied.
    """
    if asset.storage_key:
        return asset.storage_key
    if not asset.render_url:
        raise AssetCaptureError("asset carries neither render_url nor storage_key")

    data, content_type = _fetch(bust_cache(str(asset.render_url), token=post_id))
    extension = "jpg" if "jpeg" in content_type else content_type.rsplit("/", 1)[-1]
    key = storage_key(post_id, extension=extension)
    get_store().put(key, data, content_type=content_type)
    return key


def open_stored(key: str) -> BinaryIO:
    """Open the captured image for upload to a channel.

    Facebook's `POST /{page-id}/photos` takes either a `url` or multipart `source`. Use `source` with
    these bytes: passing a URL would hand the render timing back to Meta.
    """
    return get_store().open(key)


def copy_to(key: str, destination: Path) -> Path:
    """Write a stored capture out to a local file. For inspecting what actually published."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open_stored(key) as src, destination.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    return destination
