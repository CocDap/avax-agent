from __future__ import annotations

from pydantic import BaseModel


class RegistrationRequest(BaseModel):
    """Optional overrides; by default the URI is built from the agent config."""

    image_url: str | None = None
    extra_metadata: dict[str, str] = {}


class RegistrationStatus(BaseModel):
    chain_id: int
    identity_registry: str
    state: str  # not_registered | pending | registered | failed
    erc8004_agent_id: int | None = None
    agent_uri: str | None = None
    tx_hash: str | None = None
    explorer_url: str | None = None


class NetworkInfo(BaseModel):
    network: str
    chain_id: int
    rpc_url: str
    explorer_url: str
    identity_registry: str
    payment_asset: str
    payment_asset_address: str
    erc8183_enabled: bool
