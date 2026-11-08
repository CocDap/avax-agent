# Test Suite

Unit tests for the AvaxAgent SDK (Avalanche C-Chain fork). They run on `pytest` with `unittest.mock` and need no live blockchain connection. Chain fixtures use Fuji (43113) and mainnet (43114).

## Running Tests

```bash
uv sync --extra dev
uv run pytest                              # whole suite
uv run pytest tests/test_asset_catalog.py  # one file
uv run pytest -v
```

## Representative Test Files

| File | Module Under Test |
| --- | --- |
| `test_sdk.py` | `ERC8004Agent`: registration, discovery, URI parsing, metadata, chain-ID pinning |
| `test_erc8004_contract.py` | `ContractInterface`: preflight, revert detection, retries, `built_with` tag |
| `test_agent_uri.py` / `test_models.py` | Agent URI generation, `AgentEndpoint` validation |
| `test_resolve_network.py` | `avalanche-fuji` / `avalanche-mainnet` presets, `RPC_URL_<NETWORK>` precedence |
| `test_networks_addresses.py` | Registry, USDC and Multicall3 addresses; EIP-712 constants |
| `test_asset_catalog.py` | Avalanche USDC/EURC catalog: snapshot, aliases, constructor invariants, amounts |
| `test_signing_policy.py` / `test_wallet_policy_gating.py` | `SigningPolicy` allowlist (4 Circle domains), Permit denylist, validity windows |
| `test_x402_signer.py` | `X402Signer`: expected-route binding, recipient/amount guards, session budget |
| `test_local_executor.py` / `test_broadcast_idempotence.py` | `LocalExecutor` self-pay path (AVAX gas, `eth_gasPrice × 1.2`) |
| `test_tx_config.py` / `test_contract_mixin.py` | Gas-price floor (1 wei on C-Chain), receipt timeouts |
| `test_wallet.py` | `EVMWalletProvider`: keystore encryption, signing |
| `test_turnkey_provider.py` / `test_turnkey_client.py` | `TurnkeyWalletProvider` against an in-process fake enclave |
| `test_wallet_conformance.py` / `test_wallet_factory.py` | Capability declarations; `evm`/`turnkey`/`mpc` factory (`twak` is rejected) |
| `test_nonce_manager.py` / `test_multicall.py` / `test_rpc_errors.py` | Core helpers |
| `test_local_storage.py` / `test_ipfs_storage.py` / `test_storage_from_env.py` | Storage providers |

The upstream ERC-8183, paymaster, TWAK and b402 test files are not ported, because those modules do not exist in this fork.
