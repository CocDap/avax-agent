from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.control_plane.wallets.schemas import WalletBalances, WalletPolicy, WalletRead
from app.control_plane.wallets.service import WalletService
from app.core.security import CurrentUser
from app.db.session import DbSession

router = APIRouter(prefix="/agents/{agent_id}/wallet", tags=["wallets"])


@router.post("", response_model=WalletRead, status_code=status.HTTP_201_CREATED)
async def provision_wallet(agent_id: uuid.UUID, user: CurrentUser, db: DbSession) -> WalletRead:
    return await WalletService(db).provision(user.id, agent_id)


@router.get("", response_model=WalletRead)
async def get_wallet(agent_id: uuid.UUID, user: CurrentUser, db: DbSession) -> WalletRead:
    return await WalletService(db).get(user.id, agent_id)


@router.put("/policy", response_model=WalletRead)
async def update_policy(
    agent_id: uuid.UUID, body: WalletPolicy, user: CurrentUser, db: DbSession
) -> WalletRead:
    return await WalletService(db).update_policy(user.id, agent_id, body)


@router.get("/balances", response_model=WalletBalances)
async def get_balances(agent_id: uuid.UUID, user: CurrentUser, db: DbSession) -> WalletBalances:
    return await WalletService(db).balances(user.id, agent_id)
