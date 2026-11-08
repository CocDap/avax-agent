"""ERC-8004 registration. TODO: implement.

``register`` should:
1. build the registration file with ``ERC8004Agent.generate_agent_uri`` using
   ``AgentEndpoint.a2a(f"{PUBLIC_GATEWAY_URL}/agents/{slug}")``,
2. optionally pin it via the storage service (``ipfs://`` URI),
3. enqueue ``REGISTER_AGENT`` so the tx (paid in AVAX by the agent wallet)
   runs in a worker, not in the request,
4. store ``erc8004_agent_id`` + tx hash once mined.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.chain import network as net
from app.control_plane.registry.schemas import (
    NetworkInfo,
    RegistrationRequest,
    RegistrationStatus,
)
from app.core.config import settings
from app.core.errors import NotImplementedYet


def network_info() -> NetworkInfo:
    """Static chain facts (works without DB / RPC)."""
    nc = net.network()
    return NetworkInfo(
        network=nc.name,
        chain_id=nc.chain_id,
        rpc_url=nc.rpc_url,
        explorer_url=nc.explorer_url,
        identity_registry=net.identity_registry(),
        payment_asset=settings.payment_asset,
        payment_asset_address=net.payment_asset_address(),
        erc8183_enabled=settings.commerce_enabled,
    )


class RegistryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(
        self, owner_id: str, agent_id: uuid.UUID, req: RegistrationRequest
    ) -> RegistrationStatus:
        raise NotImplementedYet("registry.register")

    async def status(self, owner_id: str, agent_id: uuid.UUID) -> RegistrationStatus:
        raise NotImplementedYet("registry.status")

    async def refresh_uri(self, owner_id: str, agent_id: uuid.UUID) -> RegistrationStatus:
        """Push an updated profile with ``ERC8004Agent.set_agent_uri``."""
        raise NotImplementedYet("registry.refresh_uri")
