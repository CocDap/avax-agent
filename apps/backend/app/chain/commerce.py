"""ERC-8183 agentic-commerce contracts on Avalanche (studio-deployed).

The upstream BNB Chain stack (AgenticCommerce kernel, EvaluatorRouter,
OptimisticPolicy) has no Avalanche deployment, and the avaxagent SDK does not
ship an ERC-8183 client. The studio therefore:

1. deploys the three contracts to Fuji/mainnet itself (``contracts/``),
2. sets ``COMMERCE_ADDRESS`` / ``ROUTER_ADDRESS`` / ``POLICY_ADDRESS``,
3. talks to them with web3 + the ABIs vendored in ``app/chain/abis/``.

Until all three addresses are configured, everything here reports disabled and
callers fall back to x402 settlement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.errors import FeatureDisabled, NotImplementedYet

ABI_DIR = Path(__file__).parent / "abis"

#: Event the chain indexer watches to enqueue jobs (escrow funded by a client).
JOB_FUNDED_EVENT = "JobFunded"


@dataclass(frozen=True)
class CommerceContracts:
    commerce: str
    router: str
    policy: str


@lru_cache
def load_abi(name: str) -> list[dict[str, Any]]:
    """Load a vendored ABI: ``AgenticCommerce`` | ``EvaluatorRouter`` | ``OptimisticPolicy``."""
    data = json.loads((ABI_DIR / f"{name}.json").read_text())
    return data["abi"] if isinstance(data, dict) else data


def contracts() -> CommerceContracts:
    """Configured ERC-8183 addresses, or ``FeatureDisabled`` (HTTP 409)."""
    if not settings.commerce_enabled:
        raise FeatureDisabled(
            "erc8183",
            "ERC-8183 is not deployed on Avalanche; deploy contracts/ and set "
            "COMMERCE_ADDRESS, ROUTER_ADDRESS and POLICY_ADDRESS",
        )
    assert settings.commerce_address and settings.router_address and settings.policy_address
    return CommerceContracts(
        commerce=settings.commerce_address,
        router=settings.router_address,
        policy=settings.policy_address,
    )


class CommerceClient:
    """web3 wrapper for the studio's ERC-8183 deployment (to be implemented).

    Mirrors the upstream ``bnbagent.erc8183`` surface the data plane needs.
    """

    def __init__(self, wallet_provider: Any | None = None) -> None:
        self.contracts = contracts()
        self.wallet_provider = wallet_provider

    def get_job(self, job_id: int) -> dict[str, Any]:
        raise NotImplementedYet("erc8183.get_job")

    def submit_result(self, job_id: int, deliverable_uri: str, deliverable_hash: bytes) -> str:
        """Provider submits the deliverable (``ops.submit_result`` upstream)."""
        raise NotImplementedYet("erc8183.submit_result")

    def settle(self, job_id: int) -> str:
        """Permissionless ``router.settle`` once the policy verdict is final."""
        raise NotImplementedYet("erc8183.settle")
