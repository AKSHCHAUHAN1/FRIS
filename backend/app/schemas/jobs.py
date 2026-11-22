from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SyncJobCreate(BaseModel):
    providers: list[str] = Field(default_factory=list, max_length=10)
    year_from: int | None = Field(default=None, ge=1000, le=3000)
    year_to: int | None = Field(default=None, ge=1000, le=3000)


class SyncJobRead(BaseModel):
    job_id: UUID
    faculty_id: UUID
    started_at: datetime
    completed_at: datetime | None
    status: str
    request_parameters: dict
    source_summary: dict
    error_summary: dict
