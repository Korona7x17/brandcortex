"""Validate a Page token and store it encrypted.

    uv run python -m brandcortex.adapters.channel.facebook.authorize

Reads `FACEBOOK_PAGE_ACCESS_TOKEN` from the environment, asks Graph what it actually is, and stores
it only if it can do the job. The token is never printed, never passed as an argument (which would
put it in shell history), and never logged.

## Why it validates before storing

A token that is the wrong *type* fails in a way that reads like a permissions problem, and a token
missing one scope publishes the photo and then fails on the comment — leaving a live card with no
link, which is the one outcome the whole design exists to prevent. Both are knowable in advance from
`debug_token`, so both are refused here rather than discovered at 19:00.

The two shapes that work:

* **Page token** — `type: PAGE`, `profile_id` equal to the Page id. What `/{page}/photos` wants.
* **System User token** — issued from Business Settings, carries no expiry, and is the right answer
  for a server that publishes unattended. A user-derived Page token expires and cannot be renewed
  without a person in a browser.
"""

import os
import sys
from datetime import UTC, datetime

import httpx

from brandcortex.adapters.channel.facebook import tokens
from brandcortex.adapters.channel.facebook.adapter import FacebookChannelAdapter
from brandcortex.config import get_settings
from brandcortex.db.session import session_scope

GRAPH = "https://graph.facebook.com"


def inspect(token: str, *, app_id: str, app_secret: str, version: str) -> dict:
    """What Graph says this token is. Uses an app token so it works on an invalid user token too."""
    response = httpx.get(
        f"{GRAPH}/{version}/debug_token",
        params={"input_token": token, "access_token": f"{app_id}|{app_secret}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", {})


def exchange_code(code: str, *, app_id: str, app_secret: str, redirect_uri: str, version: str) -> str:
    """Trade a Login-for-Business authorization code for an access token.

    The code is short-lived and single-use, and useless without the app secret — which is why the
    code may travel through a console or a chat while the token never should. This is the only place
    the secret is used for anything other than `appsecret_proof`.
    """
    response = httpx.get(
        f"{GRAPH}/{version}/oauth/access_token",
        params={
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=30,
    )
    body = response.json()
    if "access_token" not in body:
        error = (body.get("error") or {}).get("message", body)
        raise RuntimeError(f"code exchange failed: {error}")
    return body["access_token"]


def make_long_lived(token: str, *, app_id: str, app_secret: str, version: str) -> str:
    """Trade a short-lived user token for the 60-day one.

    This step is what makes the final Page token permanent. A Page token inherits its lifetime from
    the user token it was derived from: derive from the short-lived one and it dies in about an hour,
    derive from the long-lived one and it does not expire at all. The difference is one request, and
    getting it wrong would not show up until the token quietly stopped working.
    """
    response = httpx.get(
        f"{GRAPH}/{version}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": token,
        },
        timeout=30,
    )
    body = response.json()
    if "access_token" not in body:
        error = (body.get("error") or {}).get("message", body)
        raise RuntimeError(f"long-lived exchange failed: {error}")
    return body["access_token"]


def exchange_for_page_token(token: str, *, page_id: str, version: str) -> str | None:
    """Trade a user or System User token for the Page's own token.

    This is the step that catches people out. Business Settings hands you a *System User* token, and
    `/{page}/photos` will not accept it — you have to ask the Page for its own token, which the
    System User can do because the Page is assigned to it. The Page token inherits the System User's
    lack of expiry, so this is also how you end up with a credential that never needs renewing.

    Returns None when the exchange is not possible, leaving the caller to report why the original
    token was unusable rather than inventing a second failure.
    """
    try:
        response = httpx.get(
            f"{GRAPH}/{version}/{page_id}",
            params={"fields": "access_token", "access_token": token},
            timeout=30,
        )
        return response.json().get("access_token")
    except (httpx.HTTPError, ValueError):
        return None


def problems(data: dict, *, page_id: str) -> list[str]:
    """Every reason this token cannot publish, in words."""
    found: list[str] = []
    if not data.get("is_valid"):
        found.append("Graph reports the token is not valid")

    if data.get("type") != "PAGE":
        found.append(
            f"this is a {data.get('type', 'UNKNOWN')} token, not a PAGE token — "
            "/{page}/photos needs a Page token"
        )
    elif str(data.get("profile_id") or "") != str(page_id):
        found.append(
            f"the token belongs to Page {data.get('profile_id')}, not {page_id}"
        )

    granted = set(data.get("scopes") or [])
    missing = [s for s in FacebookChannelAdapter.REQUIRED_PERMISSIONS if s not in granted]
    if missing:
        found.append("missing permissions: " + ", ".join(missing))

    expires = data.get("expires_at")
    if expires:
        when = datetime.fromtimestamp(expires, UTC)
        if when <= datetime.now(UTC):
            found.append(f"expired on {when:%Y-%m-%d %H:%M} UTC")
    return found


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    code = os.environ.get("FACEBOOK_OAUTH_CODE", "").strip()
    redirect_uri = os.environ.get(
        "FACEBOOK_REDIRECT_URI", "https://thaiswim.com/oauth/callback"
    )

    if code:
        if not (settings.facebook_app_id and settings.facebook_app_secret):
            print("FACEBOOK_APP_ID and FACEBOOK_APP_SECRET must be set", file=sys.stderr)
            return 2
        token = exchange_code(
            code,
            app_id=settings.facebook_app_id,
            app_secret=settings.facebook_app_secret,
            redirect_uri=redirect_uri,
            version=settings.facebook_graph_version,
        )
        print("  exchanged the authorization code for a user token")
        token = make_long_lived(
            token,
            app_id=settings.facebook_app_id,
            app_secret=settings.facebook_app_secret,
            version=settings.facebook_graph_version,
        )
        print("  upgraded it to the long-lived user token")

    if not token:
        print(
            "set FACEBOOK_OAUTH_CODE (from the login dialog) or FACEBOOK_PAGE_ACCESS_TOKEN",
            file=sys.stderr,
        )
        return 2
    if not (settings.facebook_app_id and settings.facebook_app_secret and settings.facebook_page_id):
        print("FACEBOOK_APP_ID, FACEBOOK_APP_SECRET and FACEBOOK_PAGE_ID must all be set", file=sys.stderr)
        return 2

    data = inspect(
        token,
        app_id=settings.facebook_app_id,
        app_secret=settings.facebook_app_secret,
        version=settings.facebook_graph_version,
    )

    # A System User token is the recommended credential and is not itself a Page token. Trade it in
    # rather than making the operator find that out from a permissions error.
    if data.get("is_valid") and data.get("type") != "PAGE":
        exchanged = exchange_for_page_token(
            token, page_id=settings.facebook_page_id, version=settings.facebook_graph_version
        )
        if exchanged:
            print("  exchanged a user token for the Page's own token")
            token = exchanged
            data = inspect(
                token,
                app_id=settings.facebook_app_id,
                app_secret=settings.facebook_app_secret,
                version=settings.facebook_graph_version,
            )

    expires = data.get("expires_at")
    when = datetime.fromtimestamp(expires, UTC) if expires else None
    print(f"  type    : {data.get('type')}")
    print(f"  page    : {data.get('profile_id') or '—'}")
    print(f"  expires : {when.isoformat() if when else 'never'}")
    print(f"  scopes  : {len(data.get('scopes') or [])} granted")

    found = problems(data, page_id=settings.facebook_page_id)
    if found:
        print("\nNot stored:", file=sys.stderr)
        for problem in found:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    with session_scope() as session:
        brand = FacebookChannelAdapter.brand_for(session)
        tokens.store_page_token(
            session,
            brand,
            settings.facebook_page_id,
            token,
            expires_at=when,
            scopes=list(data.get("scopes") or []),
            token_kind="system_user_token" if when is None else "page_access_token",
        )
        session.commit()

    print(f"\nStored, encrypted, for {brand}. `GET /health/channels` should now be ok.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
