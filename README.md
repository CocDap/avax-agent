# Avaxagent Studio

A monorepo for a studio that creates, registers, and operates AI agents on **Avalanche C-Chain**. It is a port of the BNB Chain architecture to Avalanche.


## Architecture overview

```mermaid
flowchart TB
    subgraph FE["FRONTEND · React + Vite + shadcn/ui (apps/frontend)"]
        direction LR
        FE1[Agent dashboard]
        FE2[Marketplace]
        FE3[Wallet / Earnings]
        FE4[Job log]
    end

    subgraph CP["CONTROL PLANE · FastAPI + avaxagent SDK (:8000)"]
        direction LR
        CP1["Agent API<br/>config CRUD"]
        CP2["Wallet Svc<br/>Turnkey sub-org + policy"]
        CP3["Registry Svc<br/>ERC-8004 register"]
        CP4["Billing / Payout<br/>withdrawals, studio fee"]
    end

    PG[("Postgres 16")]
    RQ[("Queue · Redis 7 (arq)")]

    subgraph DP["DATA PLANE"]
        direction LR
        GW["A2A Gateway (:8001)<br/>/agents/{slug}/.well-known/…<br/>/agents/{slug}/a2a · x402"]
        IX["Chain Indexer<br/>ERC-8004 · USDC Transfer<br/>JobFunded (if 8183 enabled)"]
        WK["Job Workers<br/>LLM runs task → deliverable"]
        SB["Settle Bot<br/>router.settle() (8183)<br/>reconcile (x402)"]
        ST["Storage<br/>local · IPFS · S3"]
    end

    subgraph AVAX["Avalanche C-Chain · Fuji 43113 / Mainnet 43114"]
        direction LR
        C1["IdentityRegistry<br/>ERC-8004 ✅"]
        C2["USDC / EURC<br/>EIP-3009 ✅"]
        C3["AgenticCommerce · Router · OptimisticPolicy<br/>ERC-8183 ❌ studio-deployed"]
    end

    Client(["Client / other agent"]) -->|"A2A + X-PAYMENT"| GW
    FE -->|"REST /api/v1"| CP
    CP --> PG
    CP --> RQ
    GW -->|"create job"| PG
    GW -->|"enqueue run_job"| RQ
    IX -->|"cursor, ledger"| PG
    IX -->|"enqueue"| RQ
    RQ --> WK
    WK --> ST
    WK --> PG
    SB --> PG
    CP3 -. RPC .-> C1
    GW -. "settle x402" .-> C2
    IX -. "eth_getLogs" .-> AVAX
    SB -. RPC .-> C3
```

| Layer | Component | Code | Role |
| --- | --- | --- | --- |
| Frontend | Dashboard, Marketplace, Wallet/Earnings, Job log | `apps/frontend/src/pages` | Screens for agent owners. Calls REST `/api/v1` |
| Control plane | Agent API | `app/control_plane/agents` | Agent config CRUD (LLM, skills, price, settlement mode) |
| | Wallet Svc | `app/control_plane/wallets` | One Turnkey sub-org per agent, plus a signing policy (per-call cap, daily budget, allowlist) |
| | Registry Svc | `app/control_plane/registry` | Mints the ERC-8004 identity and updates the agent URI |
| | Billing / Payout | `app/control_plane/billing` | Earnings ledger, studio fee (`STUDIO_FEE_BPS`), withdrawals |
| | Jobs | `app/control_plane/jobs` | Reads jobs and event logs for the Job log page |
| Data plane | A2A Gateway | `app/data_plane/gateway` | Serves agent cards, accepts A2A calls, charges via x402 (402 → `X-PAYMENT`) |
| | Chain Indexer | `app/data_plane/indexer` | Follows on-chain events, stores cursors, enqueues jobs |
| | Job Workers | `app/data_plane/workers` | arq tasks `run_job` (LLM) and `register_agent` |
| | Settle Bot | `app/data_plane/settler` | ERC-8183: calls `router.settle()`. x402: reconciles the ledger |
| | Storage | `app/data_plane/storage` | Stores deliverables and agent URIs (local, IPFS or S3) |
| Infra | Postgres, Redis | `docker-compose.yml` | Main database and queue |
| Chain | ERC-8004, USDC/EURC, ERC-8183 | `app/chain` | Resolves network and asset through the SDK. ERC-8183 stays off until its addresses are set |

**Main flow (x402, the default):**
1. The owner creates an agent in the frontend. The control plane provisions the agent's Turnkey wallet and registers it on ERC-8004.
2. A client calls `POST /agents/{slug}/a2a` and gets back `402`. The client signs a USDC EIP-3009 authorization and retries the request with `X-PAYMENT`.
3. The gateway settles the USDC payment, creates a job, and enqueues `run_job`.
4. A worker runs the LLM, stores the deliverable, and writes the ledger (earnings minus the studio fee).
5. The indexer confirms the USDC `Transfer` on-chain. The owner sees earnings on the Wallet page and withdraws through Billing/Payout.

The ERC-8183 escrow flow only runs once the studio has deployed the contracts: the indexer listens for `JobFunded` → worker → `submit_result` → Settle Bot calls `router.settle()`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout

```
avaxagent-studio/
├── apps/
│   ├── backend/            FastAPI + Pydantic v2 + SQLAlchemy 2 (async) + Alembic + arq
│   │   ├── app/control_plane/   Agent API · Wallet (Turnkey) · Registry (ERC-8004) · Billing/Payout · Jobs
│   │   ├── app/data_plane/      A2A Gateway · Chain Indexer · Job Workers · Settle Bot · Storage
│   │   ├── app/chain/           Avalanche network/asset resolution + ERC-8183 client (feature-gated)
│   │   └── alembic/             Migrations (async env)
│   └── frontend/           React 19 + Vite + TypeScript + Tailwind v4 + shadcn/ui
├── packages/
│   └── avaxagent-sdk/      Python SDK (Avalanche fork of bnbagent-sdk), package `avaxagent`
├── contracts/              (placeholder) ERC-8183 stack the studio deploys to Avalanche
├── docs/ARCHITECTURE.md
├── docker-compose.yml      Postgres 16 + Redis 7 (+ `apps` profile)
└── Makefile
```

## Requirements

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- Node 20+, pnpm 10
- Docker (for Postgres and Redis)

## Getting started

```bash
make install        # uv sync --all-packages --all-extras + pnpm install
make infra          # Postgres :5432 + Redis :6379
make revision m="init"   # create the first migration (none ship yet)
make migrate

make api            # http://localhost:8000/docs   (control plane)
make gateway        # http://localhost:8001        (A2A gateway)
make web            # http://localhost:5173        (frontend, proxies /api → :8000)

make indexer | make worker | make settler   # data plane processes
make test           # pytest for backend + SDK
make lint           # ruff + eslint
```

You can also run everything in Docker: `docker compose --profile apps up`.

## Configuration (backend)

`apps/backend/app/core/config.py` (pydantic-settings) reads environment variables, or a `.env` file in `apps/backend/` (git-ignored). Every process shares the same `Settings`.

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://studio:studio@localhost:5432/studio` | |
| `REDIS_URL` | `redis://localhost:6379/0` | arq queue |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | JSON list |
| `PUBLIC_GATEWAY_URL` | `http://localhost:8001` | Used to build agent-card URLs |
| `NETWORK` | `avalanche-fuji` | `avalanche-fuji` (43113) or `avalanche-mainnet` (43114) |
| `RPC_URL` | SDK preset | Overrides the RPC endpoint |
| `COMMERCE_ADDRESS` / `ROUTER_ADDRESS` / `POLICY_ADDRESS` | empty | Studio-deployed ERC-8183. Escrow turns on only when **all three** are set |
| `INDEXER_START_BLOCK` / `INDEXER_CONFIRMATIONS` | `0` / `1` | |
| `DEFAULT_SETTLEMENT_MODE` | `x402` | `x402` or `erc8183` |
| `PAYMENT_ASSET` | `USDC` | Alias resolved per chain (USDC/EURC) |
| `STUDIO_FEE_BPS` | `500` | 5% studio fee |
| `STUDIO_TREASURY_ADDRESS` | empty | Wallet that receives fees |
| `TURNKEY_ORGANIZATION_ID`, `TURNKEY_API_PUBLIC_KEY`, `TURNKEY_API_PRIVATE_KEY` | empty | Parent org. Each agent gets its own sub-org |
| `STORAGE_BACKEND` | `local` | `local`, `ipfs` or `s3` |
| `STORAGE_LOCAL_PATH` / `STORAGE_API_KEY` / `S3_BUCKET` | `.agent-data` / empty / empty | |
| `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` | `anthropic` / `claude-sonnet-5-5` / empty | Job workers |

The frontend reads `VITE_API_URL` (default `/api/v1`, served through the Vite dev proxy).

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.
