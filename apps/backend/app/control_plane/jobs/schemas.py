from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.control_plane.jobs.models import JobStatus
from app.core.config import SettlementMode


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    settlement_mode: SettlementMode
    status: JobStatus
    chain_id: int
    chain_job_id: int | None
    client_address: str | None
    amount_atomic: int
    asset: str
    deliverable_uri: str | None
    payment_tx_hash: str | None
    submit_tx_hash: str | None
    settle_tx_hash: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class JobEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    message: str
    data: dict
    created_at: datetime
