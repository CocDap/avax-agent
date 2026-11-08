from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.control_plane.agents.schemas import (
    AgentCreate,
    AgentRead,
    AgentUpdate,
    MarketplaceAgent,
)
from app.control_plane.agents.service import AgentService
from app.core.security import CurrentUser
from app.db.session import DbSession

router = APIRouter(prefix="/agents", tags=["agents"])
marketplace_router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(body: AgentCreate, user: CurrentUser, db: DbSession) -> AgentRead:
    return await AgentService(db).create(user.id, body)


@router.get("", response_model=list[AgentRead])
async def list_agents(user: CurrentUser, db: DbSession) -> list[AgentRead]:
    return await AgentService(db).list_for_owner(user.id)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: uuid.UUID, user: CurrentUser, db: DbSession) -> AgentRead:
    return await AgentService(db).get(user.id, agent_id)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: uuid.UUID, body: AgentUpdate, user: CurrentUser, db: DbSession
) -> AgentRead:
    return await AgentService(db).update(user.id, agent_id, body)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    await AgentService(db).delete(user.id, agent_id)


@marketplace_router.get("/agents", response_model=list[MarketplaceAgent])
async def marketplace_agents(
    db: DbSession,
    q: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
) -> list[MarketplaceAgent]:
    return await AgentService(db).marketplace(q, limit, offset)
