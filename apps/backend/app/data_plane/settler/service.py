"""Settle loop. TODO: implement.

* erc8183 mode: for SUBMITTED jobs past the OptimisticPolicy dispute window,
  call the permissionless ``router.settle(jobId)`` (any funded key; gas in
  AVAX), record SETTLED + ledger INCOME / STUDIO_FEE.
* x402 mode: payment is already settled by the facilitator at request time,
  so the bot only reconciles (marks SETTLED once the USDC transfer is seen by
  the indexer).
"""

from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.core.errors import NotImplementedYet

log = logging.getLogger(__name__)


class SettleBot:
    poll_interval_s: float = 30.0

    async def tick(self) -> None:
        raise NotImplementedYet("settler.tick")

    async def run(self) -> None:
        log.info("settle bot starting (erc8183 enabled=%s)", settings.commerce_enabled)
        while True:
            await self.tick()
            await asyncio.sleep(self.poll_interval_s)
