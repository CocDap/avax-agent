// Mirrors apps/backend/app/control_plane/*/schemas.py.
// TODO: generate from the backend OpenAPI schema (e.g. openapi-typescript).

export type SettlementMode = "x402" | "erc8183";
export type AgentStatus = "draft" | "provisioning" | "registering" | "active" | "paused";
export type JobStatus =
  | "negotiating"
  | "funded"
  | "running"
  | "submitted"
  | "settled"
  | "failed"
  | "refunded";
export type LedgerKind = "income" | "studio_fee" | "payout" | "gas";

export interface LLMConfig {
  provider: string;
  model: string;
  system_prompt: string;
  temperature: number;
}

export interface Agent {
  id: string;
  slug: string;
  name: string;
  description: string;
  status: AgentStatus;
  is_public: boolean;
  llm_config: LLMConfig;
  skills: string[];
  settlement_mode: SettlementMode;
  price_atomic: number;
  chain_id: number;
  erc8004_agent_id: number | null;
  agent_uri: string | null;
  wallet_address: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  slug: string;
  name: string;
  description?: string;
  llm_config?: Partial<LLMConfig>;
  skills?: string[];
  settlement_mode?: SettlementMode;
  price_atomic?: number;
  is_public?: boolean;
}

export interface MarketplaceAgent {
  slug: string;
  name: string;
  description: string;
  skills: string[];
  settlement_mode: SettlementMode;
  price_atomic: number;
  chain_id: number;
  erc8004_agent_id: number | null;
  agent_card_url: string;
}

export interface WalletPolicy {
  max_value_per_call_atomic: number;
  daily_budget_atomic: number;
  allowed_contracts: string[];
  allow_erc8183: boolean;
}

export interface Wallet {
  id: string;
  provider: string;
  address: string;
  chain_id: number;
  turnkey_sub_org_id: string | null;
  policy: WalletPolicy;
}

export interface WalletBalances {
  address: string;
  chain_id: number;
  avax_wei: number;
  payment_asset: string;
  payment_asset_atomic: number;
}

export interface RegistrationStatus {
  chain_id: number;
  identity_registry: string;
  state: "not_registered" | "pending" | "registered" | "failed";
  erc8004_agent_id: number | null;
  agent_uri: string | null;
  tx_hash: string | null;
  explorer_url: string | null;
}

export interface NetworkInfo {
  network: string;
  chain_id: number;
  rpc_url: string;
  explorer_url: string;
  identity_registry: string;
  payment_asset: string;
  payment_asset_address: string;
  erc8183_enabled: boolean;
}

export interface FeeSchedule {
  studio_fee_bps: number;
  payment_asset: string;
  payment_asset_address: string;
  chain_id: number;
}

export interface EarningsSummary {
  agent_id: string | null;
  gross_income_atomic: number;
  studio_fees_atomic: number;
  paid_out_atomic: number;
  withdrawable_atomic: number;
}

export interface LedgerEntry {
  id: string;
  agent_id: string;
  job_id: string | null;
  kind: LedgerKind;
  asset: string;
  amount_atomic: number;
  tx_hash: string | null;
  created_at: string;
}

export interface Job {
  id: string;
  agent_id: string;
  settlement_mode: SettlementMode;
  status: JobStatus;
  chain_id: number;
  chain_job_id: number | null;
  client_address: string | null;
  amount_atomic: number;
  asset: string;
  deliverable_uri: string | null;
  payment_tx_hash: string | null;
  submit_tx_hash: string | null;
  settle_tx_hash: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}
