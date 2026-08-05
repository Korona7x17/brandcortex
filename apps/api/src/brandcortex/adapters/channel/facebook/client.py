"""Thin Graph API HTTP client.

Kept separate from the adapter so the adapter's publish/insight logic can be tested against a fake
transport. Tests never reach the real Graph API.

The Graph version is pinned in settings and appears in every path: Meta renames insight metrics and
shifts permission requirements between versions, and an unpinned client silently changes behaviour on
their release schedule rather than ours.
"""

import hashlib
import hmac
import logging
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

#: Graph error codes worth trying again. Everything else is a human's problem, and retrying it only
#: delays the moment someone finds out.
#:   1, 2   transient platform faults
#:   4, 17, 32, 613  rate limiting, per-app and per-user
#:   341    temporary application-level throttle
RETRYABLE_CODES = frozenset({1, 2, 4, 17, 32, 341, 613})

#: A token that is expired, revoked or missing a scope. Never retried: the fix is a person
#: re-authorizing, and a retry loop turns a clear failure into a silent one.
AUTH_CODES = frozenset({190, 102, 200, 10})

REQUEST_TIMEOUT_SECONDS = 60.0


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


class _Retryable(RuntimeError):
    """Internal marker: a fault worth trying again. Never escapes the client."""

    def __init__(self, message: str, *, code: int | None = None, subcode: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.subcode = subcode


class GraphError(RuntimeError):
    """A Graph API error, carrying the subcode needed to distinguish retryable from terminal."""

    def __init__(self, message: str, *, code: int | None = None, subcode: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.subcode = subcode


class GraphAuthError(GraphError):
    """The token cannot do this. A person must re-authorize; nothing here should retry."""


class GraphClient:
    """Authenticated calls against a pinned Graph API version.

    Retries transient faults and rate limits only. An invalid token or a missing permission is
    terminal by design: retrying it delays the human fix and turns a loud failure into a slow one.
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

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{self._version}/{path.lstrip('/')}"

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, _Retryable)),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, max=20),
        reraise=True,
    )
    def _send(self, method: str, path: str, **kwargs: Any) -> dict:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.request(method, self._url(path), **kwargs)
        return self._unwrap(response)

    def _unwrap(self, response: httpx.Response) -> dict:
        """Turn a Graph response into data, or into the narrowest error that fits.

        Graph answers 200 with an `error` object often enough that status alone is not a reliable
        signal, so the body is inspected either way.
        """
        try:
            body = response.json()
        except ValueError:
            if response.is_success:
                return {}
            raise GraphError(
                f"graph returned {response.status_code} with a non-JSON body"
            ) from None

        error = body.get("error") if isinstance(body, dict) else None
        if error:
            code = error.get("code")
            subcode = error.get("error_subcode")
            # The message can quote the request, which carries the token. Keep Meta's type and
            # codes, drop their prose.
            summary = f"{error.get('type', 'GraphError')} code={code} subcode={subcode}"
            if code in AUTH_CODES:
                raise GraphAuthError(
                    f"{summary}: the Page token is invalid, expired or missing a permission",
                    code=code,
                    subcode=subcode,
                )
            if code in RETRYABLE_CODES or response.status_code >= 500:
                raise _Retryable(summary, code=code, subcode=subcode)
            raise GraphError(summary, code=code, subcode=subcode)

        if response.status_code >= 500:
            raise _Retryable(f"graph returned {response.status_code}")
        if not response.is_success:
            raise GraphError(f"graph returned {response.status_code}")
        return body

    def post(self, path: str, data: dict[str, Any] | None = None, files: dict | None = None) -> dict:
        """POST with auth in the form body, so the token never lands in a URL.

        URLs reach access logs, proxies and error trackers; form bodies generally do not.
        """
        return self._send(
            "POST", path, data={**(data or {}), **self._auth_params()}, files=files
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        return self._send("GET", path, params={**(params or {}), **self._auth_params()})

    def debug_token(self) -> dict:
        """What this token actually is: its scopes, expiry and the app it belongs to.

        Reads the token's own metadata, which is how `health_check` can report a missing permission
        before a scheduled publish discovers it at 3am.
        """
        return self.get("debug_token", {"input_token": self._token})
