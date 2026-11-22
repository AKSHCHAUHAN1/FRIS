import csv
import io
from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Faculty, FacultyIdentifier, FacultyNameVariant
from app.repositories.faculty import get_faculty, search_faculty
from app.schemas.contracts import FacultyIdentifier as FacultyIdentifierSchema
from app.schemas.faculty import (
    FacultyCreate,
    FacultyImportResult,
    FacultyPage,
    FacultyRead,
    ImportRowError,
)


def to_faculty_read(faculty: Faculty) -> FacultyRead:
    return FacultyRead(
        faculty_id=faculty.faculty_id,
        full_name=faculty.full_name,
        institution=faculty.institution,
        department=faculty.department,
        orcid=faculty.orcid,
        status=faculty.status,
        name_variants=[variant.name for variant in faculty.name_variants],
        external_identifiers=[
            FacultyIdentifierSchema(
                scheme=identifier.scheme,
                value=identifier.value,
                verified=identifier.verified,
            )
            for identifier in faculty.identifiers
        ],
        created_at=faculty.created_at,
        updated_at=faculty.updated_at,
    )


def create_faculty(db: Session, payload: FacultyCreate) -> FacultyRead:
    faculty = Faculty(
        full_name=payload.full_name,
        institution=payload.institution,
        department=payload.department,
        institutional_email=str(payload.institutional_email) if payload.institutional_email else None,
        orcid=payload.orcid,
    )
    faculty.name_variants = [FacultyNameVariant(name=name) for name in payload.name_variants]
    if payload.orcid:
        faculty.identifiers = [FacultyIdentifier(scheme="ORCID", value=payload.orcid, verified=False)]
    db.add(faculty)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Faculty identifier is already assigned") from exc
    db.refresh(faculty)
    return to_faculty_read(faculty)


def read_faculty(db: Session, faculty_id: UUID) -> FacultyRead:
    faculty = get_faculty(db, faculty_id)
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty member was not found")
    return to_faculty_read(faculty)


def find_faculty(
    db: Session, query: str | None, department: str | None, limit: int, offset: int
) -> FacultyPage:
    rows, total = search_faculty(db, query, department, limit, offset)
    return FacultyPage(items=[to_faculty_read(row) for row in rows], total=total, limit=limit, offset=offset)


def import_faculty_csv(db: Session, content: bytes) -> FacultyImportResult:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc
    reader = csv.DictReader(io.StringIO(text))
    required = {"full_name", "institution"}
    if not reader.fieldnames or not required.issubset({name.strip() for name in reader.fieldnames}):
        raise HTTPException(status_code=422, detail="CSV must include full_name and institution columns")

    accepted = 0
    errors: list[ImportRowError] = []
    for row_number, row in enumerate(reader, start=2):
        normalized = {str(key).strip(): value for key, value in row.items() if key is not None}
        variants_raw = normalized.get("name_variants", "") or ""
        payload_data = {
            "full_name": normalized.get("full_name"),
            "institution": normalized.get("institution"),
            "department": normalized.get("department") or None,
            "institutional_email": normalized.get("institutional_email") or None,
            "orcid": normalized.get("orcid") or None,
            "name_variants": [part.strip() for part in variants_raw.replace("|", ";").split(";")],
        }
        try:
            payload = FacultyCreate.model_validate(payload_data)
            _insert_faculty(db, payload)
            db.commit()
            accepted += 1
        except (ValidationError, ValueError) as exc:
            db.rollback()
            details = exc.errors() if isinstance(exc, ValidationError) else []
            if details:
                message = f"{'.'.join(str(part) for part in details[0]['loc'])}: {details[0]['msg']}"
            else:
                message = str(exc)[:160] or "Invalid row"
            errors.append(ImportRowError(row=row_number, message=message))
        except IntegrityError:
            db.rollback()
            errors.append(ImportRowError(row=row_number, message="Identifier is already assigned"))
    return FacultyImportResult(accepted=accepted, rejected=len(errors), errors=errors)


def _insert_faculty(db: Session, payload: FacultyCreate) -> Faculty:
    faculty = Faculty(
        full_name=payload.full_name,
        institution=payload.institution,
        department=payload.department,
        institutional_email=str(payload.institutional_email) if payload.institutional_email else None,
        orcid=payload.orcid,
    )
    faculty.name_variants = [FacultyNameVariant(name=name) for name in payload.name_variants]
    if payload.orcid:
        faculty.identifiers = [FacultyIdentifier(scheme="ORCID", value=payload.orcid, verified=False)]
    db.add(faculty)
    db.flush()
    return faculty
