"""Turnkey sub-org provisioning + policy management. TODO: implement.

Flow for ``provision``:
1. Create a Turnkey sub-organization under the studio's parent org
   (``TURNKEY_ORGANIZATION_ID``) with a non-root API user for the agent.
2. Create an Ethereum wallet account in the sub-org -> agent address.
3. Install an ALLOW policy derived from ``WalletPolicy`` (root keys bypass
   policies, so the agent must never use a root key).
4. Persist ``Wallet`` and link it to the agent; build signers at runtime with
   ``avaxagent.wallets.TurnkeyWalletProvider(..., expected_chain_id=chain_id())``.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.control_plane.wallets.schemas import WalletBalances, WalletPolicy, WalletRead
from app.core.errors import NotImplementedYet


class WalletService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def provision(self, owner_id: str, agent_id: uuid.UUID) -> WalletRead:
        raise NotImplementedYet("wallets.provision")

    async def get(self, owner_id: str, agent_id: uuid.UUID) -> WalletRead:
        raise NotImplementedYet("wallets.get")

    async def update_policy(
        self, owner_id: str, agent_id: uuid.UUID, policy: WalletPolicy
    ) -> WalletRead:
        raise NotImplementedYet("wallets.update_policy")

    async def balances(self, owner_id: str, agent_id: uuid.UUID) -> WalletBalances:
        """AVAX (gas) + payment asset balance, e.g. via avaxagent MinimalERC20Client."""
        raise NotImplementedYet("wallets.balances")
