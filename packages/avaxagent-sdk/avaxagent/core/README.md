# Core

## Overview

The `core` module contains the internal infrastructure shared across all avaxagent protocol packages. It provides nonce management, a reusable contract transaction mixin, gas-price / receipt-timeout tuning, Multicall3 reads, and ABI loading utilities. (The upstream MegaFuel paymaster client is not ported: MegaFuel does not serve Avalanche.)

Exception types are defined in the top-level `avaxagent.exceptions` module and re-exported from `avaxagent.core` for convenience.

## Key Concepts

- **NonceManager** -- thread-safe singleton that seeds from the chain on first use (`pending` block), then increments locally. Re-syncs after a `nonce too low` rejection. Ambiguous responses such as `already known` require tracking the original transaction hash instead of signing again. Keyed by `(rpc_url, account)` so multiple clients sharing a wallet share one manager.
- **Gas-price floor** -- writes pay `max(eth_gasPrice × 1.2, floor)`. The per-chain floor is 1 wei on Avalanche C-Chain (43113 / 43114) and 0.1 gwei on unknown chains; override with `set_min_gas_price_wei()` or `AVAXAGENT_MIN_GAS_PRICE_WEI`.
- **ContractClientMixin** -- mixin class that encapsulates build-sign-send logic with automatic nonce management and exponential-backoff retry on rate-limit and nonce errors. Prefers `WalletProvider.sign_transaction()` when available, falls back to raw `private_key` signing. Used by `MinimalERC20Client`.

## API Reference

### `NonceManager`

| Method | Description |
| --- | --- |
| `NonceManager.for_account(w3, account)` | Get or create a singleton for this wallet + RPC. |
| `get_nonce()` | Return the next nonce (thread-safe). |
| `handle_error(error, used_nonce)` | Re-sync after a `nonce too low` rejection; returns `True` to retry. Returns `False` for `already known` or `replacement transaction underpriced`. |
| `reset()` | Force re-seed on next `get_nonce()` call. |

### `ContractClientMixin`

Mixin for web3 contract clients. Subclasses set `self.w3`, `self._wallet_provider`, and `self._account`. A `None` wallet provider yields a read-only client (writes raise `RuntimeError`).

Signing flows exclusively through `wallet_provider.sign_transaction()` - raw private keys are never accepted at this layer.

| Method | Description |
| --- | --- |
| `_send_tx(fn, value=0, gas=2_000_000, skip_preflight=False)` | Build, sign, and send a write transaction with retry. Includes pre-flight `eth_call` simulation (surfaces revert reasons before spending gas), dynamic gas price with 20% buffer, and on-chain revert detection (`receipt.status == 0`). Pass `skip_preflight=True` when the node returns opaque `0x` reverts. |
| `_call_with_retry(fn)` | Execute a read-only contract call with rate-limit retry. |

## Transaction Retry Strategy

`ContractClientMixin._send_tx()` uses the following retry policy:

| Constant | Default | Description |
| --- | --- | --- |
| `MAX_RETRIES` | `5` | Maximum send attempts per transaction. |
| `RETRY_BASE_DELAY` | `1.0` s | Base delay for exponential backoff on rate limits. |

Nonce errors trigger an immediate re-sync from the chain and retry. Rate limits (`429` / `"too many requests"`) use exponential backoff (`base * 2^attempt`). All other errors are raised immediately.

## Related

- [`erc8004`](../erc8004/README.md) -- ERC-8004 package, writes through `LocalExecutor` + `NonceManager`.
- [`erc20`](../erc20/) -- `MinimalERC20Client`, built on `ContractClientMixin`.
- [`wallets`](../wallets/README.md) -- `ContractClientMixin` delegates signing to `WalletProvider`.
- [`storage`](../storage/README.md) -- off-chain storage used alongside core infra.
