"""Per-provider capability conformance tests (design doc §3.3 / §3.4).

The capability model's anti-drift rules, asserted for every constructible
provider:

- the declared capability set matches the design table EXACTLY;
- every declared ``sign.*`` capability is actually usable (the call succeeds);
- every undeclared ``sign.*`` capability raises ``UnsupportedWalletOperation``
  (a ``NotImplementedError`` subclass, for back-compat);
- ``supports()`` is a pure membership test over ``capabilities()``; unknown
  values are False (absence = unsupported, the EIP-5792 omission rule);
- ``describe()["capabilities"]`` is the sorted capability list;
- ``sign.*`` auto-derivation from method overrides, including the
  override-is-capability counterexample;
- ``make_executor()`` gates on ``sign.transaction`` at construction time.

The upstream TWAK provider cases are not ported (twak supports BNB Smart Chain
only).
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from eth_account import Account
from eth_account.messages import encode_defunct

from avaxagent.signing import SigningPolicy
from avaxagent.wallets import (
    EVMWalletProvider,
    ExecutionContext,
    TurnkeyWalletProvider,
    UnsupportedWalletOperation,
    WalletProvider,
)
from avaxagent.wallets.capabilities import (
    BROADCAST_SELF,
    CALLS_ARBITRARY,
    SIGN_MESSAGE,
    SIGN_TRANSACTION,
    SIGN_TYPED_DATA,
)
from avaxagent.wallets.local_executor import LocalExecutor

from .turnkey_fake import FakeTurnkeyClient

PW = "test-secure-password-123"
_TEST_KEY = "0x" + "ab" * 32

SIGN_CAPABILITIES = frozenset({SIGN_MESSAGE, SIGN_TRANSACTION, SIGN_TYPED_DATA})

# The design-table capability sets (§3.4) — asserted EXACTLY, so an
# accidentally gained or lost capability fails this suite.
EXPECTED_CAPABILITIES: dict[str, frozenset[str]] = {
    "evm": frozenset({SIGN_MESSAGE, SIGN_TRANSACTION, SIGN_TYPED_DATA, CALLS_ARBITRARY}),
    "turnkey": frozenset({SIGN_MESSAGE, SIGN_TRANSACTION, SIGN_TYPED_DATA, CALLS_ARBITRARY}),
}


def _make_provider(kind: str) -> WalletProvider:
    if kind == "evm":
        # In-memory mode: private_key + persist=False, nothing touches disk.
        # Permissive policy so the declared-usable sign_typed_data probe is
        # not entangled with SigningPolicy (covered in test_signing_policy.py).
        return EVMWalletProvider(
            password=PW,
            private_key=_TEST_KEY,
            persist=False,
            signing_policy=SigningPolicy.permissive(),
        )
    if kind == "turnkey":
        # Remote signer with the fake in-process enclave (signs with the
        # shared test key, never dials the network). Permissive policy for
        # the same reason as evm above.
        fake = FakeTurnkeyClient(_TEST_KEY)
        return TurnkeyWalletProvider(
            organization_id="org-conformance",
            sign_with=fake.address,
            api_public_key="02" + "ab" * 32,
            api_private_key="cd" * 32,
            signing_policy=SigningPolicy.permissive(),
            client=fake,
        )
    raise ValueError(f"unknown kind {kind!r}")


@pytest.fixture(params=sorted(EXPECTED_CAPABILITIES))
def kind(request) -> str:
    return request.param


@pytest.fixture
def provider(kind) -> WalletProvider:
    return _make_provider(kind)


# ── canonical invocations, one per sign.* capability ──

_TX = {
    "to": "0x" + "22" * 20,
    "value": 0,
    "gas": 21000,
    "gasPrice": 10**9,
    "nonce": 0,
    "chainId": 43113,
}
_DOMAIN = {
    "name": "Conformance",
    "version": "1",
    "chainId": 43113,
    "verifyingContract": "0x" + "33" * 20,
}
_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "Probe": [{"name": "value", "type": "uint256"}],
}
_MESSAGE = {"value": 1}

_SIGN_INVOCATIONS = {
    SIGN_MESSAGE: lambda p: p.sign_message("conformance probe"),
    SIGN_TRANSACTION: lambda p: p.sign_transaction(dict(_TX)),
    SIGN_TYPED_DATA: lambda p: p.sign_typed_data(_DOMAIN, _TYPES, _MESSAGE),
}


# ── conformance: declared set, declared-usable, undeclared-raises ──


def test_capability_set_matches_design_table_exactly(kind, provider):
    assert provider.capabilities() == EXPECTED_CAPABILITIES[kind]


def test_declared_sign_capabilities_are_usable(kind, provider):
    # Rule: a declared capability must be usable — calling the matching
    # method produces a signature dict, never UnsupportedWalletOperation.
    for capability in sorted(provider.capabilities() & SIGN_CAPABILITIES):
        result = _SIGN_INVOCATIONS[capability](provider)
        assert isinstance(result, dict)
        assert result.get("signature") is not None or result.get("rawTransaction") is not None


def test_undeclared_sign_capabilities_raise(kind, provider):
    # Rule: an undeclared capability must raise UnsupportedWalletOperation
    # naming the capability.
    for capability in sorted(SIGN_CAPABILITIES - provider.capabilities()):
        with pytest.raises(UnsupportedWalletOperation, match=capability) as exc:
            _SIGN_INVOCATIONS[capability](provider)
        # Back-compat: existing `except NotImplementedError` callers keep working.
        assert isinstance(exc.value, NotImplementedError)


def test_supports_agrees_with_capabilities(provider):
    declared = provider.capabilities()
    for capability in sorted(EXPECTED_CAPABILITIES["evm"] | {BROADCAST_SELF}):
        assert provider.supports(capability) == (capability in declared)
    # Unknown value: consumers ignore what they don't recognise, and absence
    # means unsupported — supports() must return False, never raise.
    assert provider.supports("vendor.unknown_capability") is False


def test_describe_capabilities_is_sorted_list(provider):
    assert provider.describe()["capabilities"] == sorted(provider.capabilities())


# ── sign.* auto-derivation (throwaway subclasses) ──


class _AddressOnly(WalletProvider):
    """Minimal constructible provider: only the abstract `address`."""

    @property
    def address(self) -> str:
        return "0x" + "11" * 20


def test_address_only_subclass_has_no_capabilities():
    assert _AddressOnly().capabilities() == frozenset()


def test_sign_message_override_derives_exactly_that_capability():
    class MessageOnly(_AddressOnly):
        def sign_message(self, message):
            return {"signature": "0x" + "00" * 65}

    assert MessageOnly().capabilities() == frozenset({SIGN_MESSAGE})


def test_override_to_raise_still_claims_the_capability():
    # The override-is-capability counterexample: derivation only sees that the
    # method was overridden, not what it does — so overriding sign_typed_data
    # just to raise FALSELY claims sign.typed_data. This is exactly WHY the
    # discipline says "don't override-to-raise": the base default already
    # raises a descriptive UnsupportedWalletOperation, and not overriding is
    # the only way to keep the capability out of capabilities().
    class OverridesToRaise(_AddressOnly):
        def sign_typed_data(self, domain, types, message):
            raise UnsupportedWalletOperation("sign.typed_data")

    assert SIGN_TYPED_DATA in OverridesToRaise().capabilities()


def test_extra_capabilities_union_with_derived():
    class Extra(_AddressOnly):
        _extra_capabilities = frozenset({BROADCAST_SELF, "acme.batch_sign"})

        def sign_message(self, message):
            return {"signature": "0x" + "00" * 65}

    wallet = Extra()
    assert wallet.capabilities() == frozenset({SIGN_MESSAGE, BROADCAST_SELF, "acme.batch_sign"})
    # Open set: the vendor-namespaced value is first-class in supports()...
    assert wallet.supports("acme.batch_sign") is True
    # ...and any string not declared is simply unsupported.
    assert wallet.supports("acme.other") is False


# ── make_executor construction gate ──


def test_signless_subclass_make_executor_raises_at_construction():
    # The default executor needs sign.transaction; the error must surface at
    # make_executor() — before any intent runs — not on first execution.
    with pytest.raises(UnsupportedWalletOperation, match=SIGN_TRANSACTION):
        _AddressOnly().make_executor(ExecutionContext(web3=Mock()))


@pytest.mark.parametrize("kind", ["evm", "turnkey"])
def test_generic_transaction_wallets_keep_using_local_executor(kind):
    executor = _make_provider(kind).make_executor(ExecutionContext(web3=Mock()))
    assert isinstance(executor, LocalExecutor)


# ── cross-kind signature compatibility (S-11 regression net) ──

#: A message that *looks* like hex (e.g. a hash an agent signs over).
HEX_SHAPED_MESSAGE = "0x" + "ab" * 32


def test_sign_message_text_semantics_for_hex_shaped_message(kind, provider):
    """Every kind must sign a 0x-shaped message under EIP-191 TEXT semantics,
    so a verifier's ecrecover(text) works regardless of which wallet produced
    the signature. Guards any SDK-side encoding trick (upstream S-11)."""
    if SIGN_MESSAGE not in provider.capabilities():
        pytest.skip(f"{kind} does not declare sign.message")
    result = provider.sign_message(HEX_SHAPED_MESSAGE)
    recovered = Account.recover_message(
        encode_defunct(text=HEX_SHAPED_MESSAGE), signature=result["signature"]
    )
    assert recovered.lower() == provider.address.lower()
