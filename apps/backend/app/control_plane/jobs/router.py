from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.control_plane.jobs.models import JobStatus
from app.control_plane.jobs.schemas import JobEventRead, JobRead
from app.control_plane.jobs.service import JobService
from app.core.security import CurrentUser
from app.db.session import DbSession

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobRead])
async def list_jobs(
    user: CurrentUser,
    db: DbSession,
    agent_id: uuid.UUID | None = None,
    status: JobStatus | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[JobRead]:
    return await JobService(db).list(user.id, agent_id, status, limit, offset)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: uuid.UUID, user: CurrentUser, db: DbSession) -> JobRead:
    return await JobService(db).get(user.id, job_id)


@router.get("/{job_id}/events", response_model=list[JobEventRead])
async def job_events(job_id: uuid.UUID, user: CurrentUser, db: DbSession) -> list[JobEventRead]:
    return await JobService(db).events(user.id, job_id)
