"""
AvaxAgent SDK — Python toolkit for building on-chain AI agents on Avalanche.

Avalanche C-Chain fork of the BNB Chain ``bnbagent`` SDK. Networks:
``avalanche-fuji`` (43113, default) and ``avalanche-mainnet`` (43114).

Tier 1 (public API — available via ``from avaxagent import ...``):
    NetworkConfig, AvaxAgentError
    ERC8004Agent, AgentEndpoint
    WalletProvider, EVMWalletProvider
    SigningPolicy, PolicyViolation
    X402Signer
    load_env
    set_default_receipt_timeout, get_default_receipt_timeout, set_min_gas_price_wei

Tier 2 (import from subpackage):
    from avaxagent.utils import SlidingWindowLimiter, RateLimitExceeded
    from avaxagent.core import create_web3
    from avaxagent.erc20 import MinimalERC20Client, load_erc20_abi
    from avaxagent.storage import LocalStorageProvider, IPFSStorageProvider
    from avaxagent.networks import get_address, AVALANCHE_ADDRESSES
    from avaxagent.signing import check, EIP3009_TYPES, PERMIT_UNBOUNDED_TYPES
    from avaxagent.x402 import SessionBudgetTracker, X402SignerError

Not ported (absent on Avalanche): ERC-8183 commerce stack, MegaFuel
paymaster, TWAK wallet, U-token / Binance-peg assets, b402 permit2 routes.
"""

from __future__ import annotations

from ._version import __version__

# Configuration
from .config import NetworkConfig

# Transaction tuning (gas-price floor + receipt timeout) — public knobs that
# replace any downstream monkey-patching of SDK internals.
from .core.contract_mixin import (
    get_default_receipt_timeout,
    set_default_receipt_timeout,
    set_min_gas_price_wei,
)

# Opt-in .env loading (never called at import time — applications opt in)
from .core.env import load_env

# ERC-8004 Identity Registry
from .erc8004 import AgentEndpoint, ERC8004Agent

# Exceptions
from .exceptions import (
    AvaxAgentError,
    ERC8004PartialRegistrationError,
    TransactionPendingError,
)

# Signing policy
from .signing import PolicyViolation, SigningPolicy

# Wallets
from .wallets import EVMWalletProvider, WalletProvider

# x402 payment signer
from .x402 import X402Signer

__all__ = [
    # Core
    "__version__",
    "NetworkConfig",
    "AvaxAgentError",
    "TransactionPendingError",
    "ERC8004PartialRegistrationError",
    "load_env",
    # Transaction tuning
    "set_default_receipt_timeout",
    "get_default_receipt_timeout",
    "set_min_gas_price_wei",
    # ERC-8004
    "ERC8004Agent",
    "AgentEndpoint",
    # Wallets
    "WalletProvider",
    "EVMWalletProvider",
    # Signing policy
    "SigningPolicy",
    "PolicyViolation",
    # x402 payment signer
    "X402Signer",
]
