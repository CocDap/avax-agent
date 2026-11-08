"""Redis job queue (arq) shared by the indexer (producer) and workers (consumer)."""

from __future__ import annotations

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings

#: arq function names, referenced by producers and registered in WorkerSettings.
RUN_JOB = "run_job"
REGISTER_AGENT = "register_agent"


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


async def get_queue() -> ArqRedis:
    """Open an arq connection pool (callers own its lifetime)."""
    return await create_pool(redis_settings())
