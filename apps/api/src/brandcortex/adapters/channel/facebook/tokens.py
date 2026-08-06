"""Page access token storage, retrieval, and refresh.

Long-lived Page tokens, encrypted at rest in `channel_tokens`, decrypted only at call time. A token
must never appear in a log line, an exception message, or an API response — the encryption is worth
nothing if a traceback prints the plaintext.

## On expiry

A System User token does not expire, and that is the recommended way to run a server publisher. A
Page token minted from a user login expires, and Meta offers no unattended refresh once it has: the
long-lived exchange needs a user access token, which needs a person in a browser. So this module does
not pretend to auto-renew. It warns while there is still time to act, and raises `TokenExpired` with
the date rather than letting a scheduled publish fail at 3am with a Graph code.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from brandcortex.db.models import ChannelToken
from brandcortex.services import crypto

logger = logging.getLogger(__name__)

CHANNEL = "facebook"

#: Warn this far ahead. Long enough that a person can act without it being urgent, short enough that
#: the warning still means something when it appears.
RENEWAL_WINDOW = timedelta(days=14)


class TokenExpired(RuntimeError):
    """The stored token can no longer publish. A person must re-authorize."""


class TokenMissing(LookupError):
    """No token stored for this brand and Page."""


def get_page_token(session: Session, brand: str, page_id: str, *, now: datetime | None = None) -> str:
    """Decrypt and return the current Page token.

    Raises rather than returning something unusable: a caller that receives an expired token makes a
    Graph call that fails with a code, and the reason gets buried in a retry.
    """
    row = _row(session, brand, page_id)
    at = now or datetime.now(UTC)

    if row.expires_at is not None:
        expires = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=UTC)
        if expires <= at:
            raise TokenExpired(
                f"the {brand} Page token expired on {expires:%Y-%m-%d}; re-authorize the Page"
            )
        if expires - at <= RENEWAL_WINDOW:
            logger.warning(
                "%s Page token expires on %s — a System User token would not", brand, f"{expires:%Y-%m-%d}"
            )

    return crypto.decrypt(row.encrypted_token)


def expires_at(session: Session, brand: str, page_id: str) -> datetime | None:
    """When the stored token runs out, or None if it never does. For the health surface."""
    return _row(session, brand, page_id).expires_at


def granted_scopes(session: Session, brand: str, page_id: str) -> list[str]:
    """What was actually granted, which is not always what was asked for."""
    return list(_row(session, brand, page_id).scopes or [])


def store_page_token(
    session: Session,
    brand: str,
    page_id: str,
    token: str,
    *,
    expires_at: datetime | None,
    scopes: list[str],
    token_kind: str = "page_access_token",
) -> ChannelToken:
    """Encrypt and persist a Page token. Records granted scopes, not requested ones.

    Upserts on (brand, channel, account_ref): re-authorizing replaces the token rather than leaving
    two rows where a later read picks arbitrarily.
    """
    row = session.scalar(
        select(ChannelToken).where(
            ChannelToken.brand == brand,
            ChannelToken.channel == CHANNEL,
            ChannelToken.account_ref == page_id,
        )
    )
    if row is None:
        row = ChannelToken(brand=brand, channel=CHANNEL, account_ref=page_id)
        session.add(row)

    row.encrypted_token = crypto.encrypt(token)
    row.token_kind = token_kind
    row.expires_at = expires_at
    row.scopes = list(scopes)
    row.refreshed_at = datetime.now(UTC)
    session.flush()
    logger.info("stored %s Page token for %s (%d scopes)", token_kind, page_id, len(scopes))
    return row


def _row(session: Session, brand: str, page_id: str) -> ChannelToken:
    row = session.scalar(
        select(ChannelToken).where(
            ChannelToken.brand == brand,
            ChannelToken.channel == CHANNEL,
            ChannelToken.account_ref == page_id,
        )
    )
    if row is None:
        raise TokenMissing(f"no {CHANNEL} token stored for {brand}/{page_id}")
    return row
