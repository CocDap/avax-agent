"""Ledger aggregation and payouts. TODO: implement.

Payout = ERC-20 ``transfer`` of the payment asset from the agent wallet
(Turnkey signer, gas in AVAX) to the owner's address, after reserving the
studio fee (sent to ``STUDIO_TREASURY_ADDRESS``).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.chain import network as net
from app.control_plane.billing.schemas import (
    EarningsSummary,
    FeeSchedule,
    LedgerEntryRead,
    PayoutCreate,
    PayoutRead,
)
from app.core.config import settings
from app.core.errors import NotImplementedYet


def fee_schedule() -> FeeSchedule:
    return FeeSchedule(
        studio_fee_bps=settings.studio_fee_bps,
        payment_asset=settings.payment_asset,
        payment_asset_address=net.payment_asset_address(),
        chain_id=net.chain_id(),
    )


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summary(self, owner_id: str, agent_id: uuid.UUID | None) -> EarningsSummary:
        raise NotImplementedYet("billing.summary")

    async def ledger(
        self, owner_id: str, agent_id: uuid.UUID | None, limit: int, offset: int
    ) -> list[LedgerEntryRead]:
        raise NotImplementedYet("billing.ledger")

    async def request_payout(self, owner_id: str, req: PayoutCreate) -> PayoutRead:
        raise NotImplementedYet("billing.request_payout")

    async def list_payouts(self, owner_id: str) -> list[PayoutRead]:
        raise NotImplementedYet("billing.list_payouts")
