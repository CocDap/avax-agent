"""Job log queries. TODO: implement."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.control_plane.jobs.models import JobStatus
from app.control_plane.jobs.schemas import JobEventRead, JobRead
from app.core.errors import NotImplementedYet


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        owner_id: str,
        agent_id: uuid.UUID | None,
        status: JobStatus | None,
        limit: int,
        offset: int,
    ) -> list[JobRead]:
        raise NotImplementedYet("jobs.list")

    async def get(self, owner_id: str, job_id: uuid.UUID) -> JobRead:
        raise NotImplementedYet("jobs.get")

    async def events(self, owner_id: str, job_id: uuid.UUID) -> list[JobEventRead]:
        raise NotImplementedYet("jobs.events")
