from uuid import UUID

from sqlalchemy.orm import Session

from app.models import SyncJob


def get_job(db: Session, job_id: UUID) -> SyncJob | None:
    return db.get(SyncJob, job_id)
