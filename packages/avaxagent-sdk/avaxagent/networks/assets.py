"""Canonical payment-asset catalog for supported Avalanche C-Chain networks.

Only assets whose EIP-3009 ``TransferWithAuthorization`` support and EIP-712
domain were verified on-chain are listed (Circle USDC and EURC on mainnet and
Fuji). Tether USDt on Avalanche has no EIP-3009 entrypoint and is therefore
not part of the x402 catalog.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType
from typing import Literal

from web3 import Web3

from .addresses import (
    AVALANCHE_FUJI_CHAIN_ID,
    AVALANCHE_MAINNET_CHAIN_ID,
    PAYMENT_TOKEN_EIP712_NAME,
    PAYMENT_TOKEN_EIP712_VERSION,
)

X402TransferMethod = Literal["eip3009"]
AssetAlias = Literal["USDC", "EURC"]
PaymentAssetAvailability = Literal["active", "placeholder"]


class AssetId(str, Enum):
    """Stable asset identities used by SDK APIs and persisted configuration."""

    USDC = "USDC"
    EURC = "EURC"
    FUJI_USDC = "FUJI_USDC"
    FUJI_EURC = "FUJI_EURC"


@dataclass(frozen=True)
class EIP3009Domain:
    """Verified EIP-712 domain metadata for an EIP-3009 token."""

    name: str
    version: str


@dataclass(frozen=True)
class X402Kind:
    """Exact X402 scheme identity for one transfer method."""

    method: X402TransferMethod
    name: str
    version: str


class PaymentAssetUnavailableError(KeyError):
    """Raised when metadata names an asset unavailable for payment queries."""

    def __init__(self, chain_id: int, asset_id: AssetId) -> None:
        super().__init__(f"AssetId {asset_id.value} is unavailable on chain_id={chain_id}")
        self.chain_id = chain_id
        self.asset_id = asset_id


@dataclass(frozen=True)
class PaymentAsset:
    """Immutable metadata for one canonical asset on one network."""

    chain_id: int
    asset_id: AssetId
    symbol: str
    address: str
    decimals: int
    x402_methods: tuple[X402TransferMethod, ...]
    eip3009_domain: EIP3009Domain | None
    is_default: bool
    # A trailing default preserves direct construction compatibility. An
    # AssetCatalog still rejects missing identities for declared methods.
    x402_kinds: tuple[X402Kind, ...] = ()
    # A trailing default preserves legacy object construction semantics.
    availability: PaymentAssetAvailability = "active"
    # x402 execution facts default to the catalog address and decimals.
    x402_address: str | None = None
    x402_decimals: int | None = None


X402PaymentAsset = PaymentAsset


class AssetCatalog:
    """Fail-closed lookup index keyed by network, canonical id, and address."""

    def __init__(self, assets: Sequence[PaymentAsset]) -> None:
        metadata_by_key: dict[tuple[int, AssetId], PaymentAsset] = {}
        metadata_by_address: dict[tuple[int, str], PaymentAsset] = {}
        active_by_key: dict[tuple[int, AssetId], PaymentAsset] = {}
        active_by_address: dict[tuple[int, str], PaymentAsset] = {}
        active_x402_by_key: dict[tuple[int, AssetId], X402PaymentAsset] = {}
        active_x402_by_address: dict[tuple[int, str], X402PaymentAsset] = {}
        active_by_chain: dict[int, list[PaymentAsset]] = {}

        for asset in assets:
            if not isinstance(asset.asset_id, AssetId):
                raise ValueError(f"asset_id must be a canonical AssetId: {asset.asset_id!r}")
            key = (asset.chain_id, asset.asset_id)
            if key in metadata_by_key:
                raise ValueError(
                    f"duplicate catalog key: chain_id={asset.chain_id}, "
                    f"asset_id={asset.asset_id.value}"
                )

            if not Web3.is_checksum_address(asset.address):
                raise ValueError(f"catalog address is not checksummed: {asset.address}")

            self._validate_availability(asset)
            self._validate_x402_metadata(asset)
            x402_address = asset.x402_address or asset.address
            x402_decimals = asset.decimals if asset.x402_decimals is None else asset.x402_decimals
            if not Web3.is_checksum_address(x402_address):
                raise ValueError(f"catalog X402 address is not checksummed: {x402_address}")
            if isinstance(x402_decimals, bool) or not isinstance(x402_decimals, int):
                raise ValueError("catalog X402 decimals must be a non-negative integer")
            if x402_decimals < 0:
                raise ValueError("catalog X402 decimals must be a non-negative integer")
            address_key = (asset.chain_id, asset.address.lower())
            if address_key in metadata_by_address:
                raise ValueError(
                    f"duplicate catalog address: chain_id={asset.chain_id}, "
                    f"address={asset.address}"
                )

            metadata_by_key[key] = asset
            metadata_by_address[address_key] = asset
            active_by_chain.setdefault(asset.chain_id, [])
            if asset.availability == "active":
                if x402_address.lower() == _ZERO_ADDRESS:
                    raise ValueError("active X402 asset cannot use zero address")
                x402_address_key = (asset.chain_id, x402_address.lower())
                if x402_address_key in active_x402_by_address:
                    raise ValueError(
                        f"duplicate catalog X402 address: chain_id={asset.chain_id}, "
                        f"address={x402_address}"
                    )
                x402_asset = replace(
                    asset,
                    address=x402_address,
                    decimals=x402_decimals,
                    x402_address=x402_address,
                    x402_decimals=x402_decimals,
                )
                active_by_key[key] = asset
                active_by_address[address_key] = asset
                active_x402_by_key[key] = x402_asset
                active_x402_by_address[x402_address_key] = x402_asset
                active_by_chain[asset.chain_id].append(asset)

        self._metadata_by_key: Mapping[tuple[int, AssetId], PaymentAsset] = MappingProxyType(
            metadata_by_key
        )
        self._metadata_by_address: Mapping[tuple[int, str], PaymentAsset] = MappingProxyType(
            metadata_by_address
        )
        self._active_by_key: Mapping[tuple[int, AssetId], PaymentAsset] = MappingProxyType(
            active_by_key
        )
        self._active_by_address: Mapping[tuple[int, str], PaymentAsset] = MappingProxyType(
            active_by_address
        )
        self._active_x402_by_key: Mapping[tuple[int, AssetId], X402PaymentAsset] = (
            MappingProxyType(active_x402_by_key)
        )
        self._active_x402_by_address: Mapping[tuple[int, str], X402PaymentAsset] = (
            MappingProxyType(active_x402_by_address)
        )
        self._active_by_chain: Mapping[int, tuple[PaymentAsset, ...]] = MappingProxyType(
            {chain_id: tuple(chain_assets) for chain_id, chain_assets in active_by_chain.items()}
        )

    @staticmethod
    def _validate_availability(asset: PaymentAsset) -> None:
        if asset.availability not in ("active", "placeholder"):
            raise ValueError("unknown payment asset availability")
        if asset.availability == "active":
            if asset.address.lower() == _ZERO_ADDRESS:
                raise ValueError("active asset cannot use zero address")
            return
        if asset.address.lower() != _ZERO_ADDRESS:
            raise ValueError("placeholder asset must use zero address")
        if asset.x402_methods or asset.x402_kinds:
            raise ValueError("placeholder asset cannot declare X402 methods")
        if asset.eip3009_domain is not None:
            raise ValueError("placeholder asset cannot declare an EIP-3009 domain")
        if asset.is_default:
            raise ValueError("placeholder asset cannot be the default asset")

    @staticmethod
    def _validate_x402_metadata(asset: PaymentAsset) -> None:
        supported_methods = frozenset(("eip3009",))
        methods = asset.x402_methods
        if not isinstance(methods, tuple):
            raise ValueError("x402_methods must be an immutable tuple")
        if len(set(methods)) != len(methods):
            raise ValueError("duplicate X402 method in asset catalog")
        if any(method not in supported_methods for method in methods):
            raise ValueError("unknown X402 method in asset catalog")

        kinds = asset.x402_kinds
        if not isinstance(kinds, tuple) or any(not isinstance(kind, X402Kind) for kind in kinds):
            raise ValueError("x402_kinds must be an immutable tuple of X402Kind")
        kind_methods = tuple(kind.method for kind in kinds)
        if len(set(kind_methods)) != len(kind_methods):
            raise ValueError("duplicate X402 kind identity in asset catalog")
        if any(kind.method not in supported_methods for kind in kinds):
            raise ValueError("unknown X402 kind method in asset catalog")
        if any(not kind.name or not kind.version for kind in kinds):
            raise ValueError("X402 kind name and version must be non-empty")

        missing = set(methods).difference(kind_methods)
        if missing:
            raise ValueError(f"missing X402 kind identity for method={sorted(missing)[0]}")
        extra = set(kind_methods).difference(methods)
        if extra:
            raise ValueError(f"extra X402 kind identity for method={sorted(extra)[0]}")

        eip3009_kind = next((kind for kind in kinds if kind.method == "eip3009"), None)
        if eip3009_kind is None:
            if asset.eip3009_domain is not None:
                raise ValueError("EIP-3009 domain requires an eip3009 X402 method")
        elif asset.eip3009_domain is None or (
            eip3009_kind.name,
            eip3009_kind.version,
        ) != (
            asset.eip3009_domain.name,
            asset.eip3009_domain.version,
        ):
            raise ValueError("EIP-3009 kind must match eip3009_domain exactly")

    def _require_chain(self, chain_id: int) -> None:
        if chain_id not in self._active_by_chain:
            raise KeyError(f"no asset catalog registered for chain_id={chain_id}")

    def get(self, chain_id: int, asset_id: AssetId | str) -> PaymentAsset:
        asset = self.get_metadata(chain_id, asset_id)
        if asset.availability == "placeholder":
            raise PaymentAssetUnavailableError(chain_id, asset.asset_id)
        return self._active_by_key[(chain_id, asset.asset_id)]

    def get_metadata(self, chain_id: int, asset_id: AssetId | str) -> PaymentAsset:
        self._require_chain(chain_id)
        canonical = parse_asset_id(asset_id)
        try:
            return self._metadata_by_key[(chain_id, canonical)]
        except KeyError as exc:
            raise KeyError(
                f"AssetId {canonical.value} is not available on chain_id={chain_id}"
            ) from exc

    def by_address(self, chain_id: int, address: str) -> PaymentAsset:
        self._require_chain(chain_id)
        try:
            address_key = Web3.to_checksum_address(address).lower()
        except (TypeError, ValueError) as exc:
            raise KeyError(
                f"asset address {address!r} is not registered on chain_id={chain_id}"
            ) from exc
        try:
            return self._active_by_address[(chain_id, address_key)]
        except KeyError as exc:
            raise KeyError(
                f"asset address {address!r} is not registered on chain_id={chain_id}"
            ) from exc

    def get_x402(self, chain_id: int, asset_id: AssetId | str) -> X402PaymentAsset:
        asset = self.get(chain_id, asset_id)
        return self._active_x402_by_key[(chain_id, asset.asset_id)]

    def by_x402_address(self, chain_id: int, address: str) -> X402PaymentAsset:
        self._require_chain(chain_id)
        try:
            address_key = Web3.to_checksum_address(address).lower()
        except (TypeError, ValueError) as exc:
            raise KeyError(
                f"X402 asset address {address!r} is not registered on chain_id={chain_id}"
            ) from exc
        try:
            return self._active_x402_by_address[(chain_id, address_key)]
        except KeyError as exc:
            raise KeyError(
                f"X402 asset address {address!r} is not registered on chain_id={chain_id}"
            ) from exc

    def list(self, chain_id: int) -> tuple[PaymentAsset, ...]:
        self._require_chain(chain_id)
        return self._active_by_chain[chain_id]


_USDC_DOMAIN = EIP3009Domain(
    name=PAYMENT_TOKEN_EIP712_NAME,
    version=PAYMENT_TOKEN_EIP712_VERSION,
)

_ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Every entry verified on-chain: ``DOMAIN_SEPARATOR()`` equals the EIP-712
# domain recomputed from (name, version, chainId, verifyingContract), and
# ``TRANSFER_WITH_AUTHORIZATION_TYPEHASH()`` is present.
ASSET_CATALOG = AssetCatalog(
    (
        PaymentAsset(
            chain_id=AVALANCHE_MAINNET_CHAIN_ID,
            asset_id=AssetId.USDC,
            symbol="USDC",
            address="0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
            decimals=6,
            x402_methods=("eip3009",),
            eip3009_domain=_USDC_DOMAIN,
            is_default=True,
            x402_kinds=(X402Kind("eip3009", "USD Coin", "2"),),
        ),
        PaymentAsset(
            chain_id=AVALANCHE_MAINNET_CHAIN_ID,
            asset_id=AssetId.EURC,
            symbol="EURC",
            address="0xC891EB4cbdEFf6e073e859e987815Ed1505c2ACD",
            decimals=6,
            x402_methods=("eip3009",),
            eip3009_domain=EIP3009Domain("Euro Coin", "2"),
            is_default=False,
            x402_kinds=(X402Kind("eip3009", "Euro Coin", "2"),),
        ),
        PaymentAsset(
            chain_id=AVALANCHE_FUJI_CHAIN_ID,
            asset_id=AssetId.FUJI_USDC,
            symbol="USDC",
            address="0x5425890298aed601595a70AB815c96711a31Bc65",
            decimals=6,
            x402_methods=("eip3009",),
            eip3009_domain=_USDC_DOMAIN,
            is_default=True,
            x402_kinds=(X402Kind("eip3009", "USD Coin", "2"),),
        ),
        PaymentAsset(
            chain_id=AVALANCHE_FUJI_CHAIN_ID,
            asset_id=AssetId.FUJI_EURC,
            symbol="EURC",
            address="0x5E44db7996c682E92a960b65AC713a54AD815c6B",
            decimals=6,
            x402_methods=("eip3009",),
            eip3009_domain=EIP3009Domain("EUR Coin", "2"),
            is_default=False,
            x402_kinds=(X402Kind("eip3009", "EUR Coin", "2"),),
        ),
    )
)

_ALIASES: Mapping[int, Mapping[str, AssetId]] = MappingProxyType(
    {
        AVALANCHE_MAINNET_CHAIN_ID: MappingProxyType(
            {
                "USDC": AssetId.USDC,
                "EURC": AssetId.EURC,
            }
        ),
        AVALANCHE_FUJI_CHAIN_ID: MappingProxyType(
            {
                "USDC": AssetId.FUJI_USDC,
                "EURC": AssetId.FUJI_EURC,
            }
        ),
    }
)

_DECIMAL_AMOUNT = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")


def parse_asset_id(value: AssetId | str) -> AssetId:
    """Parse a canonical ID without applying network-specific symbol aliases."""
    if isinstance(value, AssetId):
        return value
    try:
        return AssetId(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"unknown canonical AssetId: {value!r}") from exc


def resolve_asset_alias(chain_id: int, alias: AssetAlias | str) -> AssetId:
    """Resolve a UI alias after the network context is known."""
    if chain_id not in _ALIASES:
        raise KeyError(f"no asset catalog registered for chain_id={chain_id}")
    try:
        return _ALIASES[chain_id][alias]
    except KeyError as exc:
        raise KeyError(f"unknown asset alias {alias!r} for chain_id={chain_id}") from exc


def get_asset(chain_id: int, asset_id: AssetId | str) -> PaymentAsset:
    """Return an active asset for a strict ``(chain_id, canonical AssetId)`` key."""
    return ASSET_CATALOG.get(chain_id, asset_id)


def get_asset_metadata(chain_id: int, asset_id: AssetId | str) -> PaymentAsset:
    """Return validated metadata, including diagnostic placeholder entries."""
    return ASSET_CATALOG.get_metadata(chain_id, asset_id)


def get_asset_by_address(chain_id: int, address: str) -> PaymentAsset:
    """Reverse-resolve an active token address; input casing is ignored."""
    return ASSET_CATALOG.by_address(chain_id, address)


def get_x402_asset(chain_id: int, asset_id: AssetId | str) -> X402PaymentAsset:
    """Return active metadata projected to the X402 execution contract."""
    return ASSET_CATALOG.get_x402(chain_id, asset_id)


def get_x402_asset_by_address(chain_id: int, address: str) -> X402PaymentAsset:
    """Reverse-resolve an active X402 token address; input casing is ignored."""
    return ASSET_CATALOG.by_x402_address(chain_id, address)


def list_assets(chain_id: int) -> tuple[PaymentAsset, ...]:
    """Return the immutable active catalog snapshot for one known network."""
    return ASSET_CATALOG.list(chain_id)


def known_eip3009_payment_tokens() -> frozenset[tuple[int, str]]:
    """Active catalog EIP-3009 ``(chain_id, checksum_address)`` domains."""
    return frozenset(
        (chain_id, get_x402_asset(chain_id, asset.asset_id).address)
        for chain_id in (AVALANCHE_MAINNET_CHAIN_ID, AVALANCHE_FUJI_CHAIN_ID)
        for asset in list_assets(chain_id)
        if asset.eip3009_domain is not None and "eip3009" in asset.x402_methods
    )


def to_asset_atomic(chain_id: int, asset_id: AssetId | str, amount: str) -> int:
    """Convert a plain non-negative decimal string to exact atomic units."""
    if not isinstance(amount, str):
        raise TypeError("asset amount must be a decimal string")
    if _DECIMAL_AMOUNT.fullmatch(amount) is None:
        raise ValueError(f"invalid decimal amount: {amount!r}")

    asset = get_asset(chain_id, asset_id)
    whole, separator, fraction = amount.partition(".")
    if separator and len(fraction) > asset.decimals:
        raise ValueError(f"asset amount exceeds {asset.decimals} decimal places: {amount!r}")
    return int(whole) * 10**asset.decimals + int(fraction.ljust(asset.decimals, "0") or "0")
