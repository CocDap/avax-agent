"""RPC error classification: transport/RPC hiccups are transient, reverts and
content errors are permanent (upstream audit M10). The ERC-8183 funded-job
watcher cases are not ported — ERC-8183 is not deployed on Avalanche."""

import asyncio
import concurrent.futures

import httpx
import pytest
import requests
from eth_keys.exceptions import BadSignature
from web3.exceptions import (
    BadFunctionCallOutput,
    BadResponseFormat,
    ContractLogicError,
    ProviderConnectionError,
    RequestTimedOut,
    TimeExhausted,
    TooManyRequests,
    Web3RPCError,
)

from avaxagent.core.rpc_errors import is_revert_error, is_transient_rpc_error
from avaxagent.exceptions import NetworkError, RpcRangeLimitError

_REQUEST = httpx.Request("POST", "https://api.avax.network/ext/bc/C/rpc")


def _wrapped(cause: BaseException) -> BaseException:
    try:
        raise cause
    except BaseException as exc:
        try:
            raise RuntimeError("get_job_funded_block failed") from exc
        except RuntimeError as wrapped:
            return wrapped


TRANSIENT = {
    "Web3RPCError header not found": lambda: Web3RPCError("header not found"),
    "Web3RPCError missing trie node": lambda: Web3RPCError(
        "missing trie node",
        rpc_response={"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "x"}},
    ),
    "RequestTimedOut": lambda: RequestTimedOut("request timed out"),
    "TooManyRequests": lambda: TooManyRequests("too many"),
    "ProviderConnectionError": lambda: ProviderConnectionError("cannot connect"),
    "TimeExhausted": lambda: TimeExhausted("exhausted"),
    "BadResponseFormat": lambda: BadResponseFormat("not JSON"),
    "httpx.ConnectError": lambda: httpx.ConnectError("refused", request=_REQUEST),
    "httpx.ReadTimeout": lambda: httpx.ReadTimeout("slow", request=_REQUEST),
    "httpx 502": lambda: httpx.HTTPStatusError(
        "502", request=_REQUEST, response=httpx.Response(502, request=_REQUEST)
    ),
    "requests.ConnectionError": lambda: requests.ConnectionError("refused"),
    "requests.HTTPError": lambda: requests.HTTPError("502 Server Error"),
    "ConnectionResetError": lambda: ConnectionResetError(104, "Connection reset by peer"),
    "asyncio.TimeoutError": lambda: asyncio.TimeoutError(),
    "futures.TimeoutError": lambda: concurrent.futures.TimeoutError(),
    "NetworkError": lambda: NetworkError("no route"),
    "RpcRangeLimitError": lambda: RpcRangeLimitError("-32005 limit exceeded"),
    "web3 6 payload": lambda: ValueError({"code": -32005, "message": "limit exceeded"}),
    "wrapped Web3RPCError": lambda: _wrapped(Web3RPCError("header not found")),
}

PERMANENT = {
    "ContractLogicError": lambda: ContractLogicError("execution reverted"),
    "revert raised from an RPC error": lambda: _wrapped_revert(),
    "BadFunctionCallOutput": lambda: BadFunctionCallOutput("empty"),
    "BadSignature": lambda: BadSignature(),
    "AttributeError": lambda: AttributeError("'str' object has no attribute 'get'"),
    "TypeError": lambda: TypeError("unsupported operand"),
    "ValueError": lambda: ValueError("signature has the wrong length"),
    "KeyError": lambda: KeyError("terms"),
}


def _wrapped_revert() -> BaseException:
    try:
        raise Web3RPCError("execution reverted")
    except Web3RPCError as exc:
        try:
            raise ContractLogicError("execution reverted") from exc
        except ContractLogicError as revert:
            return revert


@pytest.mark.parametrize("label", list(TRANSIENT))
def test_transport_and_rpc_errors_are_transient(label):
    assert is_transient_rpc_error(TRANSIENT[label]())


@pytest.mark.parametrize("label", list(PERMANENT))
def test_reverts_and_content_errors_are_not_transient(label):
    assert not is_transient_rpc_error(PERMANENT[label]())


@pytest.mark.parametrize(
    "label", ["ContractLogicError", "revert raised from an RPC error", "BadFunctionCallOutput"]
)
def test_reverts_are_revert_errors(label):
    assert is_revert_error(PERMANENT[label]())


@pytest.mark.parametrize("label", ["AttributeError", "BadSignature", "ValueError"])
def test_other_errors_are_not_revert_errors(label):
    assert not is_revert_error(PERMANENT[label]())
    assert not is_revert_error(Web3RPCError("header not found"))
