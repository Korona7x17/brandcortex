"""The API refuses to serve bare.

Every route that can read a draft or publish to a live Page requires a verified Clerk session; the
one thing these tests exist to prove is that *forgetting to configure auth locks the API* rather
than opening it. The JWT checks run against a keypair minted here and injected into the module's
JWKS cache — no network, and a token signed by anyone else fails exactly like a forged one.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient

from brandcortex.api import auth
from brandcortex.config import get_settings

ISSUER = "https://clerk.test.example"

_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def mint(*, key=_key, issuer=ISSUER, azp="http://localhost:3000", expired=False) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": "user_1",
            "iss": issuer,
            "azp": azp,
            "iat": now - timedelta(hours=1 if expired else 0),
            "exp": now + timedelta(minutes=-30 if expired else 5),
        },
        key,
        algorithm="RS256",
    )


@pytest.fixture(autouse=True)
def clean_settings(monkeypatch):
    """Each test states its own auth env; required-but-irrelevant settings get placeholders."""
    # Explicitly pinned, not merely unset: the developer's own .env (read from the working
    # directory) legitimately carries these, and only a process env var outranks it. Empty means
    # unconfigured to the Settings model.
    monkeypatch.setenv("CLERK_ISSUER", "")
    monkeypatch.delenv("CLERK_AUTHORIZED_PARTIES", raising=False)
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("ASSET_BUCKET", "/tmp/test-assets")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "unused")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
    auth._jwks_clients.clear()


@pytest.fixture
def probe():
    """A minimal app with one protected route — the dependency is the subject, not the routers."""
    app = FastAPI()

    @app.get("/probe")
    def probe_route(session: auth.Session) -> dict:
        return {"sub": session.get("sub")}

    return TestClient(app, raise_server_exceptions=False)


def use_local_jwks(issuer: str = ISSUER, key=_key) -> None:
    public = key.public_key()
    auth._jwks_clients[issuer] = SimpleNamespace(
        get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=public)
    )


class TestFailClosed:
    def test_unconfigured_auth_is_a_lock_not_an_opening(self, monkeypatch, probe):
        response = probe.get("/probe")
        assert response.status_code == 503
        assert "AUTH_DISABLED" in response.text

    def test_the_real_app_wires_the_lock_onto_content_routes(self, monkeypatch):
        from brandcortex.main import create_app

        client = TestClient(create_app(), raise_server_exceptions=False)
        assert client.get("/posts").status_code == 503
        assert client.get("/health").status_code == 200, "health stays open for the platform"

    def test_disabling_auth_is_an_explicit_statement(self, monkeypatch, probe):
        monkeypatch.setenv("AUTH_DISABLED", "true")
        get_settings.cache_clear()
        assert probe.get("/probe").status_code == 200


class TestVerification:
    @pytest.fixture(autouse=True)
    def configured(self, monkeypatch):
        monkeypatch.setenv("CLERK_ISSUER", ISSUER)
        monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "http://localhost:3000")
        get_settings.cache_clear()
        use_local_jwks()

    def test_a_valid_session_passes_and_yields_its_claims(self, probe):
        response = probe.get("/probe", headers={"authorization": f"Bearer {mint()}"})
        assert response.status_code == 200
        assert response.json() == {"sub": "user_1"}

    def test_no_token_is_401(self, probe):
        assert probe.get("/probe").status_code == 401

    def test_a_token_signed_by_someone_else_is_401(self, probe):
        token = mint(key=_other_key)
        assert probe.get("/probe", headers={"authorization": f"Bearer {token}"}).status_code == 401

    def test_an_expired_session_is_401(self, probe):
        token = mint(expired=True)
        assert probe.get("/probe", headers={"authorization": f"Bearer {token}"}).status_code == 401

    def test_a_token_from_another_issuer_is_401(self, probe):
        use_local_jwks(issuer="https://clerk.evil.example")
        token = mint(issuer="https://clerk.evil.example")
        assert probe.get("/probe", headers={"authorization": f"Bearer {token}"}).status_code == 401

    def test_a_session_minted_by_an_unlisted_frontend_is_401(self, probe):
        token = mint(azp="https://not-our-dashboard.example")
        assert probe.get("/probe", headers={"authorization": f"Bearer {token}"}).status_code == 401
