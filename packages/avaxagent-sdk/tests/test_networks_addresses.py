"""Tests for avaxagent.networks address registry (Avalanche C-Chain)."""

from __future__ import annotations

import pytest
from web3 import Web3

from avaxagent.config import NETWORKS
from avaxagent.networks import (
    AVALANCHE_ADDRESSES,
    AVALANCHE_FUJI_CHAIN_ID,
    AVALANCHE_MAINNET_CHAIN_ID,
    PAYMENT_TOKEN_EIP712_NAME,
    PAYMENT_TOKEN_EIP712_VERSION,
    get_address,
    known_payment_tokens,
)


def test_chain_ids():
    assert AVALANCHE_MAINNET_CHAIN_ID == 43114
    assert AVALANCHE_FUJI_CHAIN_ID == 43113


def test_get_address_returns_mainnet_usdc():
    d = get_address(AVALANCHE_MAINNET_CHAIN_ID)
    assert d.payment_token == "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E"


def test_get_address_returns_fuji_usdc():
    d = get_address(AVALANCHE_FUJI_CHAIN_ID)
    assert d.payment_token == "0x5425890298aed601595a70AB815c96711a31Bc65"


def test_identity_registry_matches_network_presets():
    assert (
        get_address(AVALANCHE_FUJI_CHAIN_ID).identity_registry
        == NETWORKS["avalanche-fuji"].registry_contract
        == "0x8004A818BFB912233c491871b3d84c89A494BD9e"
    )
    assert (
        get_address(AVALANCHE_MAINNET_CHAIN_ID).identity_registry
        == NETWORKS["avalanche-mainnet"].registry_contract
        == "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
    )


def test_multicall3_is_canonical_on_both_networks():
    for deploy in AVALANCHE_ADDRESSES.values():
        assert deploy.multicall3 == "0xcA11bde05977b3631167028862bE2a173976CA11"


def test_all_addresses_are_checksummed():
    for deploy in AVALANCHE_ADDRESSES.values():
        for value in vars(deploy).values():
            assert Web3.is_checksum_address(value), value


def test_known_payment_tokens_contains_both_networks():
    tokens = known_payment_tokens()
    assert (AVALANCHE_MAINNET_CHAIN_ID, get_address(AVALANCHE_MAINNET_CHAIN_ID).payment_token) in (
        tokens
    )
    assert (AVALANCHE_FUJI_CHAIN_ID, get_address(AVALANCHE_FUJI_CHAIN_ID).payment_token) in tokens
    assert len(tokens) == 2


def test_eip712_domain_constants_match_onchain_verification():
    # Circle FiatTokenV2: DOMAIN_SEPARATOR() recomputed from these values
    # matched on both 43114 and 43113.
    assert PAYMENT_TOKEN_EIP712_NAME == "USD Coin"
    assert PAYMENT_TOKEN_EIP712_VERSION == "2"


def test_bsc_chain_ids_are_not_registered():
    for chain_id in (56, 97):
        with pytest.raises(KeyError, match="no Avalanche deployment"):
            get_address(chain_id)


def test_get_address_unknown_chain_raises_keyerror():
    with pytest.raises(KeyError):
        get_address(1)
