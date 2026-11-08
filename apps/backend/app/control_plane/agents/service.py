"""Agent config persistence. TODO: implement with SQLAlchemy queries."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.control_plane.agents.schemas import (
    AgentCreate,
    AgentRead,
    AgentUpdate,
    MarketplaceAgent,
)
from app.core.errors import NotImplementedYet


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, owner_id: str, data: AgentCreate) -> AgentRead:
        """Insert a DRAFT agent on the configured chain (no wallet/identity yet)."""
        raise NotImplementedYet("agents.create")

    async def list_for_owner(self, owner_id: str) -> list[AgentRead]:
        raise NotImplementedYet("agents.list")

    async def get(self, owner_id: str, agent_id: uuid.UUID) -> AgentRead:
        raise NotImplementedYet("agents.get")

    async def update(self, owner_id: str, agent_id: uuid.UUID, data: AgentUpdate) -> AgentRead:
        """Patch config; changing public profile fields should refresh the agent URI."""
        raise NotImplementedYet("agents.update")

    async def delete(self, owner_id: str, agent_id: uuid.UUID) -> None:
        """Soft-delete / pause. The ERC-8004 token itself cannot be burned by the studio."""
        raise NotImplementedYet("agents.delete")

    async def marketplace(self, q: str | None, limit: int, offset: int) -> list[MarketplaceAgent]:
        """Public ACTIVE agents; may later merge 8004scan results for Avalanche."""
        raise NotImplementedYet("marketplace.list")
