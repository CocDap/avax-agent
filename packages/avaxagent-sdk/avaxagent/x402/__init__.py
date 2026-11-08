"""x402 payment layer — signing primitives and the delegated-payer seam.

On Avalanche the x402 ``exact`` scheme settles via EIP-3009
``transferWithAuthorization`` on Circle USDC / EURC.

Public API::

    from avaxagent.x402 import (
        X402Signer,
        X402Payer,
        X402Quote,
        X402PaymentOption,
        X402PaymentResult,
        SessionBudgetTracker,
        X402SignerError,
        X402RecipientMismatchError,
        X402AmountExceededError,
        X402BudgetExhaustedError,
        X402PolicyError,
        X402NoPayableRouteError,
    )
"""

from __future__ import annotations

from .assets import (
    DelegatedX402ExactPayerCapability,
    ExpectedEIP3009Route,
    ExpectedX402Asset,
    X402WalletRoute,
    require_expected_eip3009_route,
    require_x402_wallet_route,
    resolve_expected_eip3009_route,
    resolve_x402_asset,
)
from .budget import SessionBudgetTracker
from .errors import (
    UnsupportedWalletRouteError,
    X402AmountExceededError,
    X402BudgetExhaustedError,
    X402NoPayableRouteError,
    X402PolicyError,
    X402RecipientMismatchError,
    X402SignerError,
)
from .payer import (
    X402Payer,
    X402PaymentOption,
    X402PaymentResult,
    X402Quote,
    expected_asset_from_payment_option,
)
from .signer import X402Signer

__all__ = [
    "X402Signer",
    "X402Payer",
    "X402Quote",
    "X402PaymentOption",
    "X402PaymentResult",
    "SessionBudgetTracker",
    "X402SignerError",
    "X402RecipientMismatchError",
    "X402AmountExceededError",
    "X402BudgetExhaustedError",
    "X402PolicyError",
    "X402NoPayableRouteError",
    "ExpectedX402Asset",
    "ExpectedEIP3009Route",
    "X402WalletRoute",
    "DelegatedX402ExactPayerCapability",
    "UnsupportedWalletRouteError",
    "resolve_x402_asset",
    "resolve_expected_eip3009_route",
    "require_x402_wallet_route",
    "require_expected_eip3009_route",
    "expected_asset_from_payment_option",
]
