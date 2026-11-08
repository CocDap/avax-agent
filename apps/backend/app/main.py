"""Control-plane API.

Run: ``uvicorn app.main:app --reload --port 8000`` (docs at ``/docs``).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.chain import network as net
from app.control_plane.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(title=f"{settings.app_name} API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "network": settings.network,
            "chain_id": net.chain_id(),
            "erc8183_enabled": settings.commerce_enabled,
        }

    return app


app = create_app()
