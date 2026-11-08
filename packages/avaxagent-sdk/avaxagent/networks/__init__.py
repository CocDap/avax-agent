"""Avalanche C-Chain deployment registry — addresses + EIP-712 metadata.

Public API::

    from avaxagent.networks import (
        AVALANCHE_ADDRESSES,
        DeployedAddresses,
        get_address,
        known_payment_tokens,
        AVALANCHE_MAINNET_CHAIN_ID,
        AVALANCHE_FUJI_CHAIN_ID,
        PAYMENT_TOKEN_EIP712_NAME,
        PAYMENT_TOKEN_EIP712_VERSION,
    )
"""

from __future__ import annotations

from .addresses import (
    AVALANCHE_ADDRESSES,
    AVALANCHE_FUJI_CHAIN_ID,
    AVALANCHE_MAINNET_CHAIN_ID,
    PAYMENT_TOKEN_EIP712_NAME,
    PAYMENT_TOKEN_EIP712_VERSION,
    DeployedAddresses,
    get_address,
    known_payment_tokens,
)
from .assets import (
    ASSET_CATALOG,
    AssetAlias,
    AssetCatalog,
    AssetId,
    EIP3009Domain,
    PaymentAsset,
    PaymentAssetAvailability,
    PaymentAssetUnavailableError,
    X402Kind,
    X402PaymentAsset,
    X402TransferMethod,
    get_asset,
    get_asset_by_address,
    get_asset_metadata,
    get_x402_asset,
    get_x402_asset_by_address,
    known_eip3009_payment_tokens,
    list_assets,
    parse_asset_id,
    resolve_asset_alias,
    to_asset_atomic,
)

__all__ = [
    "AVALANCHE_ADDRESSES",
    "ASSET_CATALOG",
    "AssetAlias",
    "AssetCatalog",
    "AssetId",
    "X402Kind",
    "X402PaymentAsset",
    "X402TransferMethod",
    "AVALANCHE_MAINNET_CHAIN_ID",
    "AVALANCHE_FUJI_CHAIN_ID",
    "DeployedAddresses",
    "EIP3009Domain",
    "PAYMENT_TOKEN_EIP712_NAME",
    "PAYMENT_TOKEN_EIP712_VERSION",
    "PaymentAsset",
    "PaymentAssetAvailability",
    "PaymentAssetUnavailableError",
    "get_asset",
    "get_asset_by_address",
    "get_x402_asset",
    "get_x402_asset_by_address",
    "get_asset_metadata",
    "known_eip3009_payment_tokens",
    "get_address",
    "known_payment_tokens",
    "list_assets",
    "parse_asset_id",
    "resolve_asset_alias",
    "to_asset_atomic",
]
