"""Moving captured cards between stores, and reporting whether a store is reachable at all.

The move that motivated this is the Railway volume to R2. What the tests are actually about is the
two ways it can go quietly wrong: bytes that the old store does not have (a published post loses the
archive of what went out), and a key that exists on both sides with different content (two
deployments wrote independently, and overwriting destroys one of them). Both must be loud.
"""

import logging

import pytest

from brandcortex.services import assets, migrate_assets

PNG = b"\x89PNG\r\n\x1a\n" + b"card bytes"


@pytest.fixture
def stores(tmp_path):
    old = assets.get_store(str(tmp_path / "old"))
    new = assets.get_store(str(tmp_path / "new"))
    return old, new


def test_a_path_shaped_bucket_is_local_disk(tmp_path) -> None:
    assert isinstance(assets.get_store(str(tmp_path)), assets.FilesystemStore)
    assert isinstance(assets.get_store(f"file://{tmp_path}"), assets.FilesystemStore)


# --- copying -------------------------------------------------------------------------------------


def test_a_card_arrives_byte_for_byte(stores) -> None:
    """The stored copy is the archive of what was published; a lossy move is not a move."""
    old, new = stores
    old.put("cards/a.png", PNG, content_type="image/png")

    assert migrate_assets.copy_key("cards/a.png", source=old, destination=new) == "copied"
    with new.open("cards/a.png") as handle:
        assert handle.read() == PNG


def test_rerunning_skips_what_is_already_there(stores) -> None:
    """Idempotent on purpose: the migration runs against production by hand, and a half-finished
    run must be safe to simply repeat."""
    old, new = stores
    old.put("cards/a.png", PNG, content_type="image/png")
    migrate_assets.copy_key("cards/a.png", source=old, destination=new)

    assert migrate_assets.copy_key("cards/a.png", source=old, destination=new) == "skipped"


def test_a_key_the_old_store_lacks_is_reported_not_swallowed(stores) -> None:
    old, new = stores
    assert migrate_assets.copy_key("cards/gone.png", source=old, destination=new) == "missing"


def test_same_key_different_bytes_is_never_overwritten(stores) -> None:
    """Two deployments wrote independently. Which copy survives is not this script's call."""
    old, new = stores
    old.put("cards/a.png", PNG, content_type="image/png")
    new.put("cards/a.png", b"a different render", content_type="image/png")

    assert migrate_assets.copy_key("cards/a.png", source=old, destination=new) == "mismatch"
    with new.open("cards/a.png") as handle:
        assert handle.read() == b"a different render"


def test_a_missing_key_fails_the_command(monkeypatch, stores) -> None:
    """`missing` and `mismatch` need a person, so they must not exit 0 into a green deploy log."""
    old, new = stores
    monkeypatch.setattr(migrate_assets, "referenced_keys", lambda: ["cards/gone.png"])
    monkeypatch.setattr(
        assets, "get_store", lambda bucket=None: old if bucket is not None else new
    )

    assert migrate_assets.main(["--source", "unused"]) == 1


def test_a_dry_run_writes_nothing(monkeypatch, stores, caplog) -> None:
    old, new = stores
    old.put("cards/a.png", PNG, content_type="image/png")
    monkeypatch.setattr(migrate_assets, "referenced_keys", lambda: ["cards/a.png"])
    monkeypatch.setattr(
        assets, "get_store", lambda bucket=None: old if bucket is not None else new
    )

    with caplog.at_level(logging.INFO):
        counts = migrate_assets.run(source_bucket="unused", dry_run=True)

    assert counts["copied"] == 1
    assert not new.exists("cards/a.png")
    assert "dry run" in caplog.text


# --- is the store even there? --------------------------------------------------------------------


def test_a_healthy_directory_has_no_problems(tmp_path) -> None:
    (tmp_path / "cards").mkdir()
    assert assets.get_store(str(tmp_path / "cards")).problems() == []


def test_an_unmounted_volume_says_so(tmp_path) -> None:
    """On a container this usually means the volume did not mount, and the next capture writes to a
    disk that disappears on redeploy — the failure `put` would hide by creating the directory."""
    problems = assets.get_store(str(tmp_path / "never-mounted")).problems()
    assert problems == ["asset root does not exist yet (on a container: the volume did not mount)"]


def test_a_read_only_root_says_so(tmp_path) -> None:
    root = tmp_path / "cards"
    root.mkdir(mode=0o500)
    try:
        assert assets.get_store(str(root)).problems() == ["asset root is not writable"]
    finally:
        root.chmod(0o700)


def _s3_raising(exc) -> assets.S3Store:
    """An S3Store whose HeadBucket fails, without constructing a real boto3 client."""
    store = assets.S3Store.__new__(assets.S3Store)
    store._bucket = "brandcortex-cards"

    class Client:
        def head_bucket(self, **_):
            raise exc

    store._client = Client()
    return store


@pytest.mark.parametrize(
    ("status", "code", "expected"),
    [
        (404, "NoSuchBucket", "bucket does not exist at this endpoint"),
        (403, "AccessDenied", "credentials rejected (AccessDenied)"),
        (401, "InvalidAccessKeyId", "credentials rejected (InvalidAccessKeyId)"),
        (500, "InternalError", "bucket unreachable (InternalError)"),
    ],
)
def test_s3_failures_are_reported_in_words(status, code, expected) -> None:
    """The three ways an R2 switch goes wrong — wrong bucket, wrong token, wrong endpoint — have to
    be distinguishable from each other, because each sends you somewhere different."""
    from botocore.exceptions import ClientError

    error = ClientError(
        {"Error": {"Code": code}, "ResponseMetadata": {"HTTPStatusCode": status}}, "HeadBucket"
    )
    assert _s3_raising(error).problems() == [expected]
    assert "brandcortex-cards" not in expected, "the bucket name never crosses out"


def test_an_unreachable_endpoint_never_echoes_the_exception_body() -> None:
    """A botocore error can carry the endpoint and the request; the response is public."""
    from botocore.exceptions import EndpointConnectionError

    problems = _s3_raising(
        EndpointConnectionError(endpoint_url="https://acct.r2.cloudflarestorage.com")
    ).problems()
    assert problems == ["cannot reach the object store: EndpointConnectionError"]


def test_health_answers_without_a_session_and_names_no_bucket(monkeypatch, tmp_path) -> None:
    """`/health/*` is the one open surface, so it may say *that* the store is wrong and never
    *where* it is. It has to stay open: this is the check you run right after switching ASSET_*,
    and reaching it should not depend on the dashboard being able to sign you in."""
    from fastapi.testclient import TestClient

    from brandcortex.config import get_settings
    from brandcortex.main import create_app

    monkeypatch.setenv("ASSET_BUCKET", str(tmp_path / "cards"))
    get_settings.cache_clear()
    try:
        response = TestClient(create_app(), raise_server_exceptions=False).get("/health/assets")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["backend"] == "filesystem"
    assert body["ok"] is False, "an unmounted root is exactly what this endpoint is for"
    assert str(tmp_path) not in response.text, "the open endpoint names conditions, not paths"
