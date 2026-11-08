# Architecture: Avaxagent Studio on Avalanche

```
┌──────────────────────────────── FRONTEND (React + Vite + shadcn/ui) ────────────────────────────────┐
│   Agent dashboard  ·  Marketplace  ·  Wallet / Earnings  ·  Job log          apps/frontend          │
└──────────────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                               │ REST /api/v1
┌──────────────────────────── CONTROL PLANE (FastAPI + avaxagent SDK) ────────────────────────────────┐
│  Agent API          Wallet Svc               Registry Svc            Billing / Payout               │
│  config CRUD        Turnkey sub-org + policy ERC-8004 register       withdrawals, studio fee        │
│  control_plane/     control_plane/wallets    control_plane/registry  control_plane/billing          │
│  agents, jobs                                                                                       │
└───────────────┬──────────────────────────────────────────────────────────────┬──────────────────────┘
                │                                                              │
        ┌───────▼────────┐                                            ┌────────▼────────┐
        │  Postgres 16   │◄───────────────────────────────────────────┤  Queue (Redis)  │  arq
        └───────▲────────┘                                            └────────▲────────┘
                │                                                              │ enqueue run_job
┌───────────────┴────────────────────────────── DATA PLANE ────────────────────┴──────────────────────┐
│  A2A Gateway (:8001)              Chain Indexer                   Job Workers        Settle Bot     │
│  /agents/{slug}/.well-known/…     ERC-8004 identity events        LLM runs task →    ERC-8183:      │
│  /agents/{slug}/a2a               USDC Transfer → agent wallet    deliverable →      router.settle()│
│  402 → X-PAYMENT (x402) → job     JobFunded (only if 8183 on)     storage, submit    x402: reconcile│
│                                                                                      Storage IPFS/S3│
└──────────────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                               │ RPC (gas paid in AVAX)
┌──────────────────────────────── Avalanche C-Chain (Fuji 43113 / Mainnet 43114) ─────────────────────┐
│  IdentityRegistry (ERC-8004) ✅    USDC / EURC (EIP-3009) ✅    Multicall3 ✅                       │
│  AgenticCommerce · EvaluatorRouter · OptimisticPolicy (ERC-8183): ❌ studio-deployed → contracts/   │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Two settlement modes (`SettlementMode`)

### 1. `x402`: the default, works on Avalanche today

1. The client sends `POST /agents/{slug}/a2a` without payment. The gateway answers `402` with `accepts` (USDC on the current chain, `payTo` = agent wallet, `maxAmountRequired` = price).
2. The client signs an EIP-3009 `TransferWithAuthorization` (SDK: `X402Signer`) and retries the request with an `X-PAYMENT` header.
3. The gateway verifies the signature and settles the USDC on-chain, then creates `Job(status=funded)` and enqueues `run_job`.
4. A worker calls the LLM, uploads the deliverable to storage, updates the job to `Job(status=settled)`, and writes `LedgerEntry` rows (income + studio_fee).
5. The indexer matches USDC `Transfer` events against agent wallets (`x402.income`) to confirm the payment.

### 2. `erc8183`: escrow, available only after the studio deploys the contracts

Enabled once `COMMERCE_ADDRESS`, `ROUTER_ADDRESS` and `POLICY_ADDRESS` are all set (`settings.commerce_enabled`). The flow matches BSC:

1. The indexer listens for `JobFunded`, creates a `Job`, and enqueues it.
2. A worker runs the task, then calls `submit_result`.
3. The Settle Bot calls `router.settle()`.

The ABIs live in `apps/backend/app/chain/abis/` (copied from bnbagent-sdk).

## Agent wallets (Turnkey)

- Each agent gets its own Turnkey **sub-org** with a non-root API user.
- Server-side policy: the key may only sign EIP-712 messages for Avalanche's USDC/EURC domains, and transactions to allowlisted contracts.
- On the client side, the SDK's `SigningPolicy` and `X402Signer` add a per-call cap and a daily budget (`WalletPolicy`).
- Avalanche has no paymaster, so each agent wallet needs a little AVAX to register on ERC-8004 and to settle.

## Processes and entrypoints

| Process | Command | Module |
| --- | --- | --- |
| API | `make api` | `app.main:app` |
| A2A Gateway | `make gateway` | `app.data_plane.gateway.main:app` |
| Indexer | `make indexer` | `app.data_plane.indexer` (streams: `erc8004.identity`, `x402.income`, `erc8183.jobs`) |
| Workers | `make worker` | `app.data_plane.workers.settings.WorkerSettings` (`run_job`, `register_agent`) |
| Settle Bot | `make settler` | `app.data_plane.settler` |

## Database tables (Alembic metadata)

`agents`, `wallets`, `jobs`, `job_events`, `ledger_entries`, `payouts`, `indexer_cursors`.

Amounts are stored as `Numeric(78,0)` in atomic units (USDC has 6 decimals).
