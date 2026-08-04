"""Symmetric encryption for channel credentials.

Fernet, keyed by `TOKEN_ENCRYPTION_KEY`. Used only by `channel_tokens` storage. Decrypted values must
never be logged, echoed in an exception, or returned by an API route.
"""


def encrypt(plaintext: str) -> bytes:
    """TODO(phase-1): Fernet encrypt using the configured key."""
    raise NotImplementedError


def decrypt(ciphertext: bytes) -> str:
    """TODO(phase-1): Fernet decrypt. Raise a message that does not contain the ciphertext."""
    raise NotImplementedError
