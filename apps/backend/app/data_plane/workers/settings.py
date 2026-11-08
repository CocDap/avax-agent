"""arq worker entrypoint: ``arq app.data_plane.workers.settings.WorkerSettings``."""

from __future__ import annotations

from app.core.queue import redis_settings
from app.data_plane.workers.tasks import register_agent, run_job


class WorkerSettings:
    functions = [run_job, register_agent]  # names match app.core.queue constants
    redis_settings = redis_settings()
    max_jobs = 10
    job_timeout = 600  # seconds; LLM tasks can be slow
