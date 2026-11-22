from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import UserRole, require_role
from app.database.session import get_db
from app.schemas.jobs import SyncJobRead
from app.services.jobs import read_job

router = APIRouter()


@router.get("/{job_id}", response_model=SyncJobRead)
def get_sync_job(
    job_id: UUID,
    _: UserRole = Depends(require_role(UserRole.VIEWER)),
    db: Session = Depends(get_db),
) -> SyncJobRead:
    return read_job(db, job_id)
