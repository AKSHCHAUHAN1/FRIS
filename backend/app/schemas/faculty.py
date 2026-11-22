from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.contracts import FacultyIdentifier


def normalize_orcid(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    cleaned = value.strip().removeprefix("https://orcid.org/").removeprefix("http://orcid.org/")
    compact = cleaned.replace("-", "").upper()
    if len(compact) != 16 or not compact[:15].isdigit() or compact[-1] not in "0123456789X":
        raise ValueError("ORCID must use the 16-character ORCID format")
    checksum = 0
    for digit in compact[:15]:
        checksum = (checksum + int(digit)) * 2
    result = (12 - checksum % 11) % 11
    expected = "X" if result == 10 else str(result)
    if compact[-1] != expected:
        raise ValueError("ORCID checksum is invalid")
    return "-".join(compact[i : i + 4] for i in range(0, 16, 4))


class FacultyCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=240)
    institution: str = Field(min_length=2, max_length=300)
    department: str | None = Field(default=None, max_length=240)
    institutional_email: EmailStr | None = None
    orcid: str | None = None
    name_variants: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("full_name", "institution", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("department", mode="before")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("orcid")
    @classmethod
    def validate_orcid(cls, value: str | None) -> str | None:
        return normalize_orcid(value)

    @field_validator("name_variants")
    @classmethod
    def normalize_variants(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))


class FacultyUpdate(BaseModel):
    department: str | None = Field(default=None, max_length=240)
    institution: str | None = Field(default=None, min_length=2, max_length=300)
    institutional_email: EmailStr | None = None
    orcid: str | None = None
    name_variants: list[str] | None = Field(default=None, max_length=30)

    @field_validator("orcid")
    @classmethod
    def validate_orcid(cls, value: str | None) -> str | None:
        return normalize_orcid(value)


class FacultyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    faculty_id: UUID
    full_name: str
    institution: str
    department: str | None = None
    orcid: str | None = None
    status: str
    name_variants: list[str] = Field(default_factory=list)
    external_identifiers: list[FacultyIdentifier] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class FacultyPage(BaseModel):
    items: list[FacultyRead]
    total: int
    limit: int
    offset: int


class ImportRowError(BaseModel):
    row: int
    message: str


class FacultyImportResult(BaseModel):
    accepted: int
    rejected: int
    errors: list[ImportRowError]
