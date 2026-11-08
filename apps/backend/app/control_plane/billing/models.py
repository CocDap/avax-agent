from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.model_base import Base, Timestamps, TokenAmount, UUIDPrimaryKey


class LedgerKind(str, Enum):
    INCOME = "income"  # client payment received (x402 transfer or ERC-8183 settle)
    STUDIO_FEE = "studio_fee"  # studio cut, settings.studio_fee_bps
    PAYOUT = "payout"  # withdrawal to the owner
    GAS = "gas"  # AVAX spent by the agent wallet (informational)


class PayoutStatus(str, Enum):
    REQUESTED = "requested"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class LedgerEntry(UUIDPrimaryKey, Timestamps, Base):
    """Append-only, double-entry-friendly record of value movements."""

    __tablename__ = "ledger_entries"

    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    kind: Mapped[LedgerKind] = mapped_column(SAEnum(LedgerKind, native_enum=False))
    asset: Mapped[str] = mapped_column(String(42))  # token address, or "AVAX"
    amount_atomic: Mapped[int] = mapped_column(TokenAmount)
    chain_id: Mapped[int] = mapped_column(BigInteger)
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)


class Payout(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "payouts"

    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    destination: Mapped[str] = mapped_column(String(42))
    asset: Mapped[str] = mapped_column(String(42))
    amount_atomic: Mapped[int] = mapped_column(TokenAmount)
    status: Mapped[PayoutStatus] = mapped_column(
        SAEnum(PayoutStatus, native_enum=False), default=PayoutStatus.REQUESTED
    )
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
