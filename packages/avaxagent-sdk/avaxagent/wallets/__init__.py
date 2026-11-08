"""
Wallet Providers Module

Abstract wallet provider interface and implementations.
Supports multiple wallet types (EVM keystore, Turnkey enclave, MPC stub)
through a unified interface.

The upstream BNB Chain SDK's TWAK (Trust Wallet Agent Kit) provider is not
part of this Avalanche fork: the twak CLI only supports BNB Smart Chain.
"""

from __future__ import annotations

from . import capabilities
from .errors import UnsupportedWalletOperation, WalletIdentityMismatch
from .evm_wallet_provider import EVMWalletProvider
from .factory import SUPPORTED_WALLET_KINDS, create_wallet_provider
from .intents import ExecutionContext, Intent, IntentExecutor
from .mpc_wallet_provider import MPCWalletProvider
from .protocols import MessageSigner, TypedDataSigner
from .turnkey import TurnkeyWalletProvider
from .wallet_provider import WalletProvider

__all__ = [
    "WalletProvider",
    "EVMWalletProvider",
    "MPCWalletProvider",
    "TurnkeyWalletProvider",
    "UnsupportedWalletOperation",
    "WalletIdentityMismatch",
    "MessageSigner",
    "TypedDataSigner",
    "capabilities",
    "Intent",
    "IntentExecutor",
    "ExecutionContext",
    "create_wallet_provider",
    "SUPPORTED_WALLET_KINDS",
]
