# Avaxagent Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the scaffolded monorepo into a working studio where owners create agents on Avalanche, give each one a Turnkey wallet and an ERC-8004 identity, sell its work over A2A with x402 (USDC EIP-3009) payments, and withdraw earnings minus the studio fee.

**Architecture:** FastAPI control plane (`/api/v1`) and a separate A2A gateway share one Postgres and one Redis (arq). Background processes (workers, indexer, settler) consume the queue and the chain. Every chain or vendor call goes through a small protocol (`Relayer`, `ChainReader`, `TurnkeyAdmin`, `LlmRunner`), so tests inject fakes and only opt-in tests touch Fuji. ERC-8183 escrow stays behind `settings.commerce_enabled` and comes last.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 async + asyncpg, Alembic, arq, web3.py (through `avaxagent`), anthropic SDK, PyJWT. React 19, Vite 6, TypeScript 5.8, Tailwind v4, shadcn/ui, TanStack Query 5, react-router 7, wagmi 2 + viem 2, vitest + Testing Library + msw.

**Spec:** `README.md` (architecture overview, config table) and `docs/ARCHITECTURE.md` (settlement flows, wallets, processes). The scaffold under `apps/` fixes the routes, schemas and models this plan fills in.

## Global Constraints

- Network default `avalanche-fuji` (43113). Mainnet is `avalanche-mainnet` (43114). Chain ids, registry and asset addresses always come from `avaxagent.networks` through `app/chain/network.py`. Never hard-code them in services.
- ERC-8004 IdentityRegistry: Fuji `0x8004A818BFB912233c491871b3d84c89A494BD9e`, mainnet `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`.
- USDC: Fuji `0x5425890298aed601595a70AB815c96711a31Bc65`, mainnet `0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E`. 6 decimals.
- Store amounts as Python `int` in atomic units (`Numeric(78,0)`). No floats anywhere in money paths, frontend included: convert with `BigInt` / `formatAtomic`.
- Studio fee is `amount * STUDIO_FEE_BPS // 10_000` (floor). Default `500` bps.
- Default settlement is `x402`. ERC-8183 code paths raise `FeatureDisabled` (HTTP 409) unless `COMMERCE_ADDRESS`, `ROUTER_ADDRESS` and `POLICY_ADDRESS` are all set.
- Gas is paid in AVAX. There is no paymaster. Gas price comes from the SDK (`eth_gasPrice × 1.2`, 1 wei floor).
- An unimplemented route keeps returning HTTP 501 `{"error":"not_implemented","feature":...}` until its task lands. Never silently return empty data.
- Ownership: any agent, wallet, job, ledger or payout that belongs to another owner returns **404**, not 403.
- Ruff line length 99, rules `E,F,I,UP,B`. ESLint clean. `tsc -b` clean.
- Frontend stays React + Vite. No Next.js.
- Never commit `.env*` files. The local hook blocks reading or writing them, so document new variables in the README config table instead.
- New settings go into `app/core/config.py` and the README config table in the same task.

## Review Focus

1. **Replayed or concurrent x402 payments.** The same EIP-3009 authorization (same `nonce`) sent twice, or twice in parallel, must produce exactly one settlement and one job. The second request gets `409 payment_replayed`. Owner: Task 11 (`test_replayed_authorization_rejected`, `test_concurrent_same_nonce_single_job`).
2. **Wrong payment details.** A payment with the wrong `to`, a short `value`, another asset or chain, an expired `validBefore` or a future `validAfter` must answer 402 with a machine-readable `reason`, and must not create a job or a transaction. Owner: Task 10 (parametrized `test_verify_rejects`).
3. **Worker failure after payment.** If the LLM or storage fails, or the worker is retried after a crash, the job ends `failed` with `error` set. Income is recorded once (the client did pay), and a retry never creates a second ledger row. Owner: Task 12 (`test_llm_error_marks_failed_keeps_income`, `test_run_job_idempotent`).
4. **Payout races and overdraw.** A payout above the withdrawable balance, or two payouts racing for the same funds, must leave at most the withdrawable amount reserved. The extra request gets `422 insufficient_balance`. Owner: Task 15 (`test_payout_exceeds_withdrawable`, `test_concurrent_payouts_never_overdraw`).
5. **Indexer restarts and reorg depth.** After a restart the indexer resumes from its cursor. It never processes blocks newer than `head - INDEXER_CONFIRMATIONS`, and re-processing a range creates no duplicate ledger rows. Owner: Task 13 (`test_resume_from_cursor`, `test_respects_confirmations`) and Task 14 (`test_income_idempotent`).

---

## Phases and dependencies

| Phase | Tasks | Depends on | Milestone |
| --- | --- | --- | --- |
| 0 Foundation | 1–2 | — | DB migrated, real login |
| 1 Control plane core | 3–5 | 1, 2 | Agents, jobs, ledger readable via API |
| 2 Wallets | 6–7 | 3 | Each agent gets a Turnkey wallet + policy |
| 3 Registry | 8 | 7 | Agent minted on ERC-8004 (Fuji) |
| 4 Gateway x402 | 9–11 | 5, 7 | Paid A2A call creates a funded job |
| 5 Workers | 12 | 11 | Job runs LLM, deliverable stored, income booked |
| 6 Indexer | 13–14 | 5, 8 | On-chain confirmation of identity + income |
| 7 Payouts | 15–16 | 5, 7 | Owners withdraw, studio fee swept |
| 8 Frontend | 17–21 | API of each phase | Full UI flow on Fuji |
| 9 ERC-8183 (gated) | 22–23 | 12, 13 | Escrow mode once contracts are deployed |
| 10 Ops | 24–25 | all | CI green, mainnet checklist |

Backend tasks run from `apps/backend` unless stated. "Run tests" means `uv run pytest <path> -v`. Postgres must be running (`make infra`).

---

## Phase 0: Foundation

### Task 1: Model hardening, first migration, Postgres test harness

**Files:**
- Modify: `app/control_plane/jobs/models.py` (add `payment_nonce`)
- Modify: `app/control_plane/billing/models.py` (add `log_index`, unique constraint)
- Modify: `app/control_plane/agents/models.py` (add `deleted_at`)
- Create: `alembic/versions/0001_initial.py` (autogenerated)
- Modify: `tests/conftest.py`
- Create: `tests/factories.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces:
  - `Job.payment_nonce: Mapped[str | None]` (`String(66)`, unique). Holds the EIP-3009 nonce and is the replay guard for Task 11.
  - `LedgerEntry.log_index: Mapped[int | None]`, plus `UniqueConstraint("chain_id", "tx_hash", "log_index", "kind", name="uq_ledger_onchain")`. Rows with a NULL `tx_hash` stay unconstrained, which is Postgres behaviour.
  - `Agent.deleted_at: Mapped[datetime | None]` for soft delete.
  - `Agent.registration_tx_hash: Mapped[str | None]` (`String(66)`), the ERC-8004 register tx used by Task 8.
  - Fixtures: `db` (an `AsyncSession` on database `studio_test`, tables truncated after each test) and `api` (an `httpx.AsyncClient` over `app` with `get_session` overridden to yield `db`).
  - Factories: `make_agent(db, owner_id="dev-user", **kw) -> Agent`, `make_wallet(db, **kw) -> Wallet`, `make_job(db, agent, **kw) -> Job`.

- [ ] **Step 1:** Write `tests/test_db.py`. `test_ledger_onchain_unique` inserts two INCOME rows with the same `(chain_id, tx_hash, log_index)` and asserts `IntegrityError`. `test_payment_nonce_unique` does the same for two jobs that share a `payment_nonce`. `test_token_amount_roundtrip` stores `2**255` in `price_atomic` and reads it back unchanged.
- [ ] **Step 2:** Run `uv run pytest tests/test_db.py -v`. Expected: FAIL (the fixture `db` is not defined).
- [ ] **Step 3:** Add the columns and the constraint. In the `conftest.py` session fixture, derive the test URL by replacing the database name in `settings.database_url` with `studio_test`, create the database if it is missing (connect to `postgres` with `AUTOCOMMIT`), then run `Base.metadata.create_all`. Truncate all tables after each test. Keep the existing `client`/`gateway` fixtures, because the scaffold tests rely on them.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: the new tests and the 14 scaffold tests PASS.
- [ ] **Step 5:** Run `uv run alembic revision --autogenerate -m "initial"`, rename the file to `0001_initial.py`, then run `uv run alembic upgrade head` and `uv run alembic check`. Expected: "No new upgrade operations detected."
- [ ] **Step 6:** Commit: `feat(db): initial schema, replay/idempotency constraints, pg test harness`.

### Task 2: SIWE login and JWT sessions

**Files:**
- Create: `app/core/auth/router.py`, `app/core/auth/siwe.py`, `app/core/auth/tokens.py`
- Modify: `app/core/security.py`, `app/core/config.py`, `app/control_plane/router.py`, `pyproject.toml` (add `pyjwt>=2.9`), README config table
- Test: `tests/test_auth.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/auth/nonce -> {"nonce": str}`. The nonce is stored in Redis as `siwe:nonce:{nonce}` with a 300 s TTL.
  - `POST /api/v1/auth/verify {message: str, signature: str} -> {"access_token": str, "token_type": "bearer", "address": str}`.
  - `GET /api/v1/auth/me -> User`.
  - `parse_siwe(message: str) -> SiweMessage` (pydantic: `domain, address, uri, chain_id, nonce, issued_at, expiration_time | None`).
  - `verify_siwe(msg: SiweMessage, signature: str) -> str` returns the checksummed address. It recovers the signer with `eth_account.Account.recover_message(encode_defunct(text=message))`.
  - `issue_token(address: str) -> str` (HS256, `sub` is the lowercase address, `exp` is now + `AUTH_TOKEN_TTL_S`) and `decode_token(token: str) -> str`.
  - `get_current_user` now reads the `Authorization: Bearer` header and returns `User(id=address_lower, address=checksum)`. It raises 401 otherwise.
- New settings: `AUTH_JWT_SECRET` (required outside `environment == "development"`, dev default `"dev-insecure"`), `AUTH_TOKEN_TTL_S=86400`, `AUTH_DOMAIN="localhost:5173"`.

- [ ] **Step 1:** Write `tests/test_auth.py`. Sign the SIWE messages with `eth_account.Account.create()`.
  - `test_login_roundtrip`: nonce, then sign, then verify returns a token. `/auth/me` with that token returns the same address.
  - `test_nonce_single_use`: verifying the same message twice returns 401 the second time.
  - `test_wrong_domain_rejected` and `test_wrong_chain_rejected` (chain id 1) both return 401.
  - `test_expired_token_401`.
  - `test_protected_route_requires_token`: `GET /api/v1/agents` without a token returns 401.
- [ ] **Step 2:** Run the tests. Expected: FAIL (404 on `/auth/nonce`).
- [ ] **Step 3:** Implement. Nonces are consumed with `GETDEL`. The chain id must equal `chain_id()`. In `conftest.py`, add an `auth_headers(address)` helper and make the `api` fixture authenticate as `0x000000000000000000000000000000000000dEaD` by default. Change the `make_agent` default `owner_id` to the lowercase form of that address, so factory rows belong to the default test user.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: PASS. Update the scaffold tests to send auth headers where they now need them.
- [ ] **Step 5:** Commit: `feat(auth): SIWE login with JWT bearer sessions`.

---

## Phase 1: Control plane core

### Task 3: Agent CRUD and marketplace

**Files:**
- Modify: `app/control_plane/agents/service.py`, `app/control_plane/agents/router.py`
- Test: `tests/control_plane/test_agents.py`

**Interfaces:**
- Consumes: the `db`/`api` fixtures and `make_agent` (Task 1), `CurrentUser` (Task 2).
- Produces:
  - All `AgentService` methods are implemented and keep their scaffold signatures.
  - `AgentService.get_owned(owner_id, agent_id) -> Agent` returns the ORM row and raises `HTTPException(404)`. Tasks 7, 8 and 15 reuse it.
  - `AgentService.get_by_slug(slug) -> Agent | None` returns only ACTIVE agents that are not deleted. The gateway uses it.
  - `AgentRead.wallet_address` comes from a join on `wallets`.

- [ ] **Step 1:** Write the tests.
  - `test_create_returns_draft`: status `draft`, `chain_id == 43113`.
  - `test_duplicate_slug_409`: body `{"error":"slug_taken"}`.
  - `test_list_only_own_agents`.
  - `test_get_other_owner_404`.
  - `test_patch_updates_fields`.
  - `test_delete_soft_pauses`: after delete the agent is gone from the list, and the DB row has `deleted_at` set and status `paused`.
  - `test_marketplace_public_active_only`: draft and private agents are excluded.
  - `test_marketplace_search`: `q` matches name, description or a skill, case-insensitive.
  - `test_marketplace_card_url`: equals `f"{PUBLIC_GATEWAY_URL}/agents/{slug}/.well-known/agent-card.json"`.
- [ ] **Step 2:** Run. Expected: FAIL (501).
- [ ] **Step 3:** Implement with SQLAlchemy `select`. Map `IntegrityError` on `uq_agents_slug` to 409. For search, use `ilike` on name and description, plus a JSON text cast for skills.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(agents): CRUD + marketplace listing`.

### Task 4: Job log read API

**Files:**
- Modify: `app/control_plane/jobs/service.py`
- Create: `app/control_plane/jobs/events.py`
- Test: `tests/control_plane/test_jobs.py`

**Interfaces:**
- Produces:
  - `JobService.list/get/events` are implemented. Only jobs whose agent belongs to the owner are visible. Filters: `agent_id`, `status`, `limit` (≤ 200) and `offset`, newest first.
  - `add_event(db, job: Job, type: str, message: str = "", **data) -> JobEvent`. This is the one place that writes timeline events. Tasks 11, 12 and 23 call it.

- [ ] **Step 1:** Write the tests: `test_list_filters_by_agent_and_status`, `test_other_owner_job_404`, `test_events_chronological`, `test_limit_capped_200`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(jobs): owner-scoped job log + event helper`.

### Task 5: Ledger domain and earnings summary

**Files:**
- Create: `app/control_plane/billing/ledger.py`
- Modify: `app/control_plane/billing/service.py`
- Test: `tests/control_plane/test_ledger.py`

**Interfaces:**
- Produces:
  - `studio_fee(amount: int) -> int`, which is `amount * settings.studio_fee_bps // 10_000`.
  - `async record_income(db, *, job: Job, amount: int, asset: str, tx_hash: str | None, log_index: int | None = None) -> None`. It writes one INCOME row and one STUDIO_FEE row in a single flush. If an INCOME row for this `job_id` already exists it does nothing, which is what makes it idempotent.
  - `async balances(db, agent_id) -> EarningsSummary`, where withdrawable = income − fees − payouts in status `requested | submitted | confirmed`. Failed payouts do not count.
  - `BillingService.summary(owner_id, agent_id | None)` sums across the owner's agents. `BillingService.ledger(...)` lists rows newest first.

- [ ] **Step 1:** Write the tests.
  - `test_fee_floor`: `studio_fee(1) == 0`, `studio_fee(1_000_000) == 50_000`, `studio_fee(19) == 0`.
  - `test_record_income_writes_income_and_fee`.
  - `test_record_income_idempotent`: two calls leave two rows, not four.
  - `test_withdrawable_excludes_failed_payouts`.
  - `test_summary_all_agents_of_owner`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Aggregate with `func.coalesce(func.sum(...), 0)` grouped by `kind`.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(billing): ledger income/fee split + earnings summary`.

---

## Phase 2: Wallets

### Task 6: Turnkey admin client (sub-orgs and policies)

**Files:**
- Create: `app/control_plane/wallets/turnkey_admin.py`
- Test: `tests/control_plane/test_turnkey_admin.py`

**Interfaces:**
- Consumes: `avaxagent.wallets.turnkey.stamper.ApiKeyStamper` for request stamping.
- Produces:
  - Protocol `TurnkeyAdmin`:
    - `create_agent_sub_org(name: str) -> SubOrg`, where `SubOrg` is a dataclass of `sub_org_id, wallet_id, address`. It sends one `ACTIVITY_TYPE_CREATE_SUB_ORGANIZATION_V7` that contains an Ethereum wallet (`m/44'/60'/0'/0/0`, `ADDRESS_FORMAT_ETHEREUM`). The studio API key is the root user.
    - `set_policy(sub_org_id: str, policy: WalletPolicy, *, chain_id: int, allowed_eip712_contracts: list[str]) -> str` returns the policy id. It uses `ACTIVITY_TYPE_CREATE_POLICY_V3` with effect `EFFECT_ALLOW`, and the condition limits signing to `eth.tx.to` / the EIP-712 `verifyingContract` in the allowlist.
  - `HttpTurnkeyAdmin(base_url, api_public_key, api_private_key, organization_id, transport: httpx.BaseTransport | None = None)` and `get_turnkey_admin() -> TurnkeyAdmin`. The factory raises `FeatureDisabled("wallets", "TURNKEY_* not configured")` when settings are missing.
  - `FakeTurnkeyAdmin` in `tests/fakes.py`. It returns deterministic addresses derived from `eth_account` keys, and it keeps those keys so tests can sign.
- Verify the exact activity names and payload fields against the current Turnkey API docs before coding. Record the doc URL in the module docstring.

- [ ] **Step 1:** Write the tests with an `httpx.MockTransport`.
  - `test_create_sub_org_request_shape`: POST to `/public/v1/submit/create_sub_organization`, the `X-Stamp` header is present, and the body `type` is correct.
  - `test_create_sub_org_parses_address`.
  - `test_policy_condition_includes_usdc`: the condition string contains the Fuji USDC address in lowercase.
  - `test_activity_failed_raises`: status `ACTIVITY_STATUS_FAILED` raises `TurnkeyApiError`.
  - `test_missing_config_feature_disabled`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Poll `/public/v1/query/get_activity` while the status is `ACTIVITY_STATUS_PENDING`, at most 10 times with 0.5 s backoff.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(wallets): Turnkey admin client for agent sub-orgs + policies`.

### Task 7: Wallet service and the agent signer factory

**Files:**
- Modify: `app/control_plane/wallets/service.py`, `app/control_plane/wallets/router.py`
- Create: `app/chain/reader.py`, `app/chain/signers.py`
- Test: `tests/control_plane/test_wallets.py`

**Interfaces:**
- Consumes: `TurnkeyAdmin` (Task 6) and `AgentService.get_owned` (Task 3).
- Produces:
  - `WalletService(session, admin: TurnkeyAdmin, reader: ChainReader)`, wired through the `Depends(get_turnkey_admin)` and `Depends(get_chain_reader)` dependencies.
  - `provision`: the agent must be in `draft`. It creates the sub-org, sets the policy (defaults from `WalletPolicy()`), inserts a `Wallet`, sets `agent.wallet_id`, and moves the agent to `provisioning`, which means it is ready to register. A second call returns `409 wallet_exists`.
  - `update_policy`: re-applies the Turnkey policy and stores it in `wallet.policy`.
  - `balances`: returns `WalletBalances` from `reader.native_balance(addr)` and `reader.erc20_balance(usdc, addr)`.
  - Protocol `ChainReader` in `app/chain/reader.py`:
    - `native_balance(address) -> int`
    - `erc20_balance(token, address) -> int`
    - `block_number() -> int`
    - `get_logs(address: str | list[str], topics: list, from_block: int, to_block: int) -> list[dict]`
    - `authorization_used(token, authorizer, nonce: bytes) -> bool`
    - Implementation `Web3ChainReader` uses `avaxagent.core.create_web3` with `network().rpc_url`. A `FakeChainReader` goes in `tests/fakes.py`.
  - `agent_signer(wallet: Wallet) -> WalletProvider` in `app/chain/signers.py`. It returns a `TurnkeyWalletProvider(organization_id=wallet.turnkey_sub_org_id, sign_with=wallet.address, expected_chain_id=chain_id(), signing_policy=SigningPolicy(...from wallet.policy))`. Tests monkeypatch it to return an `EVMWalletProvider` with a local key.

- [ ] **Step 1:** Write the tests: `test_provision_creates_wallet_and_moves_status`, `test_provision_twice_409`, `test_provision_non_draft_409`, `test_policy_update_calls_admin`, `test_balances_from_reader`, `test_wallet_other_owner_404`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(wallets): provision Turnkey wallet per agent, policy + balances`.

---

## Phase 3: Registry

### Task 8: ERC-8004 registration

**Files:**
- Modify: `app/control_plane/registry/service.py`, `app/data_plane/workers/tasks.py` (`register_agent`)
- Create: `app/control_plane/registry/agent_uri.py`
- Test: `tests/control_plane/test_registry.py`, `tests/data_plane/test_register_task.py`, `tests/chain/test_fuji_register.py` (marker `fuji`)

**Interfaces:**
- Consumes: `agent_signer` (Task 7), `erc8004_agent(wallet)` (`app/chain/sdk.py`), `get_storage()`, `get_queue()`.
- Produces:
  - `build_agent_uri(agent: Agent) -> str`. It calls `ERC8004Agent.generate_agent_uri(name, description, endpoints=[AgentEndpoint(name="A2A", endpoint=f"{PUBLIC_GATEWAY_URL}/agents/{slug}/.well-known/agent-card.json", version="0.3.0")])`, then uploads to storage when `STORAGE_BACKEND != "local"` and returns that URL. Otherwise it returns the data URI.
  - `RegistryService.register(owner_id, agent_id, req)`: the agent must have a wallet and be in `provisioning` (otherwise 409). It sets status `registering`, enqueues `REGISTER_AGENT`, and returns `RegistrationStatus(state="pending")`.
  - `RegistryService.status(...)` derives `state` from the agent row: `registered` once `erc8004_agent_id` is set, `pending` while `registering`, otherwise `not_registered`.
  - `refresh_uri` calls `set_agent_uri` on-chain through the worker.
  - Worker `register_agent(ctx, agent_id)`: it skips if `erc8004_agent_id` is already set. Otherwise it calls `register_agent(agent_uri)` and stores `erc8004_agent_id`, `agent_uri` and `registration_tx_hash` on the agent row (column from Task 1). On success the status becomes `active`. On failure the status returns to `provisioning` and the error is logged. `RegistrationStatus.tx_hash` reads `registration_tx_hash`, and `explorer_url` is `f"{network().explorer_url}/tx/{hash}"`.

- [ ] **Step 1:** Write the tests.
  - `test_register_requires_wallet_409`.
  - `test_register_enqueues_and_sets_registering`: the queue is a fake that records calls.
  - `test_task_stores_agent_id`: monkeypatch `erc8004_agent` to return a stub whose `register_agent` returns `{"success": True, "agentId": 42, "transactionHash": "0xab…"}`.
  - `test_task_idempotent_when_registered`.
  - `test_task_failure_reverts_status`.
  - `test_agent_uri_contains_gateway_endpoint`.
  - Opt-in `test_fuji_register` runs only when `FUJI_E2E=1` and a funded key are present.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. The SDK is synchronous, so the worker wraps SDK calls in `asyncio.to_thread`.
- [ ] **Step 4:** Run `uv run pytest -m "not fuji" -v`. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(registry): ERC-8004 registration via worker`.

---

## Phase 4: Gateway (x402)

### Task 9: Agent card

**Files:**
- Modify: `app/data_plane/gateway/service.py`, `app/data_plane/gateway/main.py` (inject `DbSession`)
- Test: `tests/data_plane/test_agent_card.py`

**Interfaces:**
- Consumes: `AgentService.get_by_slug` (Task 3).
- Produces: `agent_card(db, slug) -> dict`, following the A2A AgentCard shape:
  - `name`, `description`, `url = f"{PUBLIC_GATEWAY_URL}/agents/{slug}/a2a"`, `version: "1.0.0"`
  - `capabilities: {"streaming": false}`, `defaultInputModes`/`defaultOutputModes: ["text"]`
  - `skills: [{id, name}]`
  - `extensions.x402 = {network: caip2(), asset: payment_asset_address(), price: str(price_atomic), payTo: wallet.address}`
  - `extensions.erc8004 = {registry: f"{caip2()}:{identity_registry()}", agentId}`
  - An unknown or inactive slug returns 404.

- [ ] **Step 1:** Write the tests: `test_card_for_active_agent` (asserts `url` and `extensions.x402.payTo`), `test_unknown_slug_404`, `test_draft_agent_404`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(gateway): A2A agent card with x402 + ERC-8004 extensions`.

### Task 10: x402 challenge and payment verification

**Files:**
- Create: `app/data_plane/gateway/x402.py`
- Test: `tests/data_plane/test_x402_verify.py`

**Interfaces:**
- Produces:
  - `challenge(agent: Agent, wallet: Wallet) -> dict`, which is the 402 body `{"x402Version": 1, "error": "payment_required", "accepts": [X402Accept(...)]}`. `X402Accept.extra = {"name": "USD Coin", "version": "2"}`, read from the token's EIP-712 domain through `avaxagent.x402.resolve_x402_asset(network, "USDC")`.
  - `decode_payment(header: str) -> PaymentPayload`. `PaymentPayload` is pydantic: `x402Version, scheme, network, payload.signature, payload.authorization{from, to, value, validAfter, validBefore, nonce}`, decoded from base64 JSON.
  - `verify_payment(p: PaymentPayload, *, accept: X402Accept, now: int) -> Authorization`. On failure it raises `PaymentInvalid(reason)`, where `reason` is one of `bad_encoding | wrong_scheme | wrong_network | wrong_recipient | insufficient_value | expired | not_yet_valid | bad_signature`. It recovers the EIP-712 `TransferWithAuthorization` signer with `eth_account` and requires it to equal `authorization.from`.

- [ ] **Step 1:** Write the tests. Sign fixtures with `eth_account` against the real Fuji USDC domain (reuse `avaxagent.signing.EIP3009_TYPES`).
  - `test_valid_payment_passes`.
  - Parametrized `test_verify_rejects[reason]`, one case per reason above: change `to`, `value - 1`, network `eip155:43114`, `validBefore = now - 1`, `validAfter = now + 60`, a signature from another key, and garbage base64.
  - `test_challenge_shape`: `accepts[0].asset` is the Fuji USDC address, `network == "eip155:43113"`, `amount == str(price)`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Keep it pure, with no DB or network access.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(gateway): x402 challenge + EIP-3009 payment verification`.

### Task 11: Settlement relayer, paid A2A call and replay guard

**Files:**
- Create: `app/data_plane/gateway/relayer.py`, `app/data_plane/gateway/a2a.py`
- Modify: `app/data_plane/gateway/service.py`, `app/data_plane/gateway/main.py`, `app/core/config.py` (`RELAYER_SIGN_WITH`, `RELAYER_ORGANIZATION_ID`), README
- Test: `tests/data_plane/test_a2a.py`

**Interfaces:**
- Consumes: `verify_payment`/`challenge` (Task 10), `ChainReader.authorization_used` (Task 7), `add_event` (Task 4), `record_income` (Task 5), `get_queue`.
- Produces:
  - Protocol `Relayer.settle(token: str, auth: Authorization, signature: str) -> str` returns a tx hash. `TurnkeyRelayer` calls USDC `transferWithAuthorization(from, to, value, validAfter, validBefore, nonce, v, r, s)` from the studio relayer wallet, which pays AVAX gas, and waits for the receipt. `FakeRelayer` goes in `tests/fakes.py`.
  - `handle_a2a(db, slug, req, x_payment) -> JSONResponse` handles these JSON-RPC methods:
    - `message/send` with no `X-PAYMENT` returns HTTP 402 and `challenge(...)`.
    - With a valid payment it does the following, in order:
      1. Insert `Job(status=funded, payment_nonce=nonce, client_address=from, amount_atomic=value, asset=usdc, request=params)`. A unique violation on `payment_nonce` returns `409 payment_replayed`.
      2. Check `authorization_used`. If the nonce is already used, roll back and return 409.
      3. `relayer.settle`, then set `payment_tx_hash` and call `record_income(tx_hash=…)`.
      4. `add_event(job, "funded")`, commit, enqueue `RUN_JOB`.
      5. Return a JSON-RPC result with `{"kind": "task", "id": str(job.id), "status": {"state": "submitted"}}`.
    - If the relayer fails, the job is marked `failed`, the response is 502 `settlement_failed`, and no income is recorded.
    - `tasks/get {id}` returns the job state mapped to A2A states (`funded|running → working`, `submitted|settled → completed`, `failed → failed`) plus the deliverable as an artifact.
    - Any other method returns JSON-RPC error `-32601`.
  - Erc8183-mode agents return 409 `FeatureDisabled` until Task 23.

- [ ] **Step 1:** Write the tests.
  - `test_no_payment_returns_402`.
  - `test_paid_call_creates_funded_job_and_enqueues`.
  - `test_replayed_authorization_rejected`: the same header sent twice returns 409, and only one job exists.
  - `test_concurrent_same_nonce_single_job`: two requests through `asyncio.gather` give one 2xx and one 409, and the relayer was called once.
  - `test_relayer_failure_marks_failed_no_income`.
  - `test_tasks_get_maps_state`.
  - `test_unknown_method_jsonrpc_error`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. The job insert and its flush happen before `settle`, so the unique `payment_nonce` serializes concurrent requests. The concurrency test must call `handle_a2a` with two independent sessions from `SessionLocal` bound to the test DB, not the shared `db` fixture, otherwise both requests run inside one transaction.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(gateway): paid A2A message/send via x402 relayer settlement`.

---

## Phase 5: Workers

### Task 12: Job runner (LLM, storage, state machine)

**Files:**
- Create: `app/data_plane/workers/llm.py`
- Modify: `app/data_plane/workers/tasks.py` (`run_job`), `pyproject.toml` (add `anthropic`)
- Test: `tests/data_plane/test_run_job.py`

**Interfaces:**
- Consumes: `add_event` (Task 4), `get_storage()`, `record_income` (Task 5, which is already called by the gateway, so the worker never books income for x402).
- Produces:
  - Protocol `LlmRunner.complete(*, model: str, system: str, prompt: str, temperature: float) -> str`. `AnthropicRunner` uses `anthropic.AsyncAnthropic(api_key=settings.llm_api_key).messages.create(model=…, system=…, max_tokens=4096, temperature=…, messages=[{"role": "user", "content": prompt}])` and joins the text blocks. `get_llm_runner()` raises `FeatureDisabled` when `LLM_API_KEY` is unset.
  - `run_job(ctx, job_id)`:
    - If the status is not `funded`, it returns at once. This makes it idempotent.
    - Otherwise: set `running` and record event `llm_started`, then call the LLM with the agent's `llm_config` and the prompt (the text parts of `job.request["message"]`).
    - Upload `{"job_id", "agent", "output"}` to storage and set `deliverable_uri` and `deliverable_hash` (`keccak` of the canonical JSON).
    - Set `submitted`, record event `submitted`, then, for x402, set `settled` and record event `settled`.
    - On any exception: set `failed`, put `error = str(exc)[:2000]`, record event `failed`, and do not re-raise, so arq does not retry a paid job blindly.

- [ ] **Step 1:** Write the tests, using a `FakeLlmRunner` and local storage in `tmp_path`.
  - `test_run_job_happy_path_settled`: the test seeds a `funded` job plus its `funded` event (as the gateway would). Afterwards the deliverable exists in storage and the events are `[funded, llm_started, submitted, settled]`.
  - `test_run_job_idempotent`: a second call is a no-op, and there is still only one INCOME row.
  - `test_llm_error_marks_failed_keeps_income`.
  - `test_storage_error_marks_failed`.
  - `test_prompt_uses_system_prompt`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. `ctx` carries `llm` and `storage` through arq's `on_startup` in `WorkerSettings`, and tests pass fakes.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(workers): run_job LLM execution + deliverable storage`.

---

## Phase 6: Indexer

### Task 13: Indexer core (cursor, confirmations, batching)

**Files:**
- Modify: `app/data_plane/indexer/service.py`, `app/data_plane/indexer/streams.py`
- Test: `tests/data_plane/test_indexer_core.py`

**Interfaces:**
- Consumes: `ChainReader` (Task 7) and `IndexerCursor`.
- Produces:
  - `Stream` gains `address(db) -> list[str]`, `topics(db) -> list`, and `async handle(db, logs: list[dict]) -> None`.
  - `ChainIndexer(session_factory, reader, streams, batch_size=2000)`.
  - `tick()`, per enabled stream:
    1. `safe = block_number() - INDEXER_CONFIRMATIONS`.
    2. `start = max(cursor.last_block + 1, INDEXER_START_BLOCK)`.
    3. Loop over chunks of at most `batch_size` blocks up to `safe`.
    4. For each chunk, run `get_logs`, `handle`, and the cursor update in one transaction.
  - `run()` loops `tick` with `asyncio.sleep(2)`, which matches Avalanche's roughly 2 s blocks, and logs exceptions without crashing.

- [ ] **Step 1:** Write the tests, using `FakeChainReader` with a scripted head and logs.
  - `test_resume_from_cursor`.
  - `test_respects_confirmations`: with head 100 and confirmations 3, nothing beyond block 97 is processed.
  - `test_chunks_large_ranges`: 5000 blocks with batch 2000 make 3 `get_logs` calls.
  - `test_handler_error_does_not_advance_cursor`.
  - `test_disabled_stream_skipped`: `erc8183.jobs` is skipped when commerce is off.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(indexer): cursor-based log polling with confirmations`.

### Task 14: Identity and income streams

**Files:**
- Modify: `app/data_plane/indexer/streams.py`
- Test: `tests/data_plane/test_streams.py`

**Interfaces:**
- Consumes: Task 13's `Stream` and `record_income` (Task 5).
- Produces:
  - `erc8004.identity`:
    - It watches IdentityRegistry `Registered(agentId, agentURI, owner)` and `URIUpdated` (topics from the SDK ABI `IdentityRegistry.json`) for the managed wallet addresses.
    - It confirms `erc8004_agent_id` and the URI on the agent row, and is the source of truth if the worker crashed after sending.
    - It also handles ERC-721 `Transfer` away from the agent wallet: the agent is marked `paused` and a warning is logged.
  - `x402.income`:
    - It watches USDC `Transfer(from, to, value)` where `to` ∈ managed wallets.
    - When `(tx_hash)` matches a job's `payment_tx_hash`, it sets the INCOME row's `log_index`.
    - Otherwise, for a direct transfer with no job, it books INCOME with `job_id=None`, `tx_hash` and `log_index`. The ledger unique constraint makes this idempotent.

- [ ] **Step 1:** Write the tests: `test_registered_event_confirms_agent`, `test_identity_transfer_pauses_agent`, `test_income_matches_job_payment`, `test_income_direct_transfer_booked`, `test_income_idempotent` (the same logs processed twice leave one row).
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Decode with `web3.Web3().eth.contract(abi=…).events.X().process_log`. Catch `IntegrityError` per row by using a SAVEPOINT (`db.begin_nested()`).
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(indexer): ERC-8004 identity + USDC income streams`.

---

## Phase 7: Payouts and fee sweep

### Task 15: Payout requests and execution

**Files:**
- Modify: `app/control_plane/billing/service.py`, `app/data_plane/settler/service.py`
- Create: `app/data_plane/settler/payouts.py`
- Test: `tests/control_plane/test_payouts.py`, `tests/data_plane/test_payout_executor.py`

**Interfaces:**
- Consumes: `balances` (Task 5), `AgentService.get_owned` (Task 3), `agent_signer` (Task 7), `avaxagent.erc20.MinimalERC20Client`.
- Produces:
  - `BillingService.request_payout(owner_id, body)`:
    - It locks the agent row with `select(Agent).where(...).with_for_update()` and recomputes `balances`.
    - If `amount > withdrawable` it returns `422 {"error":"insufficient_balance","withdrawable":…}`.
    - Otherwise it inserts a `Payout(status=requested)` plus a PAYOUT ledger row, both in one transaction.
  - `list_payouts`.
  - `PayoutExecutor.tick()`:
    - For `requested` payouts it sends `USDC.transfer(destination, amount)` signed by `agent_signer(wallet)` and moves the payout to `submitted` with `tx_hash`.
    - Once the receipt succeeds it moves the payout to `confirmed`.
    - On a revert or error it moves the payout to `failed`, and the PAYOUT ledger row is reversed by deleting it in the same transaction, so the funds become withdrawable again.
  - `SettleBot.tick()` calls `PayoutExecutor.tick()`, then `FeeSweeper.tick()` (Task 16), then the ERC-8183 settle step (Task 23, a no-op while disabled).

- [ ] **Step 1:** Write the tests.
  - `test_payout_exceeds_withdrawable`.
  - `test_concurrent_payouts_never_overdraw`: with a withdrawable of 1 USDC, two requests of 0.8 USDC go through `asyncio.gather` on separate sessions, and exactly one succeeds.
  - `test_payout_other_owner_404`.
  - `test_executor_submits_and_confirms`.
  - `test_executor_failure_restores_balance`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(billing): payouts with row locking + settler executor`.

### Task 16: Studio fee sweep

**Files:**
- Create: `app/data_plane/settler/fees.py`
- Modify: `app/core/config.py` (`FEE_SWEEP_MIN_ATOMIC=1_000_000`), README
- Test: `tests/data_plane/test_fee_sweep.py`

**Interfaces:**
- Produces: `FeeSweeper.tick()`.
  - Per agent, it sums STUDIO_FEE rows with `tx_hash IS NULL`.
  - If the sum is at least `FEE_SWEEP_MIN_ATOMIC` and `STUDIO_TREASURY_ADDRESS` is set, it transfers that sum from the agent wallet to the treasury and stamps those rows with the sweep `tx_hash`.
  - It skips the agent and logs a warning when the agent wallet's AVAX balance is below the estimated gas.

- [ ] **Step 1:** Write the tests: `test_sweeps_above_threshold`, `test_below_threshold_noop`, `test_no_treasury_noop`, `test_low_avax_skips`, `test_rows_stamped_once` (a second tick does not transfer again).
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(settler): batched studio fee sweep to treasury`.

---

## Phase 8: Frontend

Frontend tasks run from `apps/frontend`. "Run tests" means `pnpm test -- --run <path>`.

### Task 17: Test harness and generated API types

**Files:**
- Modify: `package.json` (devDeps: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, `jsdom`, `msw`, `openapi-typescript`; scripts `test`, `gen:api`), `vite.config.ts` (`test: {environment: "jsdom", setupFiles: "./src/test/setup.ts"}`)
- Create: `src/test/setup.ts`, `src/test/server.ts` (msw), `src/test/render.tsx` (QueryClient + MemoryRouter wrapper), `src/lib/api-schema.d.ts` (generated)
- Modify: `src/lib/types.ts` (re-export from `components["schemas"]`)
- Test: `src/lib/format.test.ts`, `src/components/query-state.test.tsx`

**Interfaces:**
- Produces:
  - `pnpm gen:api` runs `openapi-typescript http://localhost:8000/openapi.json -o src/lib/api-schema.d.ts`. The generated file is committed.
  - `renderWithProviders(ui, {route?: string}) -> RenderResult`.
  - The msw `server`, which tests extend with `server.use(...)`.

- [ ] **Step 1:** Write the tests.
  - `formatAtomic(1_500_000) === "1.5"`, `formatAtomic(0) === "0"`, `formatAtomic(2n ** 70n)` keeps full precision, and `shortAddress(null) === "—"`.
  - QueryState renders "Chưa implement" on 501, the error text on 500, and its children on success.
- [ ] **Step 2:** Run `pnpm test -- --run`. Expected: FAIL (vitest missing).
- [ ] **Step 3:** Install and configure. Generate the types and point `types.ts` at them, keeping the same exported names so pages compile unchanged.
- [ ] **Step 4:** Run `pnpm test -- --run && pnpm build && pnpm lint`. Expected: PASS.
- [ ] **Step 5:** Commit: `chore(web): vitest + msw harness, OpenAPI-generated types`.

### Task 18: Wallet connect and SIWE login

**Files:**
- Modify: `package.json` (`wagmi`, `viem`), `src/main.tsx`, `src/lib/api.ts`, `src/components/layout/app-shell.tsx`
- Create: `src/lib/wagmi.ts`, `src/hooks/use-auth.ts`, `src/components/connect-button.tsx`, `src/components/require-auth.tsx`
- Test: `src/hooks/use-auth.test.tsx`, `src/lib/api.test.ts`

**Interfaces:**
- Consumes: `/auth/nonce`, `/auth/verify` and `/auth/me` (Task 2).
- Produces:
  - `wagmiConfig` with chains `[avalancheFuji, avalanche]` from `viem/chains` and the `injected()` connector (Core / MetaMask).
  - `useAuth() -> {address, token, login(): Promise<void>, logout(): void, status: "anon" | "signing" | "authed"}`. The token lives in `localStorage` under the key `avaxagent.token`, with every access wrapped in try/catch.
  - `api` sends `Authorization: Bearer` when a token exists. On 401 it clears the token and dispatches `window` event `auth:expired`.
  - `<RequireAuth>` wraps every route except `/marketplace` and shows `<ConnectButton>` when the user is signed out.

- [ ] **Step 1:** Write the tests. Mock the wagmi `signMessage`.
  - `test login stores token and sends bearer`.
  - `test 401 clears token`.
  - `test marketplace accessible anonymously`.
  - `test SIWE message has domain, chainId 43113, nonce`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Build the SIWE message string manually in EIP-4361 format with `domain = window.location.host`.
- [ ] **Step 4:** Run tests, build and lint. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(web): wallet connect + SIWE login`.

### Task 19: Agent creation wizard

**Files:**
- Modify: `src/pages/agents/new.tsx`, `src/lib/api.ts`
- Create: `src/pages/agents/wizard-steps.tsx`, `src/components/ui/progress.tsx` (shadcn)
- Test: `src/pages/agents/new.test.tsx`

**Interfaces:**
- Consumes: `POST /agents` (Task 3), `POST /agents/{id}/wallet` (Task 7), `POST/GET /agents/{id}/registration` (Task 8).
- Produces: a three-step wizard with an internal state machine `"config" → "wallet" → "register" → "done"`. Step 3 polls `GET /registration` every 3 s until the state is `registered` or `failed`. When done it navigates to `/agents/{id}`. A 409 `slug_taken` shows an inline error on the slug field.

- [ ] **Step 1:** Write the tests with msw.
  - `test full happy path reaches done`.
  - `test slug_taken shows field error`.
  - `test registration failed shows retry`.
  - `test price converts to atomic`: entering `0.25` posts `price_atomic: 250000`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Convert the price with a string-based decimal parser, not `Number`, to avoid float drift: add `parseAtomic(input: string, decimals = 6): bigint` to `src/lib/format.ts` and test it in `format.test.ts` (`"0.1" → 100000n`, `"1.0000001"` throws).
- [ ] **Step 4:** Run tests, build and lint. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(web): 3-step agent creation wizard`.

### Task 20: Agent detail actions and marketplace

**Files:**
- Modify: `src/pages/agents/detail.tsx`, `src/pages/marketplace.tsx`, `src/lib/api.ts`
- Create: `src/components/policy-form.tsx`, `src/components/agent-card-dialog.tsx`, `src/components/ui/dialog.tsx` (shadcn, adds `@radix-ui/react-dialog`)
- Test: `src/pages/agents/detail.test.tsx`, `src/pages/marketplace.test.tsx`

**Interfaces:**
- Consumes: `PATCH /agents/{id}`, `PUT /agents/{id}/wallet/policy`, `GET /agents/{id}/wallet/balances`, `GET /marketplace/agents?q=`, and the gateway agent card.
- Produces:
  - The detail page gets an editable config form, a policy form (USDC inputs through `parseAtomic`), and a balances card showing AVAX with 18 decimals and USDC with 6, with a "low gas" badge when AVAX < 0.01.
  - The marketplace search is debounced by 300 ms, and the "View card" dialog shows the agent card JSON plus copyable `curl` examples for a paid call.

- [ ] **Step 1:** Write the tests: `test edit saves patch`, `test policy saves atomic values`, `test low gas badge`, `test search debounced single request`, `test card dialog shows a2a url`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run tests, build and lint. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(web): agent detail actions + marketplace search/card`.

### Task 21: Withdrawals and the job timeline

**Files:**
- Modify: `src/pages/wallet.tsx`, `src/pages/jobs.tsx`, `src/router.tsx`
- Create: `src/pages/job-detail.tsx`, `src/components/withdraw-form.tsx`
- Test: `src/pages/wallet.test.tsx`, `src/pages/job-detail.test.tsx`

**Interfaces:**
- Consumes: `POST/GET /billing/payouts` (Task 15), `GET /jobs/{id}` and `/jobs/{id}/events` (Task 4).
- Produces:
  - The withdraw form has an agent select, a destination input (`^0x[0-9a-fA-F]{40}$`) and an amount with a "Max" button that fills the withdrawable amount. A 422 `insufficient_balance` shows the server's withdrawable value. The payout list links each tx to `{explorer_url}/tx/{hash}`.
  - New route `/jobs/:id` shows the job with its event timeline and polls every 2 s while the status is in `funded|running|submitted`. Rows in the job list link to it.

- [ ] **Step 1:** Write the tests: `test max fills withdrawable`, `test invalid address blocked`, `test 422 shows withdrawable`, `test timeline polls until settled`, `test explorer link uses network explorer_url`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run tests, build and lint. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(web): withdrawals + job timeline`.

---

## Phase 9: ERC-8183 escrow (gated)

### Task 22: Deploy the ERC-8183 stack to Fuji

**Files:**
- Create: `contracts/foundry.toml`, `contracts/src/` (upstream AgenticCommerce, EvaluatorRouter, OptimisticPolicy, pinned to the commit whose ABIs match `apps/backend/app/chain/abis/`), `contracts/script/Deploy.s.sol`, `contracts/test/Smoke.t.sol`
- Modify: `contracts/README.md`, root `Makefile` (`contracts-test`, `contracts-deploy-fuji`)

**Interfaces:**
- Produces:
  - `forge script script/Deploy.s.sol --rpc-url fuji --broadcast --verify` prints `COMMERCE_ADDRESS`, `ROUTER_ADDRESS`, `POLICY_ADDRESS` and the deploy block.
  - The payment token is set to Fuji USDC. Any MegaFuel/paymaster hooks are removed.

- [ ] **Step 1:** Write `Smoke.t.sol`: the create → fund → submit → settle happy path on a local fork of Fuji (`vm.createSelectFork`), with USDC dealt via `deal`.
- [ ] **Step 2:** Run `forge test`. Expected: FAIL (contracts are not imported yet).
- [ ] **Step 3:** Import the sources and write the deploy script.
- [ ] **Step 4:** Run `forge test`. Expected: PASS. Then diff `forge inspect <C> abi` against the vendored ABIs. Expected: identical, otherwise refresh the vendored ABIs.
- [ ] **Step 5:** Deploy to Fuji, verify on Snowtrace, and record the addresses in `contracts/README.md`.
- [ ] **Step 6:** Commit: `feat(contracts): ERC-8183 stack + Fuji deployment`.

### Task 23: Escrow flow in the backend

**Files:**
- Modify: `app/chain/commerce.py`, `app/data_plane/indexer/streams.py` (`erc8183.jobs`), `app/data_plane/workers/tasks.py`, `app/data_plane/settler/service.py`, `app/data_plane/gateway/a2a.py`
- Test: `tests/chain/test_commerce.py`, `tests/data_plane/test_erc8183_flow.py`

**Interfaces:**
- Consumes: `contracts()` (raises `FeatureDisabled` when unset), `agent_signer`, `add_event`, `record_income`.
- Produces:
  - `CommerceClient.get_job`, `submit_result(job_id, deliverable_uri, deliverable_hash) -> tx` and `settle(job_id) -> tx` are implemented with web3 contract calls, signed by `agent_signer` (submit) or the relayer (settle).
  - Stream `erc8183.jobs`: `JobFunded` where the provider ∈ managed wallets inserts `Job(settlement_mode=erc8183, chain_job_id, status=funded)` and enqueues `RUN_JOB`. It is idempotent on `(chain_id, chain_job_id)`, which needs a migration adding that unique constraint.
  - `run_job`: for erc8183 it calls `submit_result` after storage and stops at `submitted`.
  - The settler calls `settle` for `submitted` erc8183 jobs once the policy window has passed, sets `settled`, and calls `record_income` with the settle `tx_hash`.
  - The gateway, for erc8183 agents, answers `message/send` with the escrow parameters (`commerce`, `provider`, `price`, `token`) instead of a 402.

- [ ] **Step 1:** Write the tests: `test_disabled_raises_409` (the commerce env vars are unset), `test_jobfunded_creates_job_once`, `test_worker_submits_for_erc8183`, `test_settler_settles_and_books_income`, `test_gateway_returns_escrow_params`. Mock the web3 contract objects.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement, plus the Alembic migration `0002_erc8183_job_unique`.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: PASS, with the full x402 suite still green.
- [ ] **Step 5:** Commit: `feat(erc8183): escrow jobs via indexer, worker submit, settler settle`.

---

## Phase 10: Ops

### Task 24: CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces three jobs on `push` and `pull_request`:
  - `backend`: service `postgres:16` and `redis:7`, `uv sync --all-packages --all-extras`, `uv run ruff check apps/backend`, `cd apps/backend && uv run alembic upgrade head && uv run alembic check && uv run pytest -m "not fuji"`.
  - `sdk`: `cd packages/avaxagent-sdk && uv run pytest -q`.
  - `frontend`: pnpm 10 / Node 20, `pnpm install --frozen-lockfile`, `pnpm lint:web`, `pnpm --filter @avaxagent-studio/frontend test -- --run`, `pnpm build:web`.

- [ ] **Step 1:** Write the workflow.
- [ ] **Step 2:** Validate locally with `act -j backend` if available. Otherwise push a branch and check that all three jobs are green.
- [ ] **Step 3:** Commit: `ci: backend, sdk, frontend pipelines`.

### Task 25: Production hardening and mainnet checklist

**Files:**
- Create: `app/core/logging.py`, `app/data_plane/gateway/ratelimit.py`, `docs/MAINNET.md`
- Modify: `app/main.py`, `app/data_plane/gateway/main.py`, `app/core/config.py` (startup validation)
- Test: `tests/test_hardening.py`

**Interfaces:**
- Produces:
  - JSON logs with `request_id` (middleware sets the `X-Request-ID` header).
  - Gateway rate limit, per IP and per slug, using a Redis sliding window: 60 requests per minute per IP on `/a2a`, otherwise 429.
  - `Settings.validate_for_production()`, called at startup when `environment == "production"`. It fails fast if `AUTH_JWT_SECRET` is the dev default, `TURNKEY_*`/`RELAYER_*`/`STUDIO_TREASURY_ADDRESS` are unset, `CORS_ORIGINS` contains `localhost`, or `network == "avalanche-mainnet"` while `INDEXER_START_BLOCK == 0`.
  - `docs/MAINNET.md`: a checklist of relayer AVAX float, treasury multisig, Turnkey policy review, RPC provider with archive and getLogs limits, a backup/restore drill, and a fee-sweep threshold.

- [ ] **Step 1:** Write the tests: `test_request_id_header_echoed`, `test_gateway_rate_limited_429`, `test_production_rejects_dev_secret`, `test_production_rejects_localhost_cors`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `uv run pytest -m "not fuji" -v`. Expected: PASS.
- [ ] **Step 5:** Commit: `feat(ops): structured logs, gateway rate limit, production config guard`.

---

## Definition of done (whole plan)

- `make test`, `make lint` and `pnpm build:web` pass, and CI is green.
- On Fuji, end to end: log in with a wallet, create an agent, provision its wallet, register it on ERC-8004 (verify the id on 8004scan or Snowtrace), make a paid x402 call with `examples/x402/buyer_demo.py` pointed at the gateway, see the job reach `settled` in the job log, see earnings net of the 5% fee, withdraw to an external address, and see the fee swept to the treasury.
- No endpoint in Phases 0–8 still returns 501. ERC-8183 endpoints return 409 until Task 22's addresses are set.
