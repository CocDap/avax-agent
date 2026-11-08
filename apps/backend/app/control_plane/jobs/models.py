from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import SettlementMode
from app.db.model_base import Base, Timestamps, TokenAmount, UUIDPrimaryKey


class JobStatus(str, Enum):
    NEGOTIATING = "negotiating"  # A2A negotiate in progress
    FUNDED = "funded"  # x402 payment verified / ERC-8183 JobFunded seen
    RUNNING = "running"  # worker executing the LLM task
    SUBMITTED = "submitted"  # deliverable stored (+ submitted on-chain for 8183)
    SETTLED = "settled"  # payment final (x402 settled / router.settle)
    FAILED = "failed"
    REFUNDED = "refunded"  # ERC-8183 claimRefund after expiry


class Job(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "jobs"

    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    settlement_mode: Mapped[SettlementMode] = mapped_column(
        SAEnum(SettlementMode, native_enum=False)
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, native_enum=False), default=JobStatus.NEGOTIATING
    )
    chain_id: Mapped[int] = mapped_column(BigInteger)
    chain_job_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # ERC-8183
    client_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    amount_atomic: Mapped[int] = mapped_column(TokenAmount, default=0)
    asset: Mapped[str] = mapped_column(String(42))

    request: Mapped[dict] = mapped_column(JSON, default=dict)  # task input from A2A
    deliverable_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    deliverable_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    payment_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    submit_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    settle_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class JobEvent(UUIDPrimaryKey, Timestamps, Base):
    """Timeline entry for the job log UI."""

    __tablename__ = "job_events"

    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    type: Mapped[str] = mapped_column(String(64))  # e.g. funded, llm_started, submitted
    message: Mapped[str] = mapped_column(Text, default="")
    data: Mapped[dict] = mapped_column(JSON, default=dict)
