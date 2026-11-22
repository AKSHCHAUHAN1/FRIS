from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, Faculty, Provider, SyncJob
from app.repositories.jobs import get_job
from app.schemas.jobs import SyncJobCreate, SyncJobRead
from app.core.security import UserRole

DEFAULT_PROVIDERS = ("OpenAlex", "Crossref", "Semantic Scholar", "ORCID")


def start_sync(db: Session, faculty_id: UUID, payload: SyncJobCreate, actor_role: UserRole) -> SyncJobRead:
    faculty = db.get(Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty member was not found")

    available = db.scalars(select(Provider).where(Provider.enabled.is_(True))).all()
    names = [provider.provider_name for provider in available] or list(DEFAULT_PROVIDERS)
    requested = {name.casefold() for name in payload.providers}
    if requested:
        unknown = requested - {name.casefold() for name in names}
        if unknown:
            raise HTTPException(status_code=422, detail="One or more requested providers are unavailable")
        names = [name for name in names if name.casefold() in requested]

    job = SyncJob(
        faculty_id=faculty_id,
        status="QUEUED",
        request_parameters={"year_from": payload.year_from, "year_to": payload.year_to},
        source_summary={name: "QUEUED" for name in names},
        error_summary={},
    )
    db.add(job)
    db.flush()
    db.add(
        AuditEvent(
            actor_id=f"development:{actor_role.value}",
            actor_role=actor_role.value,
            action="faculty.sync.requested",
            resource_type="sync_job",
            resource_id=str(job.job_id),
            event_data={
                "faculty_id": str(faculty_id),
                "providers": names,
                "year_from": payload.year_from,
                "year_to": payload.year_to,
            },
        )
    )
    db.commit()
    db.refresh(job)
    return to_job_read(job)


def read_job(db: Session, job_id: UUID) -> SyncJobRead:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Synchronization job was not found")
    return to_job_read(job)


def to_job_read(job: SyncJob) -> SyncJobRead:
    return SyncJobRead(
        job_id=job.job_id,
        faculty_id=job.faculty_id,
        started_at=job.started_at,
        completed_at=job.completed_at,
        status=job.status,
        request_parameters=job.request_parameters,
        source_summary=job.source_summary,
        error_summary=job.error_summary,
    )


def complete_job(
    db: Session,
    job_id: UUID,
    *,
    status: str,
    source_summary: dict,
    error_summary: dict,
) -> SyncJobRead:
    """Worker integration hook for connectors and ingestion orchestration."""
    if status not in {"SUCCEEDED", "PARTIAL", "FAILED"}:
        raise ValueError("Completed sync status must be SUCCEEDED, PARTIAL or FAILED")
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Synchronization job was not found")
    job.status = status
    job.source_summary = source_summary
    job.error_summary = error_summary
    job.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)
    return to_job_read(job)
