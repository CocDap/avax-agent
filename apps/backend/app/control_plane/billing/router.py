from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.control_plane.billing.schemas import (
    EarningsSummary,
    FeeSchedule,
    LedgerEntryRead,
    PayoutCreate,
    PayoutRead,
)
from app.control_plane.billing.service import BillingService, fee_schedule
from app.core.security import CurrentUser
from app.db.session import DbSession

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/fees", response_model=FeeSchedule)
async def get_fees() -> FeeSchedule:
    return fee_schedule()


@router.get("/summary", response_model=EarningsSummary)
async def get_summary(
    user: CurrentUser, db: DbSession, agent_id: uuid.UUID | None = None
) -> EarningsSummary:
    return await BillingService(db).summary(user.id, agent_id)


@router.get("/ledger", response_model=list[LedgerEntryRead])
async def get_ledger(
    user: CurrentUser,
    db: DbSession,
    agent_id: uuid.UUID | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[LedgerEntryRead]:
    return await BillingService(db).ledger(user.id, agent_id, limit, offset)


@router.post("/payouts", response_model=PayoutRead, status_code=status.HTTP_202_ACCEPTED)
async def request_payout(body: PayoutCreate, user: CurrentUser, db: DbSession) -> PayoutRead:
    return await BillingService(db).request_payout(user.id, body)


@router.get("/payouts", response_model=list[PayoutRead])
async def list_payouts(user: CurrentUser, db: DbSession) -> list[PayoutRead]:
    return await BillingService(db).list_payouts(user.id)
