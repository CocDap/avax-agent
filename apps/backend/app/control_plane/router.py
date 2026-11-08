"""Aggregate control-plane router mounted at ``settings.api_prefix``."""

from fastapi import APIRouter

from app.control_plane.agents.router import marketplace_router
from app.control_plane.agents.router import router as agents_router
from app.control_plane.billing.router import router as billing_router
from app.control_plane.jobs.router import router as jobs_router
from app.control_plane.registry.router import router as registry_router
from app.control_plane.wallets.router import router as wallets_router

api_router = APIRouter()
api_router.include_router(agents_router)
api_router.include_router(marketplace_router)
api_router.include_router(wallets_router)
api_router.include_router(registry_router)
api_router.include_router(billing_router)
api_router.include_router(jobs_router)
