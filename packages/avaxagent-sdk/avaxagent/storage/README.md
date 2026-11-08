# Storage Providers

## Overview

The `storage` module provides a pluggable off-chain storage interface for the avaxagent SDK. Typical uses on Avalanche: hosting ERC-8004 agent registration files (pass the returned `ipfs://` URL as the agent URI) and any off-chain payload whose hash you anchor on-chain. Implementations handle upload, download, and existence checks through a unified async API.

## Built-in providers

| Provider | Import | When to use |
| --- | --- | --- |
| `LocalStorageProvider` | `avaxagent.storage` | Development / local testing |
| `IPFSStorageProvider` | `avaxagent.storage` | Production (Pinata-compatible IPFS) |

Custom backends: subclass `StorageProvider` and pass the instance wherever your application needs storage.

## Quick Start

```python
# LocalStorageProvider - dev / local
from avaxagent.storage import LocalStorageProvider

storage = LocalStorageProvider("./my-data")
url = await storage.upload({"key": "value"})          # returns "file://..."
url = await storage.upload({"key": "value"}, "job-1.json")

# LocalStorageProvider from env (reads STORAGE_LOCAL_PATH, default ".agent-data")
storage = LocalStorageProvider.from_env()

# IPFSStorageProvider - production (Pinata)
from avaxagent.storage import IPFSStorageProvider

storage = IPFSStorageProvider(
    pinning_api_url="https://api.pinata.cloud/pinning/pinJSONToIPFS",
    pinning_api_key="your-pinata-jwt",
    gateway_url="https://gateway.pinata.cloud/ipfs/",
)
url = await storage.upload({"key": "value"})          # returns "ipfs://Qm..."

# IPFSStorageProvider from env (reads STORAGE_API_KEY / STORAGE_API_URL / STORAGE_GATEWAY_URL)
storage = IPFSStorageProvider.from_env()
```

## Loading from env

Each provider reads its own env vars via `from_env()`. The dispatch between providers happens in the caller (e.g. the startup script), not in the SDK:

```python
import os
from avaxagent.storage import LocalStorageProvider, IPFSStorageProvider

storage_type = (os.getenv("STORAGE_PROVIDER") or "local").lower()
if storage_type == "ipfs":
    storage = IPFSStorageProvider.from_env()
elif storage_type == "local":
    storage = LocalStorageProvider.from_env()
else:
    raise SystemExit(f"Unknown STORAGE_PROVIDER={storage_type!r}")
```

### `LocalStorageProvider` env vars

| Variable             | Default       | Description                          |
| -------------------- | ------------- | ------------------------------------ |
| `STORAGE_LOCAL_PATH` | `.agent-data` | Base directory for stored JSON files |

### `IPFSStorageProvider` env vars

| Variable | Default | Description |
| --- | --- | --- |
| `STORAGE_API_KEY` | - (required) | Pinata JWT or compatible pinning service API key |
| `STORAGE_API_URL` | `https://api.pinata.cloud/pinning/pinJSONToIPFS` | Pinning endpoint |
| `STORAGE_GATEWAY_URL` | `https://gateway.pinata.cloud/ipfs/` | IPFS HTTP gateway |

## API Reference

### `StorageProvider` (ABC)

Async abstract base class. Subclass this to build a custom backend.

| Method | Description |
| --- | --- |
| `async upload(data, filename=None)` | Upload JSON dict. Returns a URL (`file://`, `ipfs://`, `https://`…). Implementations must reject `filename` values that resolve outside the storage scope by raising `StorageError`. |
| `async download(url)` | Download and parse JSON from a URL. |
| `async exists(url)` | Check whether data at the URL exists. |
| `compute_hash(data)` (static) | `keccak256` of canonical JSON for on-chain verification. |
| `compute_content_hash(content)` (static) | `keccak256` of a raw string. |

### `upload_sync(provider, data, filename=None)`

Synchronous bridge for non-async callers. Runs `provider.upload()` via a new event loop.

```python
from avaxagent.storage import upload_sync, LocalStorageProvider

storage = LocalStorageProvider("./data")
url = upload_sync(storage, {"job": {"id": 1}}, "job-1.json")
```

## Custom storage providers

Just like the wallet module has `EVMWalletProvider` / `MPCWalletProvider` plus the option to inject any `WalletProvider` subclass, storage has `LocalStorageProvider` / `IPFSStorageProvider` plus arbitrary custom backends.

Subclass `StorageProvider` and implement the three async methods. The SDK doesn't care about the implementation - only that `upload()` returns a URL your consumers can fetch.

**Example - SQLite backend (30 lines):**

```python
import json
import aiosqlite
from avaxagent.storage import StorageProvider
from avaxagent.exceptions import StorageError

class SQLiteStorageProvider(StorageProvider):
    def __init__(self, db_path: str, public_base_url: str):
        self._db = db_path
        self._base = public_base_url  # e.g. "https://my-agent.example.com/deliverables"

    async def _ensure_table(self, conn):
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS deliverables (key TEXT PRIMARY KEY, data TEXT)"
        )

    async def upload(self, data: dict, filename: str | None = None) -> str:
        key = filename or self.compute_hash(data).hex() + ".json"
        async with aiosqlite.connect(self._db) as db:
            await self._ensure_table(db)
            await db.execute(
                "INSERT OR REPLACE INTO deliverables VALUES (?, ?)",
                (key, json.dumps(data)),
            )
            await db.commit()
        return f"{self._base}/{key}"

    async def download(self, url: str) -> dict:
        key = url.rsplit("/", 1)[-1]
        async with aiosqlite.connect(self._db) as db:
            async with db.execute(
                "SELECT data FROM deliverables WHERE key=?", (key,)
            ) as cur:
                row = await cur.fetchone()
        if not row:
            raise StorageError(f"Key not found: {key}")
        return json.loads(row[0])

    async def exists(self, url: str) -> bool:
        key = url.rsplit("/", 1)[-1]
        async with aiosqlite.connect(self._db) as db:
            async with db.execute(
                "SELECT 1 FROM deliverables WHERE key=?", (key,)
            ) as cur:
                return await cur.fetchone() is not None
```

Inject it:

```python
storage = SQLiteStorageProvider("agent.db", "https://my-agent.example.com/deliverables")
url = upload_sync(storage, {"name": "my-agent"}, filename="agent.json")
```

## Content Hashing

On-chain contracts store only a `keccak256` hash for verification:

```python
data = {"job": {"id": 42}, "result": "done"}
content_hash = StorageProvider.compute_hash(data)   # bytes32
```

The hash is computed over canonical JSON (`sort_keys=True`, `separators=(",",":")`) to ensure deterministic output regardless of dict ordering.

## Related

- [`erc8004`](../erc8004/README.md) - agent registration files can be hosted via a `StorageProvider`.
- [`core`](../core/README.md) - shared infrastructure.
