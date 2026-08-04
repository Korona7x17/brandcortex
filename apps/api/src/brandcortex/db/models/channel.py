"""Channel credentials: `channel_tokens` (spec §5.2).

BrandCortex carries every channel permission; brand sites carry none. Tokens are encrypted at rest with
`TOKEN_ENCRYPTION_KEY`, decrypted only inside a channel adapter at call time, and must never be logged
or returned by an API route.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from brandcortex.db.base import Base, TimestampMixin


class ChannelToken(Base, TimestampMixin):
    __tablename__ = "channel_tokens"
    __table_args__ = (
        UniqueConstraint("brand", "channel", "account_ref", name="uq_channel_tokens_account"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)

    # Channel-side account identity, e.g. a Facebook Page id.
    account_ref: Mapped[str] = mapped_column(String(128), nullable=False)

    # Fernet ciphertext. Never a plaintext column, and never widened to one "just for debugging".
    encrypted_token: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    token_kind: Mapped[str] = mapped_column(String(32), default="page_access_token")

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Granted scopes and refresh bookkeeping. Meta's required permissions shift between Graph versions,
    # so record what was actually granted rather than assuming what was requested.
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    refresh_meta: Mapped[dict] = mapped_column(JSON, default=dict)

    def __repr__(self) -> str:  # pragma: no cover - never expose the secret in logs or tracebacks
        return f"<ChannelToken {self.brand}/{self.channel}/{self.account_ref}>"
