"""A2A gateway ASGI app (separate process from the control-plane API).

Run: ``uvicorn app.data_plane.gateway.main:app --port 8001``
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header

from app.chain import network as net
from app.core.errors import register_exception_handlers
from app.data_plane.gateway import service
from app.data_plane.gateway.schemas import JsonRpcRequest

app = FastAPI(title="Avaxagent Studio A2A Gateway", version="0.1.0")
register_exception_handlers(app)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "gateway", "chain_id": net.chain_id()}


@app.get("/agents/{slug}/.well-known/agent-card.json")
async def agent_card(slug: str) -> dict[str, Any]:
    return await service.agent_card(slug)


@app.post("/agents/{slug}/a2a")
async def a2a(
    slug: str,
    body: JsonRpcRequest,
    x_payment: str | None = Header(default=None, alias="X-PAYMENT"),
) -> dict[str, Any]:
    return await service.handle_a2a(slug, body, x_payment)
