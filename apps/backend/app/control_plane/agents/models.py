from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import SettlementMode
from app.db.model_base import Base, Timestamps, TokenAmount, UUIDPrimaryKey


class AgentStatus(str, Enum):
    DRAFT = "draft"  # config saved, no wallet / identity yet
    PROVISIONING = "provisioning"  # Turnkey sub-org + wallet being created
    REGISTERING = "registering"  # ERC-8004 register tx in flight
    ACTIVE = "active"  # discoverable, accepting jobs
    PAUSED = "paused"


class Agent(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "agents"

    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)  # /agents/{slug}/...
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[AgentStatus] = mapped_column(
        SAEnum(AgentStatus, native_enum=False), default=AgentStatus.DRAFT
    )
    is_public: Mapped[bool] = mapped_column(default=False)  # listed in marketplace

    # Runtime behaviour (system prompt, model, tools) consumed by job workers.
    llm_config: Mapped[dict] = mapped_column(JSON, default=dict)
    skills: Mapped[list] = mapped_column(JSON, default=list)

    # Pricing in the payment asset's atomic units (USDC: 6 decimals).
    settlement_mode: Mapped[SettlementMode] = mapped_column(
        SAEnum(SettlementMode, native_enum=False), default=SettlementMode.X402
    )
    price_atomic: Mapped[int] = mapped_column(TokenAmount, default=0)

    # On-chain identity (ERC-8004 on Avalanche C-Chain).
    chain_id: Mapped[int] = mapped_column(BigInteger)
    erc8004_agent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    agent_uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    wallet_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("wallets.id", ondelete="SET NULL"), nullable=True
    )
