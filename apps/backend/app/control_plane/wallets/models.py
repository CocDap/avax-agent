from __future__ import annotations

from sqlalchemy import JSON, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.model_base import Base, Timestamps, UUIDPrimaryKey


class Wallet(UUIDPrimaryKey, Timestamps, Base):
    """Agent wallet. Keys live in Turnkey's enclave; the studio stores references only."""

    __tablename__ = "wallets"

    provider: Mapped[str] = mapped_column(String(32), default="turnkey")
    turnkey_sub_org_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    turnkey_wallet_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    address: Mapped[str] = mapped_column(String(42), unique=True)
    chain_id: Mapped[int] = mapped_column(BigInteger)

    # Mirrors both the Turnkey server-side policy and the SDK SigningPolicy.
    policy: Mapped[dict] = mapped_column(JSON, default=dict)
