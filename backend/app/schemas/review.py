from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewUpdate(BaseModel):
    decision: str = Field(pattern="^(accept|reject)$")
    reason: str = Field(min_length=3, max_length=2000)


class ReviewQueueItem(BaseModel):
    id: UUID
    faculty_id: UUID
    faculty_name: str
    publication_id: UUID
    title: str
    year: int | None
    match_score: int
    evidence: dict
    created_at: datetime


class ReviewResult(BaseModel):
    id: UUID
    faculty_id: UUID
    publication_id: UUID
    match_score: int
    match_status: str
    reviewed_by: str
    reviewed_at: datetime
    reason: str
