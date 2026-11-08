"""Tests for resolve_network RPC override precedence (Avalanche presets).

Precedence: RPC_URL_<NETWORK> (per-network) > RPC_URL (global) > preset.
A NetworkConfig object passed directly is returned as-is (no env applied).
"""

from __future__ import annotations

import pytest

from avaxagent.config import DEFAULT_NETWORK, NETWORKS, NetworkConfig, resolve_network

FUJI = "avalanche-fuji"
MAINNET = "avalanche-mainnet"


@pytest.fixture(autouse=True)
def _clean_rpc_env(monkeypatch):
    for key in ("RPC_URL", "RPC_URL_AVALANCHE_FUJI", "RPC_URL_AVALANCHE_MAINNET"):
        monkeypatch.delenv(key, raising=False)


class TestPresets:
    def test_default_network_is_fuji(self):
        assert DEFAULT_NETWORK == FUJI
        assert resolve_network().chain_id == 43113

    def test_fuji_preset(self):
        nc = NETWORKS[FUJI]
        assert nc.chain_id == 43113
        assert nc.rpc_url == "https://api.avax-test.network/ext/bc/C/rpc"
        assert nc.registry_contract == "0x8004A818BFB912233c491871b3d84c89A494BD9e"

    def test_mainnet_preset(self):
        nc = NETWORKS[MAINNET]
        assert nc.chain_id == 43114
        assert nc.rpc_url == "https://api.avax.network/ext/bc/C/rpc"
        assert nc.registry_contract == "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"

    def test_no_bsc_presets_or_paymaster_fields(self):
        assert set(NETWORKS) == {FUJI, MAINNET}
        assert not hasattr(NETWORKS[FUJI], "paymaster_url")
        assert not hasattr(NETWORKS[FUJI], "commerce_contract")


class TestResolveNetworkPrecedence:
    def test_preset_default_when_no_env(self):
        nc = resolve_network(FUJI)
        assert nc.rpc_url == NETWORKS[FUJI].rpc_url

    def test_global_rpc_url_overrides_preset(self, monkeypatch):
        monkeypatch.setenv("RPC_URL", "https://global.example.com")
        nc = resolve_network(FUJI)
        assert nc.rpc_url == "https://global.example.com"

    def test_per_network_overrides_global(self, monkeypatch):
        monkeypatch.setenv("RPC_URL", "https://global.example.com")
        monkeypatch.setenv("RPC_URL_AVALANCHE_FUJI", "https://fuji.example.com")
        nc = resolve_network(FUJI)
        assert nc.rpc_url == "https://fuji.example.com"

    def test_per_network_is_network_scoped(self, monkeypatch):
        """A Fuji pin must not leak onto mainnet resolution."""
        monkeypatch.setenv("RPC_URL_AVALANCHE_FUJI", "https://fuji.example.com")
        assert resolve_network(FUJI).rpc_url == "https://fuji.example.com"
        assert resolve_network(MAINNET).rpc_url == NETWORKS[MAINNET].rpc_url

    def test_both_networks_pinned_simultaneously(self, monkeypatch):
        """One process can resolve BOTH networks to distinct pinned nodes."""
        monkeypatch.setenv("RPC_URL_AVALANCHE_FUJI", "https://f.example.com")
        monkeypatch.setenv("RPC_URL_AVALANCHE_MAINNET", "https://m.example.com")
        assert resolve_network(FUJI).rpc_url == "https://f.example.com"
        assert resolve_network(MAINNET).rpc_url == "https://m.example.com"

    def test_chain_metadata_preserved_under_override(self, monkeypatch):
        monkeypatch.setenv("RPC_URL_AVALANCHE_FUJI", "https://fuji.example.com")
        nc = resolve_network(FUJI)
        preset = NETWORKS[FUJI]
        assert nc.chain_id == preset.chain_id
        assert nc.registry_contract == preset.registry_contract
        assert nc.explorer_url == preset.explorer_url
        # The preset object itself is never mutated by an override.
        assert preset.rpc_url == "https://api.avax-test.network/ext/bc/C/rpc"

    def test_network_config_object_ignores_env(self, monkeypatch):
        monkeypatch.setenv("RPC_URL", "https://global.example.com")
        monkeypatch.setenv("RPC_URL_AVALANCHE_FUJI", "https://fuji.example.com")
        explicit = NetworkConfig(name=FUJI, chain_id=43113, rpc_url="https://mine.example.com")
        nc = resolve_network(explicit)
        assert nc is explicit
        assert nc.rpc_url == "https://mine.example.com"

    @pytest.mark.parametrize("name", ["bsc-testnet", "bsc-mainnet", "opbnb"])
    def test_unknown_network_raises(self, name):
        with pytest.raises(ValueError, match="Unknown network"):
            resolve_network(name)
