"""Application settings (pydantic-settings).

Every process (API, gateway, indexer, workers, settler) reads the same
``Settings``. Values come from environment variables, optionally loaded from a
local dotenv file in ``apps/backend/``.

Avalanche notes
---------------
* ``network`` selects an ``avaxagent`` preset: ``avalanche-fuji`` (43113,
  default) or ``avalanche-mainnet`` (43114).
* ERC-8004 Identity Registry is live on both chains (address from the SDK).
* ERC-8183 (AgenticCommerce / EvaluatorRouter / OptimisticPolicy) is NOT
  deployed on Avalanche. The studio must deploy its own stack (see
  ``contracts/``) and set the three ``commerce_*`` addresses; until then the
  escrow flow stays disabled and agents settle through x402 (USDC EIP-3009).
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettlementMode(str, Enum):
    """How a client pays an agent for a job."""

    X402 = "x402"  # pay-per-call, USDC EIP-3009 (available on Avalanche today)
    ERC8183 = "erc8183"  # on-chain escrow (needs studio-deployed contracts)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────────
    app_name: str = "Avaxagent Studio"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    public_gateway_url: str = "http://localhost:8001"

    # ── Infra ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://studio:studio@localhost:5432/studio"
    redis_url: str = "redis://localhost:6379/0"

    # ── Chain (Avalanche C-Chain) ──────────────────────────────────────────
    network: str = "avalanche-fuji"
    rpc_url: str | None = None  # overrides the SDK preset RPC when set

    # ERC-8183 stack deployed BY THE STUDIO on Avalanche (empty = disabled).
    commerce_address: str | None = None
    router_address: str | None = None
    policy_address: str | None = None
    indexer_start_block: int = 0
    indexer_confirmations: int = 1

    # ── Payments / billing ─────────────────────────────────────────────────
    default_settlement_mode: SettlementMode = SettlementMode.X402
    payment_asset: str = "USDC"  # resolved per chain via avaxagent.networks
    studio_fee_bps: int = 500  # 5% studio fee on agent income
    studio_treasury_address: str | None = None

    # ── Wallets (Turnkey parent org; one sub-org per agent) ───────────────
    turnkey_organization_id: str | None = None
    turnkey_api_public_key: str | None = None
    turnkey_api_private_key: str | None = None
    turnkey_api_base_url: str = "https://api.turnkey.com"

    # ── Storage ────────────────────────────────────────────────────────────
    storage_backend: str = "local"  # local | ipfs | s3
    storage_local_path: str = ".agent-data"
    storage_api_key: str | None = None  # IPFS pinning (Pinata-compatible)
    s3_bucket: str | None = None

    # ── LLM (job workers) ──────────────────────────────────────────────────
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-5-5"
    llm_api_key: str | None = None

    @property
    def commerce_enabled(self) -> bool:
        """True only when the studio-deployed ERC-8183 stack is configured."""
        return bool(self.commerce_address and self.router_address and self.policy_address)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
