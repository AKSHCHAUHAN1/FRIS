from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class MatchStatus(StrEnum):
    VERIFIED = "VERIFIED"
    REVIEW_NEEDED = "REVIEW_NEEDED"
    REJECTED = "REJECTED"


class FacultyIdentifier(BaseModel):
    scheme: str
    value: str
    verified: bool = False


class FacultyProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    faculty_id: UUID
    full_name: str
    institution: str
    department: str | None = None
    institutional_email: str | None = None
    orcid: str | None = None
    name_variants: list[str] = Field(default_factory=list)
    external_identifiers: list[FacultyIdentifier] = Field(default_factory=list)


class WorkAuthor(BaseModel):
    name: str
    external_author_id: str | None = None
    affiliation: str | None = None


class WorkCandidate(BaseModel):
    """Provider-neutral publication candidate emitted by scholarly connectors."""

    source: str = Field(min_length=1, max_length=80)
    source_record_id: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=20000)
    normalized_title: str | None = None
    doi: str | None = None
    year: int | None = Field(default=None, ge=1000, le=3000)
    publication_type: str | None = None
    venue: str | None = None
    abstract: str | None = None
    authors: list[WorkAuthor] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    external_author_ids: list[FacultyIdentifier] = Field(default_factory=list)
    landing_page_url: HttpUrl | None = None
    open_access_url: HttpUrl | None = None
    raw_payload: dict[str, Any] | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("source", "source_record_id", "title", mode="before")
    @classmethod
    def strip_required_fields(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class MatchResult(BaseModel):
    confidence_score: int = Field(ge=0, le=100)
    match_status: MatchStatus
    evidence: dict[str, Any] = Field(default_factory=dict)
    contradictions: list[str] = Field(default_factory=list)
    decision_reason: str


class ConnectorHealth(BaseModel):
    provider: str
    available: bool
    detail: str | None = None


class ScholarlyConnector(Protocol):
    """Common connector boundary; provider-specific logic stays behind it."""

    name: str

    async def search_faculty(self, query: str) -> list[dict[str, Any]]: ...

    async def get_author(self, author_id: str) -> dict[str, Any] | None: ...

    async def list_works(self, author_id: str) -> list[WorkCandidate]: ...

    def normalize(self, record: dict[str, Any]) -> WorkCandidate: ...

    async def health_check(self) -> ConnectorHealth: ...
