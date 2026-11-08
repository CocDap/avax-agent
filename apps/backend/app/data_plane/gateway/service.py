"""Gateway logic. TODO: implement.

* ``agent_card``: build the A2A agent card from the agent config (name,
  skills, ``url = {PUBLIC_GATEWAY_URL}/agents/{slug}/a2a``) and advertise the
  ERC-8004 identity (``eip155:{chain_id}:{registry}`` + agentId).
* ``handle_a2a``:
    - ``negotiate``: quote price / terms from the agent config.
    - x402 mode: without ``X-PAYMENT`` answer 402 with ``X402Accept``
      (Avalanche USDC, EIP-3009); with it, verify + settle through a
      facilitator, create a FUNDED ``Job`` and enqueue ``RUN_JOB``.
    - erc8183 mode: return the commerce job params; the indexer picks up
      ``JobFunded`` (requires the studio-deployed contracts).
"""

from __future__ import annotations

from typing import Any

from app.core.errors import NotImplementedYet
from app.data_plane.gateway.schemas import JsonRpcRequest


async def agent_card(slug: str) -> dict[str, Any]:
    raise NotImplementedYet("gateway.agent_card")


async def handle_a2a(slug: str, req: JsonRpcRequest, x_payment: str | None) -> dict[str, Any]:
    raise NotImplementedYet("gateway.a2a")
