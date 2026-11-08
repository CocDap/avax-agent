"""Indexer loop. TODO: implement.

Per enabled stream: read ``IndexerCursor``, ``eth_getLogs`` from
``last_block + 1`` to ``head - INDEXER_CONFIRMATIONS`` in bounded ranges
(public C-Chain RPCs cap the range), decode, filter to managed agents, write
rows / enqueue work, then advance the cursor in the same DB transaction.
"""

from __future__ import annotations

import asyncio
import logging

from app.chain import network as net
from app.core.errors import NotImplementedYet
from app.data_plane.indexer.streams import streams

log = logging.getLogger(__name__)


class ChainIndexer:
    poll_interval_s: float = 2.0  # C-Chain block time is ~1-2 s

    async def tick(self) -> None:
        raise NotImplementedYet("indexer.tick")

    async def run(self) -> None:
        enabled = [s.name for s in streams() if s.enabled]
        log.info("indexer starting on chain %s, streams=%s", net.chain_id(), enabled)
        while True:
            await self.tick()
            await asyncio.sleep(self.poll_interval_s)
