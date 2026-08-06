"""Symmetric encryption for channel credentials.

Fernet, keyed by `TOKEN_ENCRYPTION_KEY`. Used only by `channel_tokens` storage. Decrypted values must
never be logged, echoed in an exception, or returned by an API route.

The failure message below says nothing about its inputs on purpose. A decrypt error is nearly always
a rotated or mismatched key, and the ciphertext adds nothing to that diagnosis while adding a copy of
the secret to every log aggregator the traceback passes through.
"""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from brandcortex.config import get_settings


class TokenDecryptionError(RuntimeError):
    """Ciphertext could not be decrypted. Never carries the ciphertext or the key."""


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().token_encryption_key
    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is not a valid Fernet key; generate one with "
            '`python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"`'
        ) from exc


def encrypt(plaintext: str) -> bytes:
    return _fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes) -> str:
    try:
        return _fernet().decrypt(ciphertext).decode("utf-8")
    except InvalidToken as exc:
        raise TokenDecryptionError(
            "stored channel token could not be decrypted — TOKEN_ENCRYPTION_KEY has most likely "
            "changed since it was written; re-authorize the channel rather than guessing at keys"
        ) from exc
