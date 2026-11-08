"""LocalExecutor self-pay path (Avalanche: no paymaster, gas paid in AVAX).

Ported from the upstream ``test_local_executor_paymaster.py``; the MegaFuel
sponsorship cases are dropped because the paymaster does not exist on
Avalanche. ``_make_pieces`` is shared with ``test_broadcast_idempotence``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from avaxagent.core.nonce_manager import NonceManager
from avaxagent.networks import AVALANCHE_FUJI_CHAIN_ID
from avaxagent.wallets.local_executor import LocalExecutor


def _ok_receipt(tx_hash: bytes) -> dict:
    return {"status": 1, "blockNumber": 1, "gasUsed": 50_000, "transactionHash": tx_hash}


def _make_pieces(*, gas_limit: int = 100_000, data: str = "0x"):
    """A function mock + web3 mock + wallet mock wired for one write."""
    web3 = MagicMock()
    web3.eth.gas_price = 25_000_000_000
    web3.eth.chain_id = AVALANCHE_FUJI_CHAIN_ID
    web3.eth.get_transaction_count.return_value = 1
    web3.eth.call.return_value = b""  # pre-flight passes
    web3.eth.send_raw_transaction.return_value = b"\xab" * 32
    web3.eth.wait_for_transaction_receipt.return_value = _ok_receipt(b"\xab" * 32)

    fn = MagicMock()
    fn.estimate_gas.return_value = gas_limit
    fn.build_transaction.return_value = {
        "from": "0xDeadBeef",
        "to": "0x1234",
        "data": data,
        "value": 0,
        "gas": gas_limit,
        "gasPrice": 25_000_000_000,
        "nonce": 1,
        "chainId": AVALANCHE_FUJI_CHAIN_ID,
    }

    wallet = MagicMock()
    wallet.address = "0x" + "11" * 20
    signed = MagicMock()
    signed.__getitem__ = lambda _s, k: b"\x00" * 32 if k == "rawTransaction" else None
    wallet.sign_transaction.return_value = signed
    return fn, web3, wallet


@pytest.fixture(autouse=True)
def _clean_nonces():
    NonceManager._clear_all()
    yield
    NonceManager._clear_all()


def test_self_pays_via_web3():
    fn, web3, wallet = _make_pieces()
    ex = LocalExecutor(web3=web3, wallet_provider=wallet)
    result = ex._execute_function(fn, description="register")
    web3.eth.send_raw_transaction.assert_called_once()
    assert result["transactionHash"] == "0x" + "ab" * 32


def test_gas_price_tracks_eth_gas_price_with_headroom():
    """Avalanche floor is 1 wei, so the price is eth_gasPrice * 1.2."""
    fn, web3, wallet = _make_pieces()
    web3.eth.gas_price = 1_000
    ex = LocalExecutor(web3=web3, wallet_provider=wallet)
    ex._execute_function(fn, description="register")
    built = fn.build_transaction.call_args.args[0]
    assert built["gasPrice"] == 1_200
    assert built["chainId"] == AVALANCHE_FUJI_CHAIN_ID
    assert built["gas"] == 120_000  # 20% buffer on the estimate


def test_executor_has_no_paymaster_parameter():
    with pytest.raises(TypeError):
        LocalExecutor(web3=MagicMock(), wallet_provider=MagicMock(), paymaster=MagicMock())


def test_preflight_revert_propagates_and_never_broadcasts():
    fn, web3, wallet = _make_pieces()
    web3.eth.call.side_effect = RuntimeError("execution reverted: NotOwner()")

    ex = LocalExecutor(web3=web3, wallet_provider=wallet)
    with pytest.raises(RuntimeError, match="would revert"):
        ex._execute_function(fn, description="set_metadata")

    web3.eth.send_raw_transaction.assert_not_called()
