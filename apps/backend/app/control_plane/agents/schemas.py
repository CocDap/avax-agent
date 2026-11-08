from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.control_plane.agents.models import AgentStatus
from app.core.config import SettlementMode

SLUG_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{1,62}[a-z0-9])?$"


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-5-5"
    system_prompt: str = ""
    temperature: float = Field(default=0.2, ge=0, le=2)


class AgentCreate(BaseModel):
    slug: str = Field(pattern=SLUG_PATTERN)
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    skills: list[str] = Field(default_factory=list)
    settlement_mode: SettlementMode = SettlementMode.X402
    price_atomic: int = Field(default=0, ge=0, description="Price in payment-asset atomic units")
    is_public: bool = False


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    llm_config: LLMConfig | None = None
    skills: list[str] | None = None
    settlement_mode: SettlementMode | None = None
    price_atomic: int | None = Field(default=None, ge=0)
    is_public: bool | None = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str
    status: AgentStatus
    is_public: bool
    llm_config: LLMConfig
    skills: list[str]
    settlement_mode: SettlementMode
    price_atomic: int
    chain_id: int
    erc8004_agent_id: int | None
    agent_uri: str | None
    wallet_address: str | None = None
    created_at: datetime
    updated_at: datetime


class MarketplaceAgent(BaseModel):
    """Public projection of an agent (no owner / config internals)."""

    slug: str
    name: str
    description: str
    skills: list[str]
    settlement_mode: SettlementMode
    price_atomic: int
    chain_id: int
    erc8004_agent_id: int | None
    agent_card_url: str
