"""Contract tests for the Avalanche C-Chain payment-asset catalog.

Circle-native USDC / EURC only (EIP-3009, FiatTokenV2, 6 decimals). The
upstream BSC rows (U, USD1, Binance-peg USDC/USDT, permit2-exact routes) are
not ported because those tokens / routes do not exist on Avalanche.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest
from web3 import Web3

import avaxagent.networks as networks


def _api(name: str) -> Any:
    assert hasattr(networks, name), f"avaxagent.networks.{name} is not implemented"
    return getattr(networks, name)


def _snapshot() -> list[dict[str, object]]:
    list_assets = _api("list_assets")
    result: list[dict[str, object]] = []
    for chain_id in (networks.AVALANCHE_MAINNET_CHAIN_ID, networks.AVALANCHE_FUJI_CHAIN_ID):
        for asset in list_assets(chain_id):
            result.append(
                {
                    "chain_id": asset.chain_id,
                    "asset_id": asset.asset_id.value,
                    "symbol": asset.symbol,
                    "address": asset.address,
                    "decimals": asset.decimals,
                    "availability": asset.availability,
                    "x402_methods": asset.x402_methods,
                    "x402_kinds": tuple(
                        (kind.method, kind.name, kind.version) for kind in asset.x402_kinds
                    ),
                    "eip3009_domain": (
                        None
                        if asset.eip3009_domain is None
                        else (
                            asset.eip3009_domain.name,
                            asset.eip3009_domain.version,
                        )
                    ),
                    "is_default": asset.is_default,
                }
            )
    return result


ZERO = "0x0000000000000000000000000000000000000000"
MAINNET = networks.AVALANCHE_MAINNET_CHAIN_ID
FUJI = networks.AVALANCHE_FUJI_CHAIN_ID


def _usdc():
    return _api("get_asset")(MAINNET, _api("AssetId").USDC)


def test_asset_catalog_snapshot_matches_locked_avalanche_matrix():
    assert _snapshot() == [
        {
            "chain_id": 43114,
            "asset_id": "USDC",
            "symbol": "USDC",
            "address": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
            "decimals": 6,
            "availability": "active",
            "x402_methods": ("eip3009",),
            "x402_kinds": (("eip3009", "USD Coin", "2"),),
            "eip3009_domain": ("USD Coin", "2"),
            "is_default": True,
        },
        {
            "chain_id": 43114,
            "asset_id": "EURC",
            "symbol": "EURC",
            "address": "0xC891EB4cbdEFf6e073e859e987815Ed1505c2ACD",
            "decimals": 6,
            "availability": "active",
            "x402_methods": ("eip3009",),
            "x402_kinds": (("eip3009", "Euro Coin", "2"),),
            "eip3009_domain": ("Euro Coin", "2"),
            "is_default": False,
        },
        {
            "chain_id": 43113,
            "asset_id": "FUJI_USDC",
            "symbol": "USDC",
            "address": "0x5425890298aed601595a70AB815c96711a31Bc65",
            "decimals": 6,
            "availability": "active",
            "x402_methods": ("eip3009",),
            "x402_kinds": (("eip3009", "USD Coin", "2"),),
            "eip3009_domain": ("USD Coin", "2"),
            "is_default": True,
        },
        {
            "chain_id": 43113,
            "asset_id": "FUJI_EURC",
            "symbol": "EURC",
            "address": "0x5E44db7996c682E92a960b65AC713a54AD815c6B",
            "decimals": 6,
            "availability": "active",
            "x402_methods": ("eip3009",),
            "x402_kinds": (("eip3009", "EUR Coin", "2"),),
            "eip3009_domain": ("EUR Coin", "2"),
            "is_default": False,
        },
    ]


def test_exactly_one_default_asset_per_network():
    for chain_id in (MAINNET, FUJI):
        defaults = [a for a in _api("list_assets")(chain_id) if a.is_default]
        assert len(defaults) == 1
        assert defaults[0].symbol == "USDC"


def test_x402_view_matches_contract_facts():
    asset_id = _api("AssetId")
    for chain_id, aid in ((MAINNET, asset_id.USDC), (FUJI, asset_id.FUJI_USDC)):
        contract = _api("get_asset")(chain_id, aid)
        x402 = _api("get_x402_asset")(chain_id, aid)
        assert (x402.address, x402.decimals) == (contract.address, contract.decimals)
        assert _api("get_x402_asset_by_address")(chain_id, contract.address.lower()) == x402


def test_catalog_addresses_are_checksummed_and_reverse_lookup_is_case_insensitive():
    get_asset_by_address = _api("get_asset_by_address")
    for row in _snapshot():
        address = str(row["address"])
        assert Web3.is_checksum_address(address)
        resolved = get_asset_by_address(int(row["chain_id"]), address.lower())
        assert resolved.address == address
        assert resolved.asset_id.value == row["asset_id"]


def test_x402_kind_identity_snapshot_is_deeply_immutable():
    first = _usdc()

    assert isinstance(first.x402_kinds, tuple)
    with pytest.raises(FrozenInstanceError):
        first.x402_kinds[0].name = "Forged Token"  # type: ignore[misc]


def test_friendly_aliases_are_resolved_only_with_network_context():
    resolve_asset_alias = _api("resolve_asset_alias")
    assert resolve_asset_alias(MAINNET, "USDC").value == "USDC"
    assert resolve_asset_alias(MAINNET, "EURC").value == "EURC"
    assert resolve_asset_alias(FUJI, "USDC").value == "FUJI_USDC"
    assert resolve_asset_alias(FUJI, "EURC").value == "FUJI_EURC"
    for missing in ("USDT", "U", "USD1"):
        with pytest.raises(KeyError, match="unknown asset alias"):
            resolve_asset_alias(FUJI, missing)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"address": ZERO}, "active asset cannot use zero address"),
        ({"availability": "placeholder"}, "placeholder asset must use zero address"),
        (
            {"address": ZERO, "availability": "placeholder", "x402_kinds": ()},
            "placeholder asset cannot declare X402 methods",
        ),
        (
            {
                "address": ZERO,
                "availability": "placeholder",
                "x402_methods": (),
                "x402_kinds": (),
            },
            "placeholder asset cannot declare an EIP-3009 domain",
        ),
        (
            {
                "address": ZERO,
                "availability": "placeholder",
                "x402_methods": (),
                "x402_kinds": (),
                "eip3009_domain": None,
            },
            "placeholder asset cannot be the default asset",
        ),
    ],
)
def test_catalog_constructor_rejects_invalid_availability_invariants(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _api("AssetCatalog")((replace(_usdc(), **changes),))


def test_omitted_availability_is_active_in_catalog_results():
    asset_id = _api("AssetId")
    first = _usdc()
    legacy = _api("PaymentAsset")(
        chain_id=first.chain_id,
        asset_id=first.asset_id,
        symbol=first.symbol,
        address=first.address,
        decimals=first.decimals,
        x402_methods=first.x402_methods,
        eip3009_domain=first.eip3009_domain,
        is_default=first.is_default,
        x402_kinds=first.x402_kinds,
    )

    assert _api("AssetCatalog")((legacy,)).get(MAINNET, asset_id.USDC).availability == "active"


def test_canonical_parser_rejects_unknown_ids():
    parse_asset_id = _api("parse_asset_id")
    assert parse_asset_id("USDC").value == "USDC"
    assert parse_asset_id("FUJI_EURC").value == "FUJI_EURC"
    for bad in ("USDT", "TEST_U", "BINANCE_PEG_USDC", "usdc"):
        with pytest.raises(ValueError, match="canonical AssetId"):
            parse_asset_id(bad)


def test_catalog_fails_closed_for_unknown_chain_asset_alias_and_address():
    asset_id = _api("AssetId")
    get_asset = _api("get_asset")
    get_asset_by_address = _api("get_asset_by_address")
    list_assets = _api("list_assets")
    resolve_asset_alias = _api("resolve_asset_alias")

    for chain_id in (1, 56, 97):
        with pytest.raises(KeyError, match=f"chain_id={chain_id}"):
            list_assets(chain_id)
        with pytest.raises(KeyError, match=f"chain_id={chain_id}"):
            resolve_asset_alias(chain_id, "USDC")
    with pytest.raises(KeyError, match="not available"):
        get_asset(FUJI, asset_id.USDC)
    with pytest.raises(KeyError, match="not available"):
        get_asset(MAINNET, asset_id.FUJI_USDC)
    with pytest.raises(KeyError, match="not registered"):
        get_asset_by_address(MAINNET, "0x0000000000000000000000000000000000000001")
    # A mainnet address must not resolve on Fuji (and vice versa).
    with pytest.raises(KeyError, match="not registered"):
        get_asset_by_address(FUJI, "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E")


def test_catalog_constructor_rejects_duplicate_key_and_duplicate_address():
    asset_catalog = _api("AssetCatalog")
    asset_id = _api("AssetId")
    first = _usdc()

    with pytest.raises(ValueError, match="duplicate catalog key"):
        asset_catalog((first, first))

    duplicate_address = replace(first, asset_id=asset_id.EURC, is_default=False)
    with pytest.raises(ValueError, match="duplicate catalog address"):
        asset_catalog((first, duplicate_address))


def test_catalog_constructor_rejects_noncanonical_id_and_nonchecksum_address():
    asset_catalog = _api("AssetCatalog")
    first = _usdc()

    invalid_id = replace(first, asset_id="NOT_CANONICAL")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="canonical AssetId"):
        asset_catalog((invalid_id,))

    lowercase_address = replace(first, address=first.address.lower())
    with pytest.raises(ValueError, match="not checksummed"):
        asset_catalog((lowercase_address,))


def test_catalog_constructor_requires_exactly_one_kind_per_x402_method():
    asset_catalog = _api("AssetCatalog")
    first = _usdc()

    with pytest.raises(ValueError, match="missing X402 kind"):
        asset_catalog((replace(first, x402_kinds=()),))
    with pytest.raises(ValueError, match="duplicate X402 kind"):
        asset_catalog((replace(first, x402_kinds=first.x402_kinds * 2),))


def test_catalog_constructor_rejects_duplicate_methods_and_eip3009_mismatch():
    asset_catalog = _api("AssetCatalog")
    x402_kind = _api("X402Kind")
    first = _usdc()

    with pytest.raises(ValueError, match="duplicate X402 method"):
        asset_catalog((replace(first, x402_methods=("eip3009", "eip3009")),))
    with pytest.raises(ValueError, match="EIP-3009 kind must match"):
        asset_catalog((replace(first, x402_kinds=(x402_kind("eip3009", "Wrong Token", "2"),)),))


def test_asset_amount_conversion_uses_exact_non_negative_decimal_strings():
    asset_id = _api("AssetId")
    to_asset_atomic = _api("to_asset_atomic")

    assert to_asset_atomic(MAINNET, asset_id.USDC, "0") == 0
    assert to_asset_atomic(MAINNET, asset_id.USDC, "1.000001") == 1_000_001
    assert to_asset_atomic(FUJI, asset_id.FUJI_EURC, "12.5") == 12_500_000

    for invalid in ("", " 1", "1 ", "+1", "-1", ".1", "1.", "1e-6", "1E6"):
        with pytest.raises(ValueError, match="decimal amount"):
            to_asset_atomic(MAINNET, asset_id.USDC, invalid)
    with pytest.raises(ValueError, match="decimal places"):
        to_asset_atomic(FUJI, asset_id.FUJI_USDC, "1.0000001")
    with pytest.raises(TypeError, match="string"):
        to_asset_atomic(MAINNET, asset_id.USDC, 1.1)


def test_legacy_default_address_and_eip3009_allowlist_remain_compatible():
    asset_id = _api("AssetId")
    get_asset = _api("get_asset")

    assert networks.get_address(MAINNET).payment_token == get_asset(MAINNET, asset_id.USDC).address
    assert networks.get_address(FUJI).payment_token == get_asset(FUJI, asset_id.FUJI_USDC).address

    assert networks.known_payment_tokens() == frozenset(
        {
            (43114, "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E"),
            (43113, "0x5425890298aed601595a70AB815c96711a31Bc65"),
        }
    )
    # Every catalog asset is EIP-3009 on Avalanche, so the signing allowlist
    # covers USDC and EURC on both networks.
    assert networks.known_eip3009_payment_tokens() == frozenset(
        (row["chain_id"], row["address"]) for row in _snapshot()
    )
