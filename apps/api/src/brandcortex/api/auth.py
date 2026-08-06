"""Session verification for every route that can read or change content.

The dashboard signs users in with Clerk; this module is the API's half of that arrangement. Each
request carries the Clerk session JWT as a bearer token, and the API verifies it independently —
signature against the instance's JWKS, expiry, issuer, and which frontend minted it. The API never
talks to Clerk per-request: verification is pure computation against cached public keys, so Clerk
being down leaves signed-in reviewers working.

Fail closed. With no `CLERK_ISSUER` configured the protected routes return 503 rather than serving
openly — an API that approves and publishes to a live Page must never be reachable bare because a
deployment forgot one env var. Local development without Clerk opts out explicitly with
`AUTH_DISABLED=true`, which is a statement in the .env a person wrote, not a default they fell into.
"""

import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient

from brandcortex.config import get_settings

logger = logging.getLogger(__name__)

#: One JWKS client per issuer for the process lifetime. PyJWKClient caches the keys and refetches
#: on unknown-kid, which is exactly the rotation behaviour Clerk expects of verifiers.
_jwks_clients: dict[str, PyJWKClient] = {}


def _jwks_client(issuer: str) -> PyJWKClient:
    client = _jwks_clients.get(issuer)
    if client is None:
        client = PyJWKClient(f"{issuer.rstrip('/')}/.well-known/jwks.json", cache_keys=True)
        _jwks_clients[issuer] = client
    return client


def _unauthorized(reason: str) -> HTTPException:
    # The reason is for the dashboard's error rendering and the server log, and names the check
    # that failed, never anything from inside the token.
    return HTTPException(status_code=401, detail=f"unauthorized: {reason}")


def require_session(request: Request) -> dict:
    """FastAPI dependency: the verified claims of the caller's session, or 401/503.

    Applied to every router except health. Health stays open because it is what the platform's
    checks and a locked-out operator both need first.
    """
    settings = get_settings()
    if settings.auth_disabled:
        return {"sub": "dev", "auth": "disabled"}
    if not settings.clerk_issuer:
        raise HTTPException(
            status_code=503,
            detail=(
                "auth is not configured: set CLERK_ISSUER, or AUTH_DISABLED=true for local"
                " development"
            ),
        )

    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("missing bearer token")

    try:
        key = _jwks_client(settings.clerk_issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            # Clerk session tokens carry `azp` (the origin that minted them) instead of `aud`.
            options={"verify_aud": False},
            leeway=5,
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized(type(exc).__name__) from None

    azp = claims.get("azp")
    if settings.clerk_authorized_parties and azp not in settings.clerk_authorized_parties:
        raise _unauthorized("azp not in CLERK_AUTHORIZED_PARTIES")
    return claims


Session = Annotated[dict, Depends(require_session)]
