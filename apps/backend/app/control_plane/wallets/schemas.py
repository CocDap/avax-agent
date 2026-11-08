from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class WalletPolicy(BaseModel):
    """Spending guard rails applied in two layers.

    * Turnkey policy (server side, in the sub-org): which contracts / methods
      the agent's key may sign for.
    * avaxagent ``SigningPolicy`` + ``X402Signer`` (client side): EIP-712 domain
      allowlist (Avalanche USDC/EURC), per-call cap and session budget.
    """

    max_value_per_call_atomic: int = Field(default=1_000_000, ge=0)  # 1 USDC
    daily_budget_atomic: int = Field(default=50_000_000, ge=0)  # 50 USDC
    allowed_contracts: list[str] = Field(default_factory=list)
    allow_erc8183: bool = False  # only meaningful once the studio deploys ERC-8183


class WalletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    address: str
    chain_id: int
    turnkey_sub_org_id: str | None
    policy: WalletPolicy


class WalletBalances(BaseModel):
    address: str
    chain_id: int
    avax_wei: int  # gas (Avalanche has no paymaster)
    payment_asset: str
    payment_asset_atomic: int
