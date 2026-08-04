"""Thin Graph API HTTP client.

Kept separate from the adapter so the adapter's publish/insight logic can be tested against a fake
transport. Tests never reach the real Graph API.

The Graph version is pinned in settings and appears in every path: Meta renames insight metrics and
shifts permission requirements between versions, and an unpinned client silently changes behaviour on
their release schedule rather than ours.
"""

import hashlib
import hmac
from typing import Any


def appsecret_proof(access_token: str, app_secret: str) -> str:
    """HMAC-SHA256 of the access token, keyed by the app secret.

    Sent as `appsecret_proof` on every call. Required when the app has "Require app secret" enabled,
    and worth sending unconditionally: it means a stolen Page token is useless on its own, since an
    attacker would also need the app secret to forge the proof. For a server holding tokens that can
    publish to a brand's Page, that is exactly the threat worth closing.

    Cheap enough that there is no reason to make it conditional.
    """
    return hmac.new(
        app_secret.encode("utf-8"), access_token.encode("utf-8"), hashlib.sha256
    ).hexdigest()


class GraphError(RuntimeError):
    """A Graph API error, carrying the subcode needed to distinguish retryable from terminal."""

    def __init__(self, message: str, *, code: int | None = None, subcode: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.subcode = subcode


class GraphClient:
    """Authenticated calls against a pinned Graph API version.

    TODO(phase-1): implement over `httpx`, with `tenacity` retries on transient errors only —
    rate limits and 5xx are retryable; an invalid token or a permission error is not, and retrying it
    only delays the human fix.
    """

    def __init__(
        self,
        access_token: str,
        *,
        version: str,
        app_secret: str | None = None,
        base_url: str = "https://graph.facebook.com",
    ):
        self._token = access_token  # never log this
        self._version = version
        self._base_url = base_url
        # Precomputed once: the proof depends only on the token and the secret, not the call.
        self._proof = appsecret_proof(access_token, app_secret) if app_secret else None

    def _auth_params(self) -> dict[str, str]:
        """Auth parameters every request carries."""
        params = {"access_token": self._token}
        if self._proof:
            params["appsecret_proof"] = self._proof
        return params

    def post(self, path: str, data: dict[str, Any] | None = None, files: dict | None = None) -> dict:
        raise NotImplementedError

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        raise NotImplementedError
