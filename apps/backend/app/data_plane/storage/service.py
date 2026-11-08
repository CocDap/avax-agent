"""Storage selection. Local + IPFS reuse ``avaxagent.storage``; S3 is TODO."""

from __future__ import annotations

from avaxagent.storage import IPFSStorageProvider, LocalStorageProvider, StorageProvider

from app.core.config import settings
from app.core.errors import NotImplementedYet


def get_storage() -> StorageProvider:
    backend = settings.storage_backend.lower()
    if backend == "local":
        return LocalStorageProvider(base_dir=settings.storage_local_path)
    if backend == "ipfs":
        return IPFSStorageProvider.from_env()
    if backend == "s3":
        raise NotImplementedYet("storage.s3")
    raise ValueError(f"unknown STORAGE_BACKEND={settings.storage_backend!r}")
