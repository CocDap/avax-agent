from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.control_plane.registry.schemas import (
    NetworkInfo,
    RegistrationRequest,
    RegistrationStatus,
)
from app.control_plane.registry.service import RegistryService, network_info
from app.core.security import CurrentUser
from app.db.session import DbSession

router = APIRouter(tags=["registry"])


@router.get("/network", response_model=NetworkInfo)
async def get_network() -> NetworkInfo:
    return network_info()


@router.post(
    "/agents/{agent_id}/registration",
    response_model=RegistrationStatus,
    status_code=status.HTTP_202_ACCEPTED,
)
async def register_agent(
    agent_id: uuid.UUID, body: RegistrationRequest, user: CurrentUser, db: DbSession
) -> RegistrationStatus:
    return await RegistryService(db).register(user.id, agent_id, body)


@router.get("/agents/{agent_id}/registration", response_model=RegistrationStatus)
async def registration_status(
    agent_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> RegistrationStatus:
    return await RegistryService(db).status(user.id, agent_id)


@router.post("/agents/{agent_id}/registration/refresh-uri", response_model=RegistrationStatus)
async def refresh_uri(agent_id: uuid.UUID, user: CurrentUser, db: DbSession) -> RegistrationStatus:
    return await RegistryService(db).refresh_uri(user.id, agent_id)
