"""Top-level SDK configuration.

Exports:

- :class:`NetworkConfig` — per-network defaults (RPC + contract addresses for
  every module that uses on-chain state).
- :func:`resolve_network` — looks up a preset by name, with an optional
  ``RPC_URL`` env override. **Module-specific contract overrides live in
  their own module configs** (e.g. ``get_erc8004_config``), not here.

Networks
--------
- ``avalanche-fuji``    — Avalanche Fuji testnet C-Chain (chain id 43113)
- ``avalanche-mainnet`` — Avalanche mainnet C-Chain (chain id 43114)

Env var surface
---------------
``resolve_network`` is intentionally narrow: it only reads ``RPC_URL`` /
``RPC_URL_<NETWORK>``. Module-scoped env vars (``ERC8004_REGISTRY_ADDRESS``,
``STORAGE_*``, ...) are owned by the corresponding module config. The
project ``.env.example`` is the authoritative reference.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace

from .core.config import get_env
from .networks.addresses import (
    AVALANCHE_FUJI_CHAIN_ID,
    AVALANCHE_MAINNET_CHAIN_ID,
    get_address,
)

logger = logging.getLogger(__name__)

DEFAULT_NETWORK = "avalanche-fuji"


@dataclass
class NetworkConfig:
    """Per-network configuration with all protocol addresses.

    Gas is always self-paid in AVAX: Avalanche has no protocol-level
    paymaster equivalent to BNB Chain's MegaFuel, so this fork carries no
    sponsorship settings.
    """

    name: str
    chain_id: int
    rpc_url: str
    # ERC-8004 Identity Registry
    registry_contract: str = ""
    # Block explorer base URL (informational; used in logs / examples).
    explorer_url: str = ""


NETWORKS: dict[str, NetworkConfig] = {
    "avalanche-fuji": NetworkConfig(
        name="avalanche-fuji",
        chain_id=AVALANCHE_FUJI_CHAIN_ID,
        rpc_url="https://api.avax-test.network/ext/bc/C/rpc",
        registry_contract=get_address(AVALANCHE_FUJI_CHAIN_ID).identity_registry,
        explorer_url="https://testnet.snowtrace.io",
    ),
    "avalanche-mainnet": NetworkConfig(
        name="avalanche-mainnet",
        chain_id=AVALANCHE_MAINNET_CHAIN_ID,
        rpc_url="https://api.avax.network/ext/bc/C/rpc",
        registry_contract=get_address(AVALANCHE_MAINNET_CHAIN_ID).identity_registry,
        explorer_url="https://snowtrace.io",
    ),
}


def resolve_network(network: str | NetworkConfig = DEFAULT_NETWORK) -> NetworkConfig:
    """Resolve a network preset to a concrete ``NetworkConfig``.

    Accepts either a preset name (``"avalanche-fuji"`` / ``"avalanche-mainnet"``)
    or a concrete ``NetworkConfig`` instance:

    - **String** → look up the preset; apply the RPC env override if set.
      Module-scoped contract-address envs (``ERC8004_*``) are NOT read here —
      they belong to each module's own config loader.
    - **NetworkConfig** → returned as-is; env vars are never applied (fully
      explicit control is the point of passing an object).

    RPC override precedence (a process that touches several networks needs
    per-network pins — a single shared URL would silently apply to the wrong
    chain):

    1. ``RPC_URL_<NETWORK>`` — per-network, e.g. ``RPC_URL_AVALANCHE_FUJI`` /
       ``RPC_URL_AVALANCHE_MAINNET`` (preset name uppercased, ``-`` → ``_``).
    2. ``RPC_URL`` — global, network-agnostic.
    3. The preset default.
    """
    if isinstance(network, NetworkConfig):
        return network

    nc = NETWORKS.get(network)
    if nc is None:
        raise ValueError(f"Unknown network: {network}. Known: {sorted(NETWORKS)}")

    per_network_key = f"RPC_URL_{nc.name.upper().replace('-', '_')}"
    rpc_override = get_env(per_network_key) or get_env("RPC_URL")
    if rpc_override:
        return replace(nc, rpc_url=rpc_override)
    return nc
