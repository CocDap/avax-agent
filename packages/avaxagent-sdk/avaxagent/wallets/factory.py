"""Wallet provider factory — a single creation entry point.

Each provider has its own creation lifecycle (the EVM provider loads or
auto-generates an encrypted keystore in its constructor; the Turnkey provider
delegates custody to a remote enclave), so there is no shared key store. This
factory does not try to unify *storage* — it unifies *selection*: given a
``kind`` string (typically from configuration) plus provider-specific keyword
arguments, it constructs the matching :class:`WalletProvider`.

Example::

    wallet = create_wallet_provider("evm", password="pw")
    wallet = TurnkeyWalletProvider.from_env()  # or create_wallet_provider("turnkey", ...)
"""

from __future__ import annotations

from typing import Any

from .wallet_provider import WalletProvider

#: Wallet kinds the factory can construct. Mirrors each provider's ``kind``.
SUPPORTED_WALLET_KINDS: tuple[str, ...] = ("evm", "mpc", "turnkey")


def create_wallet_provider(kind: str, **kwargs: Any) -> WalletProvider:
    """Construct a :class:`WalletProvider` for ``kind``.

    Args:
        kind: Provider identifier (case-insensitive): ``"evm"``, ``"mpc"``
            or ``"turnkey"``.
        **kwargs: Forwarded verbatim to the provider constructor. Required
            arguments differ per kind — e.g. ``EVMWalletProvider`` needs
            ``password=...``; ``TurnkeyWalletProvider`` needs the ``organization_id`` /
            ``sign_with`` / ``api_public_key`` / ``api_private_key``
            credentials (or use ``TurnkeyWalletProvider.from_env()``).

    Returns:
        The constructed provider.

    Raises:
        ValueError: If ``kind`` is not one of :data:`SUPPORTED_WALLET_KINDS`.
        NotImplementedError: If ``kind`` is ``"mpc"`` (stub by design — supply
            your own subclass instead).
    """
    normalized = (kind or "").strip().lower()

    if normalized == "evm":
        from .evm_wallet_provider import EVMWalletProvider

        return EVMWalletProvider(**kwargs)
    if normalized == "mpc":
        from .mpc_wallet_provider import MPCWalletProvider

        return MPCWalletProvider(**kwargs)
    if normalized == "turnkey":
        from .turnkey import TurnkeyWalletProvider

        return TurnkeyWalletProvider(**kwargs)

    raise ValueError(
        f"Unknown wallet kind {kind!r}. "
        f"Supported kinds: {', '.join(SUPPORTED_WALLET_KINDS)}."
    )
