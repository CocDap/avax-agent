# AvaxAgent SDK

[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](../LICENSE)

Python SDK for building on-chain AI agents on **Avalanche C-Chain**: register agent identities (ERC-8004), manage wallets, and sign x402 payments in Circle USDC / EURC (EIP-3009), all behind a policy-gated signer.

`avaxagent` is a fork of the BNB Chain [`bnbagent`](../python/) Python SDK. It keeps every module that works on Avalanche and drops the ones that depend on BNB-Chain-only infrastructure (see [What was not ported](#what-was-not-ported)).

| Capability | Status on Avalanche |
| --- | --- |
| **ERC-8004 Identity Registry**: register an agent, set its URI and metadata, discover agents through 8004scan | ✅ Fuji and mainnet (same vanity CREATE2 registry addresses as other chains) |
| **x402 `exact` payments**: EIP-3009 `TransferWithAuthorization` through `X402Signer` | ✅ Circle USDC and EURC on Fuji and mainnet |
| **`SigningPolicy`**: deny-by-default EIP-712 gate (Permit and Permit2 are always refused) | ✅ allowlist built from the Avalanche asset catalog |
| **Wallets**: `EVMWalletProvider` (Keystore V3) and `TurnkeyWalletProvider` (remote enclave) | ✅ |
| **Storage**: Local and IPFS (pinning service) | ✅ chain-agnostic |
| **Multicall3, nonce manager, RPC error classifier, receipt timeouts** | ✅ |

> ⚠️ Experimental fork, version 0.1.0. Gas is always self-paid in AVAX, because Avalanche has no paymaster.

## Installation

From this folder:

```bash
uv sync                       # or: pip install -e .
pip install -e ".[ipfs]"      # optional IPFS storage backend
pip install -e ".[turnkey]"   # optional Turnkey remote signer
```

## Table of Contents

- [What was not ported](#what-was-not-ported)
- [Network & Contracts](#network--contracts)
- [Quick Start: Register an Agent (ERC-8004)](#quick-start-register-an-agent-erc-8004)
- [Quick Start: Pay with x402 (USDC on Avalanche)](#quick-start-pay-with-x402-usdc-on-avalanche)
- [Configuration Reference](#configuration-reference)
- [Architecture & Components](#architecture--components)
- [Gas pricing on Avalanche](#gas-pricing-on-avalanche)
- [Examples](#examples)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## What was not ported

These upstream modules depend on contracts, services or tokens that do not exist on Avalanche C-Chain, so the fork leaves them out:

| Upstream feature | Why it was skipped |
| --- | --- |
| **ERC-8183 agentic commerce** (`erc8183/`: AgenticCommerce kernel, EvaluatorRouter, OptimisticPolicy, negotiation, job ops, voter and agent-server examples) | The kernel, router and policy contracts are only deployed on BSC. |
| **MegaFuel paymaster** (`core/paymaster.py`, `relay_verifier.py`, sponsored sends) | MegaFuel is a NodeReal service for BSC and opBNB only. |
| **TWAK wallet** (`TWAKProvider`, `TwakX402Payer`, `WALLET_KIND=twak`) | The Trust Wallet Agent Kit CLI only supports `bsc` and `bsctestnet`. |
| **U, USD1, Binance-peg USDC/USDT assets; b402 Permit2 routes** | These are BSC token deployments and facilitator routes. Avalanche uses Circle-native USDC and EURC (EIP-3009, FiatTokenV2). |

Anything that would need these modules raises `ValueError("Unknown wallet kind ...")`, `ValueError("Unknown network ...")` or `KeyError(... not registered)`. Nothing falls back silently.

---

## Network & Contracts

| | Avalanche Fuji (default) | Avalanche mainnet |
| --- | --- | --- |
| Network name | `avalanche-fuji` | `avalanche-mainnet` |
| Chain ID | `43113` | `43114` |
| Public RPC | `https://api.avax-test.network/ext/bc/C/rpc` | `https://api.avax.network/ext/bc/C/rpc` |
| Explorer | <https://testnet.snowtrace.io> | <https://snowtrace.io> |
| ERC-8004 Identity Registry | [`0x8004A818BFB912233c491871b3d84c89A494BD9e`](https://testnet.snowtrace.io/address/0x8004A818BFB912233c491871b3d84c89A494BD9e) | [`0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`](https://snowtrace.io/address/0x8004A169FB4a3325136EB29fA0ceB6D2e539a432) |
| USDC (default x402 asset) | `0x5425890298aed601595a70AB815c96711a31Bc65` | `0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E` |
| EURC | `0x5E44db7996c682E92a960b65AC713a54AD815c6B` | `0xC891EB4cbdEFf6e073e859e987815Ed1505c2ACD` |
| Multicall3 | `0xcA11bde05977b3631167028862bE2a173976CA11` | `0xcA11bde05977b3631167028862bE2a173976CA11` |

All payment assets use 6 decimals and EIP-712 version `"2"`. USDC's domain name is `"USD Coin"` on both chains. EURC's is `"Euro Coin"` on mainnet and `"EUR Coin"` on Fuji. Each domain was checked against the on-chain `DOMAIN_SEPARATOR()`.

In code:

```python
from avaxagent.networks import get_address, list_assets, AVALANCHE_FUJI_CHAIN_ID

get_address(AVALANCHE_FUJI_CHAIN_ID).identity_registry
[a.symbol for a in list_assets(AVALANCHE_FUJI_CHAIN_ID)]   # ['USDC', 'EURC']
```

Fuji AVAX for gas: <https://core.app/tools/testnet-faucet>. Fuji USDC and EURC: <https://faucet.circle.com>.

---

## Quick Start: Register an Agent (ERC-8004)

[ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) gives each agent an ERC-721 identity token (`agentId`), a discoverable profile URI and on-chain key-value metadata. Registration is a normal transaction paid in AVAX, and a Fuji registration costs a fraction of a cent.

```python
import os
from dotenv import load_dotenv
from avaxagent import ERC8004Agent, AgentEndpoint, EVMWalletProvider

load_dotenv()

wallet = EVMWalletProvider(
    password=os.environ["WALLET_PASSWORD"],
    private_key=os.getenv("PRIVATE_KEY"),  # only needed on first run
)

sdk = ERC8004Agent(network="avalanche-fuji", wallet_provider=wallet)

agent_uri = sdk.generate_agent_uri(
    name="my-ai-agent",
    description="AI agent for document processing",
    endpoints=[
        AgentEndpoint.a2a("https://my-agent.example.com"),
        AgentEndpoint.mcp("https://my-agent.example.com/mcp", version="2025-06-18"),
    ],
)

result = sdk.register_agent(agent_uri=agent_uri)
print(f"Agent ID: {result['agentId']}  tx: https://testnet.snowtrace.io/tx/{result['transactionHash']}")
```

Read-only calls need a wallet object but no funds:

```python
sdk.get_agent_info(1)                 # owner + agentURI from the registry
sdk.get_all_agents(limit=10)          # 8004scan indexer (chain_id=43113)
```

`ERC8004Agent` refuses to start if the RPC reports a different chain ID than the selected network.

A complete script is in [`examples/erc8004_register.py`](examples/erc8004_register.py).

---

## Quick Start: Pay with x402 (USDC on Avalanche)

```python
from avaxagent import EVMWalletProvider, X402Signer
from avaxagent.networks import AssetId
from avaxagent.x402 import resolve_expected_eip3009_route

ROUTE = resolve_expected_eip3009_route("eip155:43113", AssetId.FUJI_USDC)
USDC = ROUTE.address

wallet = EVMWalletProvider(password=os.environ["WALLET_PASSWORD"])
signer = X402Signer(
    wallet,
    max_value_per_call={USDC: 1_000_000},   # 1 USDC (6 decimals)
    session_budget={USDC: 50_000_000},      # 50 USDC per session
)

signed = signer.sign_payment(
    domain=challenge_domain,
    types=challenge_types,
    message=challenge_message,
    expected_route=ROUTE,        # your own record of chain/token/method/domain
    expected_to=MY_KNOWN_PAYEE,  # never taken from the 402 body
)
```

Canonical asset IDs are `USDC` and `EURC` on mainnet (43114) and `FUJI_USDC` and `FUJI_EURC` on Fuji (43113). For UI input such as "USDC", resolve the symbol with network context: `resolve_asset_alias(43113, "USDC") -> AssetId.FUJI_USDC`. CAIP-2 networks are `eip155:43114` and `eip155:43113`.

A runnable loop against a mock 402 server is in [`examples/x402/buyer_demo.py`](examples/x402/buyer_demo.py).

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `PRIVATE_KEY` | Recommended | Auto-generate | Wallet private key. Encrypted to `~/.avaxagent/wallets/` on first run; you can remove it afterwards. |
| `WALLET_PASSWORD` | Yes (evm) | - | Keystore encryption password. |
| `WALLET_ADDRESS` | No | Auto-select | Picks a keystore when several exist. |
| `WALLET_KIND` | No | `evm` | `evm` or `turnkey` (`mpc` is a stub). |
| `TURNKEY_ORG_ID`, `TURNKEY_SIGN_WITH`, `TURNKEY_API_PUBLIC_KEY`, `TURNKEY_API_PRIVATE_KEY` | If `turnkey` | - | Turnkey remote-signer credentials. `TURNKEY_API_BASE_URL` is optional. |
| `RPC_URL` | No | Preset | Global RPC override. |
| `RPC_URL_AVALANCHE_FUJI` / `RPC_URL_AVALANCHE_MAINNET` | No | - | Per-network RPC override. Takes priority over `RPC_URL`. |
| `ERC8004_REGISTRY_ADDRESS` | No | Preset | Identity Registry override, for example on a custom Avalanche L1. |
| `AVAXAGENT_MIN_GAS_PRICE_WEI` | No | Per-chain (1 wei on C-Chain) | Global gas-price floor in wei. |
| `AVAXAGENT_RECEIPT_TIMEOUT` | No | `300` | Receipt wait in seconds. |
| `STORAGE_API_KEY` | If IPFS | - | Pinning-service JWT. |
| `STORAGE_API_URL` / `STORAGE_GATEWAY_URL` | No | Pinata | Pinning API and gateway. |
| `STORAGE_LOCAL_PATH` | No | `.agent-data` | Local storage directory. |

Minimal dotenv template:

```dotenv
WALLET_KIND=evm                     # evm | turnkey
WALLET_PASSWORD=change-me
PRIVATE_KEY=                        # first run only, then remove
# RPC_URL_AVALANCHE_FUJI=https://api.avax-test.network/ext/bc/C/rpc
# TURNKEY_ORG_ID= / TURNKEY_SIGN_WITH= / TURNKEY_API_PUBLIC_KEY= / TURNKEY_API_PRIVATE_KEY=
# STORAGE_API_KEY=                  # IPFS pinning (pip install "avaxagent[ipfs]")
```

### Custom networks (Avalanche L1s)

Pass a `NetworkConfig` to `ERC8004Agent` instead of a preset name:

```python
from avaxagent import NetworkConfig
my_l1 = NetworkConfig(
    name="my-l1", chain_id=12345, rpc_url="https://my-l1.example/rpc",
    registry_contract="0x...",
)
sdk = ERC8004Agent(network=my_l1, wallet_provider=wallet)
```

`create_web3()` injects the POA extra-data middleware defensively. C-Chain headers do not need it, but some custom L1s do.

---

## Architecture & Components

```
avaxagent/
├── config.py           NetworkConfig + avalanche-fuji / avalanche-mainnet presets
├── networks/           addresses (registry, USDC, Multicall3) + payment-asset catalog
├── erc8004/            ERC8004Agent, ContractInterface, AgentEndpoint
├── wallets/            WalletProvider ABC, EVM, Turnkey, MPC stub, LocalExecutor
├── signing/            SigningPolicy (EIP-712 gate)
├── x402/               X402Signer, expected-route resolution, session budget
├── erc20/              MinimalERC20Client
├── storage/            Local + IPFS StorageProvider
└── core/               web3 factory, nonce manager, multicall, gas/receipt tuning
```

Every write goes through `wallet.make_executor(ExecutionContext(web3))`, which returns a `LocalExecutor`. The executor builds a legacy `gasPrice` transaction, runs an `eth_call` preflight, signs with the wallet, broadcasts and waits for the receipt. A preflight revert is raised before anything is broadcast.

**Wallet providers**

- `EVMWalletProvider`: Keystore V3 (scrypt + AES-128-CTR, MetaMask/Geth compatible). Persistent mode stores the key in `~/.avaxagent/wallets/`; in-memory mode uses `persist=False`. Keystore files are `0600`. The password is not retained, and `destroy()` wipes the key.
- `TurnkeyWalletProvider`: signs in Turnkey's enclave, and the SDK never holds the key. See [`avaxagent/wallets/README.md`](avaxagent/wallets/README.md).
- Subclass `WalletProvider` for HSM, KMS or multisig backends. Capabilities (`sign.message`, `sign.transaction`, `sign.typed_data`, `calls.arbitrary`) are derived from which methods the subclass overrides.

**Storage providers**: `LocalStorageProvider` (JSON files under `STORAGE_LOCAL_PATH`) and `IPFSStorageProvider` (Pinata-compatible pinning that returns `ipfs://CID` URIs). Use them to host agent registration files.

---

## Gas pricing on Avalanche

C-Chain uses a dynamic base fee that can fall far below BSC's fixed 0.05–1 gwei. The fork sets the per-chain floor to **1 wei** on both 43113 and 43114, so the SDK pays `eth_gasPrice × 1.2` and does not overpay against a BSC-style floor. Unknown chains keep the conservative 0.1 gwei floor. To override:

```python
from avaxagent import set_min_gas_price_wei
set_min_gas_price_wei(2_000_000_000)   # or AVAXAGENT_MIN_GAS_PRICE_WEI=2000000000
```

---

## Examples

| Example | Description |
| --- | --- |
| [`examples/erc8004_register.py`](examples/erc8004_register.py) | By default, looks up an agent and lists agents from 8004scan without spending anything. With `--register`, mints a new identity (one AVAX-paid transaction). |
| [`examples/x402/buyer_demo.py`](examples/x402/buyer_demo.py) | Buyer loop (GET → 402 → EIP-3009 sign → retry) against a mock server, using Fuji USDC. |
| [`examples/security/e2e.py`](examples/security/e2e.py) | Six off-chain assertions on the SigningPolicy and X402Signer defense matrix. |
| [`examples/turnkey_e2e.py`](examples/turnkey_e2e.py) | Opt-in live Turnkey run on Fuji (EIP-191, EIP-712, legacy tx, EIP-1559 tx). |

---

## Security

### Wallet & key handling

- `EVMWalletProvider` encrypts the key with Keystore V3 and does not keep the password. The live key is still in process memory, so call `destroy()` when you finish. For high-value deployments, use Turnkey, an HSM or MPC.
- Chain-ID pinning: `ERC8004Agent` and `TurnkeyWalletProvider.from_env(expected_chain_id=...)` refuse to run on a mismatched RPC.
- Storage files are written `0600` and directories `0700`.

### EIP-712 typed-data signing (`SigningPolicy`)

`EVMWalletProvider.sign_typed_data` is **policy-gated by default**. With no configuration, it signs only EIP-3009 `TransferWithAuthorization` and `ReceiveWithAuthorization` against the catalog's Circle USDC and EURC contracts on Avalanche. ERC-2612 `Permit` and Permit2 `PermitSingle` / `PermitBatch` are always denied, and the denylist wins over any allowlist entry.

The threat: Circle USDC supports ERC-2612 `Permit` on-chain. A malicious 402 server could talk an LLM agent into signing a Permit that grants an unbounded allowance. The default policy refuses this unconditionally.

```python
print(EVMWalletProvider(password=...).signing_policy)
# SigningPolicy(
#   domain_allowlist (4 entries):
#     - chain_id=43113 verifyingContract=0x5425890298aed601595a70AB815c96711a31Bc65
#     - chain_id=43113 verifyingContract=0x5E44db7996c682E92a960b65AC713a54AD815c6B
#     - chain_id=43114 verifyingContract=0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E
#     - chain_id=43114 verifyingContract=0xC891EB4cbdEFf6e073e859e987815Ed1505c2ACD
#   primary_type_allowlist=['ReceiveWithAuthorization', 'TransferWithAuthorization']
#   primary_type_denylist=['Permit', 'PermitBatch', 'PermitSingle']
#   validity: window<=600s, future<=900s, required_for=[...]
#   allow_unknown_domain=False
# )
```

`X402Signer` re-resolves `expected_route` through the catalog. Before it reserves budget or signs, it checks the chain, verifying contract, primary type and EIP-712 name/version. It also requires `message['to'] == expected_to`, requires `message['from'] == wallet.address`, and enforces the per-call cap and the session budget. Take `expected_route` and `expected_to` from your own configuration, never from the 402 response.

**Extending the policy:**

```python
from avaxagent import SigningPolicy
from avaxagent.networks import AVALANCHE_MAINNET_CHAIN_ID

extended = SigningPolicy.strict_default().extend(
    domain_allowlist={(AVALANCHE_MAINNET_CHAIN_ID, "0xMyCustomVerifyingContract")},
)
wallet = EVMWalletProvider(password=..., signing_policy=extended)
```

| Scenario | Extension snippet |
| --- | --- |
| Custom token on C-Chain | `extend(domain_allowlist={(43114, "0xMyToken")})` |
| Custom primary type "MyOrder" | `extend(domain_allowlist={(43114, X)}, primary_type_allowlist={"MyOrder"})` |
| Opt into Permit2 SignatureTransfer | `extend(primary_type_allowlist={"PermitTransferFrom"})` |
| Widen validity to 30 min | `extend(max_validity_window_seconds=1800)` |

Register tools with a scoped `X402Signer`, never with the raw `WalletProvider`. `SigningPolicy.permissive()` and `_DANGEROUS_sign_typed_data_no_policy()` exist for tests only; both log a warning and must not be reachable from agent code.

---

## Troubleshooting

| Error | Cause | Solution |
| --- | --- | --- |
| `Unknown network: bsc-testnet` | Network presets are Avalanche-only | Use `avalanche-fuji` or `avalanche-mainnet`, or pass a `NetworkConfig`. |
| `Unknown wallet kind 'twak'` | TWAK is not ported | Use `WALLET_KIND=evm` or `turnkey`. |
| `RPC chain_id mismatch` | `RPC_URL` points at another chain | Fix `RPC_URL` / `RPC_URL_AVALANCHE_FUJI`. |
| `AssetId USDC is not available on chain_id=43113` | Canonical IDs are per chain | Use `AssetId.FUJI_USDC` on Fuji, or `resolve_asset_alias(43113, "USDC")`. |
| `insufficient funds for gas` | The wallet has no AVAX | Fund it from the Fuji faucet. Avalanche has no paymaster. |
| `No PRIVATE_KEY and no keystore found` | Empty `~/.avaxagent/wallets/` | Set `PRIVATE_KEY` to import, or let the SDK generate a key. |
| `Multiple wallets found` | Several keystores exist | Set `WALLET_ADDRESS=0x...`. |

---

## License

MIT License. See [LICENSE](../LICENSE).
