from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PublicationRead(BaseModel):
    publication_id: UUID
    title: str
    doi: str | None
    year: int | None
    publication_type: str | None
    venue: str | None
    abstract: str | None
    url: str | None
    authors: list[str]
    sources: list[str]
    source_urls: list[str]
    retrieved_at: datetime | None
    match_score: int
    match_status: str
    evidence: dict


class PublicationPage(BaseModel):
    items: list[PublicationRead]
    total: int
    limit: int
    offset: int
