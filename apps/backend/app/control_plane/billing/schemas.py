from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.control_plane.billing.models import LedgerKind, PayoutStatus


class FeeSchedule(BaseModel):
    studio_fee_bps: int
    payment_asset: str
    payment_asset_address: str
    chain_id: int


class EarningsSummary(BaseModel):
    agent_id: uuid.UUID | None = None  # None = all agents of the owner
    gross_income_atomic: int
    studio_fees_atomic: int
    paid_out_atomic: int
    withdrawable_atomic: int


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    job_id: uuid.UUID | None
    kind: LedgerKind
    asset: str
    amount_atomic: int
    tx_hash: str | None
    created_at: datetime


class PayoutCreate(BaseModel):
    agent_id: uuid.UUID
    destination: str = Field(pattern=r"^0x[0-9a-fA-F]{40}$")
    amount_atomic: int = Field(gt=0)


class PayoutRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    destination: str
    asset: str
    amount_atomic: int
    status: PayoutStatus
    tx_hash: str | None
    created_at: datetime
