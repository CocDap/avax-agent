"""Tests for the wallet provider factory and uniform introspection.

Covers ``create_wallet_provider`` selection plus the ``kind`` / ``key_location``
/ ``exists`` / ``describe`` introspection surface shared by every provider.
"""

from __future__ import annotations

import pytest

from avaxagent.wallets import (
    SUPPORTED_WALLET_KINDS,
    EVMWalletProvider,
    WalletProvider,
    create_wallet_provider,
)

PW = "test-secure-password-123"


class TestFactory:
    def test_creates_evm(self, tmp_path):
        wallet = create_wallet_provider("evm", password=PW, wallets_dir=tmp_path)
        assert isinstance(wallet, EVMWalletProvider)
        assert wallet.kind == "evm"

    def test_kind_is_case_insensitive(self, tmp_path):
        wallet = create_wallet_provider("EVM", password=PW, wallets_dir=tmp_path)
        assert isinstance(wallet, EVMWalletProvider)

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="Unknown wallet kind"):
            create_wallet_provider("ledger")

    def test_twak_is_not_available_on_avalanche(self):
        # TWAK (twak CLI) only supports BNB Smart Chain; skipped in this fork.
        with pytest.raises(ValueError, match="Unknown wallet kind"):
            create_wallet_provider("twak")

    def test_mpc_is_not_implemented(self):
        # mpc is a recognised kind, but the stub provider refuses to construct.
        with pytest.raises(NotImplementedError):
            create_wallet_provider("mpc")

    def test_supported_kinds_match_class_attrs(self):
        assert set(SUPPORTED_WALLET_KINDS) == {"evm", "mpc", "turnkey"}

    def test_turnkey_dispatches_to_provider(self):
        from avaxagent.wallets.turnkey import TurnkeyWalletProvider

        wallet = create_wallet_provider(
            "turnkey",
            organization_id="org-123",
            sign_with="0x" + "7a" * 20,
            api_public_key="02" + "ab" * 32,
            api_private_key="cd" * 32,
        )
        assert isinstance(wallet, TurnkeyWalletProvider)
        assert wallet.kind == "turnkey"


class TestIntrospection:
    def test_base_default_kind(self):
        assert WalletProvider.kind == "custom"

    def test_evm_describe_and_key_location(self, tmp_path):
        wallet = create_wallet_provider("evm", password=PW, wallets_dir=tmp_path)
        info = wallet.describe()
        assert info["kind"] == "evm"
        assert info["address"] == wallet.address
        assert info["address"] in info["key_location"]
        assert info["exists"] is True

    def test_evm_in_memory_does_not_exist(self):
        wallet = EVMWalletProvider(password=PW, private_key="0x" + "a" * 64, persist=False)
        assert wallet.exists() is False
        assert "in-memory" in wallet.key_location
