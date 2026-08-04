"""Page access token storage, retrieval, and refresh.

Long-lived Page tokens, encrypted at rest in `channel_tokens`, decrypted only at call time. A token
must never appear in a log line, an exception message, or an API response — the encryption is worth
nothing if a traceback prints the plaintext.
"""

from datetime import datetime


class TokenExpired(RuntimeError):
    pass


def get_page_token(brand: str, page_id: str) -> str:
    """Decrypt and return the current Page token, refreshing it if it is close to expiry.

    TODO(phase-1): read `channel_tokens`, decrypt with `services.crypto`, refresh when within the
    renewal window, and raise `TokenExpired` when refresh is no longer possible so a human is told
    rather than a scheduled publish failing silently at 3am.
    """
    raise NotImplementedError


def store_page_token(
    brand: str, page_id: str, token: str, *, expires_at: datetime | None, scopes: list[str]
) -> None:
    """Encrypt and persist a Page token. Records granted scopes, not requested ones."""
    raise NotImplementedError
