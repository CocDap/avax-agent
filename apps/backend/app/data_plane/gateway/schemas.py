from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JsonRpcRequest(BaseModel):
    """A2A uses JSON-RPC 2.0 (``message/send``, ``tasks/get``, ...)."""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class X402Accept(BaseModel):
    """One entry of an HTTP 402 ``accepts[]`` challenge (scheme ``exact``)."""

    scheme: str = "exact"
    network: str  # CAIP-2, e.g. eip155:43113
    asset: str  # Avalanche USDC address
    payTo: str  # agent wallet address  # noqa: N815 (x402 wire format)
    amount: str
    maxTimeoutSeconds: int = 300  # noqa: N815
    extra: dict[str, str] = Field(default_factory=dict)  # EIP-712 name/version
