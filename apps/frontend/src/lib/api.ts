import type {
  Agent,
  AgentCreate,
  EarningsSummary,
  FeeSchedule,
  Job,
  LedgerEntry,
  MarketplaceAgent,
  NetworkInfo,
  RegistrationStatus,
  Wallet,
  WalletBalances,
} from "@/lib/types";

const BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API ${status}`);
    this.status = status;
    this.body = body;
  }

  /** Backend route exists but has no logic yet (scaffold → HTTP 501). */
  get notImplemented() {
    return this.status === 501;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const body = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body);
  return body as T;
}

const post = (body?: unknown): RequestInit => ({
  method: "POST",
  body: JSON.stringify(body ?? {}),
});

/** Typed client for the control-plane REST API (`apps/backend`). */
export const api = {
  network: () => request<NetworkInfo>("/network"),

  agents: {
    list: () => request<Agent[]>("/agents"),
    get: (id: string) => request<Agent>(`/agents/${id}`),
    create: (body: AgentCreate) => request<Agent>("/agents", post(body)),
    wallet: (id: string) => request<Wallet>(`/agents/${id}/wallet`),
    provisionWallet: (id: string) => request<Wallet>(`/agents/${id}/wallet`, post()),
    balances: (id: string) => request<WalletBalances>(`/agents/${id}/wallet/balances`),
    registration: (id: string) => request<RegistrationStatus>(`/agents/${id}/registration`),
    register: (id: string) => request<RegistrationStatus>(`/agents/${id}/registration`, post()),
  },

  marketplace: (q?: string) =>
    request<MarketplaceAgent[]>(
      `/marketplace/agents${q ? `?q=${encodeURIComponent(q)}` : ""}`,
    ),

  billing: {
    fees: () => request<FeeSchedule>("/billing/fees"),
    summary: () => request<EarningsSummary>("/billing/summary"),
    ledger: () => request<LedgerEntry[]>("/billing/ledger"),
  },

  jobs: {
    list: () => request<Job[]>("/jobs"),
  },
};
