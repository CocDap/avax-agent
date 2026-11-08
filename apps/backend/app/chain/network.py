"""Resolve the configured Avalanche network via the avaxagent SDK."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache

from avaxagent.config import NetworkConfig, resolve_network
from avaxagent.networks import AssetId, get_address, get_x402_asset, resolve_asset_alias

from app.core.config import settings


@lru_cache
def network() -> NetworkConfig:
    """Network preset (``avalanche-fuji`` / ``avalanche-mainnet``), RPC overridable."""
    nc = resolve_network(settings.network)
    return replace(nc, rpc_url=settings.rpc_url) if settings.rpc_url else nc


def chain_id() -> int:
    return network().chain_id


def identity_registry() -> str:
    """ERC-8004 Identity Registry (live on both Avalanche chains)."""
    return get_address(chain_id()).identity_registry


def payment_asset_id() -> AssetId:
    """Per-chain canonical id for the configured alias (USDC → FUJI_USDC on Fuji)."""
    return resolve_asset_alias(chain_id(), settings.payment_asset)


def payment_asset_address() -> str:
    return get_x402_asset(chain_id(), payment_asset_id()).address


def caip2() -> str:
    """CAIP-2 network id used in x402 challenges, e.g. ``eip155:43113``."""
    return f"eip155:{chain_id()}"
