"""Factories wiring avaxagent SDK objects to studio settings."""

from __future__ import annotations

from avaxagent import ERC8004Agent, WalletProvider
from avaxagent.core import create_web3  # noqa: F401  (re-export for workers)

from app.chain.network import network


def erc8004_agent(wallet: WalletProvider) -> ERC8004Agent:
    """ERC-8004 client bound to the configured Avalanche network."""
    return ERC8004Agent(wallet_provider=wallet, network=network())
