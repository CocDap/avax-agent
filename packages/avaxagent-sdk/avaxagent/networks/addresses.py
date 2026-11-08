"""On-chain address registry for Avalanche C-Chain deployments.

Covers Avalanche C-Chain mainnet (43114) and the Fuji testnet (43113). Every
address below was verified on-chain (``eth_getCode`` non-empty; token
``DOMAIN_SEPARATOR()`` recomputed from ``name``/``version``/``chainId``):

- ``identity_registry`` — canonical ERC-8004 Identity Registry
  (``AgentIdentity`` / ``AGENT``, ``getVersion() == "2.0.0"``). Same vanity
  CREATE2 addresses used on every EVM chain the registry ships on.
- ``usdc`` — Circle native USDC (FiatTokenV2, EIP-3009, domain
  ``name="USD Coin"`` / ``version="2"``, 6 decimals).
- ``multicall3`` — the canonical Multicall3 deployment.

Not present on Avalanche and therefore **not** part of this fork: the ERC-8183
commerce stack (AgenticCommerce / EvaluatorRouter / OptimisticPolicy), the
U-token (United Stables) payment token, and the MegaFuel paymaster.

Only ``usdc`` is an EIP-712 verifyingContract (EIP-3009
``TransferWithAuthorization``). The other addresses are direct-call targets
exposed purely as a lookup convenience — they are **not** added to any signing
allowlist.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from web3 import Web3

# ── Chain ids ──────────────────────────────────────────────────────────────

AVALANCHE_MAINNET_CHAIN_ID = 43114
AVALANCHE_FUJI_CHAIN_ID = 43113

# ── EIP-712 domain metadata for the default payment token (verified on-chain) ─

PAYMENT_TOKEN_EIP712_NAME = "USD Coin"
PAYMENT_TOKEN_EIP712_VERSION = "2"


@dataclass(frozen=True)
class DeployedAddresses:
    """Snapshot of one network's contract deployment."""

    identity_registry: str
    payment_token: str
    multicall3: str


# Raw addresses as verified on-chain. Stored pre-checksum to stay easy to diff
# against block explorers; the public ``AVALANCHE_ADDRESSES`` table below is the
# checksummed form.
_RAW: dict[int, dict[str, str]] = {
    AVALANCHE_FUJI_CHAIN_ID: {
        "identity_registry": "0x8004A818BFB912233c491871b3d84c89A494BD9e",
        "payment_token": "0x5425890298aed601595a70AB815c96711a31Bc65",
        "multicall3": "0xcA11bde05977b3631167028862bE2a173976CA11",
    },
    AVALANCHE_MAINNET_CHAIN_ID: {
        "identity_registry": "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432",
        "payment_token": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        "multicall3": "0xcA11bde05977b3631167028862bE2a173976CA11",
    },
}


def _build() -> dict[int, DeployedAddresses]:
    out: dict[int, DeployedAddresses] = {}
    field_names = {f.name for f in fields(DeployedAddresses)}
    for chain_id, raw in _RAW.items():
        missing = field_names - raw.keys()
        if missing:
            raise RuntimeError(f"chain {chain_id} missing addresses: {missing}")
        out[chain_id] = DeployedAddresses(
            **{k: Web3.to_checksum_address(v) for k, v in raw.items()}
        )
    return out


AVALANCHE_ADDRESSES: dict[int, DeployedAddresses] = _build()


def get_address(chain_id: int) -> DeployedAddresses:
    """Return the deployment snapshot for ``chain_id``.

    Raises:
        KeyError: if ``chain_id`` is not a known Avalanche deployment.
    """
    try:
        return AVALANCHE_ADDRESSES[chain_id]
    except KeyError as e:
        raise KeyError(
            f"no Avalanche deployment registered for chain_id={chain_id}; "
            f"known: {sorted(AVALANCHE_ADDRESSES)}"
        ) from e


def known_payment_tokens() -> frozenset[tuple[int, str]]:
    """``(chain_id, checksum_address)`` pairs of every registered default payment token.

    ``SigningPolicy.strict_default()`` derives its domain allowlist from active
    catalog assets with verified EIP-3009 metadata (see
    :func:`avaxagent.networks.known_eip3009_payment_tokens`), so this set must
    not be used to infer every strict-signing domain.
    """
    return frozenset(
        (cid, deploy.payment_token) for cid, deploy in AVALANCHE_ADDRESSES.items()
    )
