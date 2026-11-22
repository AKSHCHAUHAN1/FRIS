from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import UserRole, require_role
from app.database.session import get_db
from app.schemas.faculty import FacultyCreate, FacultyImportResult, FacultyPage, FacultyRead
from app.schemas.jobs import SyncJobCreate, SyncJobRead
from app.schemas.publication import PublicationPage
from app.services.faculty import create_faculty, find_faculty, import_faculty_csv, read_faculty
from app.services.jobs import start_sync
from app.services.publications import export_faculty_publications, get_publications

router = APIRouter()


@router.post("/import", response_model=FacultyImportResult, status_code=status.HTTP_200_OK)
def import_faculty(
    file: UploadFile = File(...),
    _: UserRole = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> FacultyImportResult:
    if file.content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel", None}:
        raise HTTPException(status_code=415, detail="Upload a CSV file")
    content = file.file.read(5_000_001)
    if len(content) > 5_000_000:
        raise HTTPException(status_code=413, detail="CSV file exceeds the 5 MB limit")
    return import_faculty_csv(db, content)


@router.post("", response_model=FacultyRead, status_code=status.HTTP_201_CREATED)
def create_faculty_profile(
    payload: FacultyCreate,
    _: UserRole = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> FacultyRead:
    return create_faculty(db, payload)


@router.get("", response_model=FacultyPage)
def search_faculty_profiles(
    query: str | None = Query(default=None, max_length=240),
    department: str | None = Query(default=None, max_length=240),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: UserRole = Depends(require_role(UserRole.VIEWER)),
    db: Session = Depends(get_db),
) -> FacultyPage:
    return find_faculty(db, query, department, limit, offset)


@router.get("/{faculty_id}/export")
def export_publications(
    faculty_id: UUID,
    year: int | None = Query(default=None, ge=1000, le=3000),
    source: str | None = Query(default=None, max_length=80),
    publication_type: str | None = Query(default=None, max_length=100),
    match_status: str | None = Query(default=None, pattern="^(VERIFIED|REVIEW_NEEDED|REJECTED)$"),
    _: UserRole = Depends(require_role(UserRole.VIEWER)),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    content = export_faculty_publications(
        db,
        faculty_id,
        year=year,
        source=source,
        publication_type=publication_type,
        match_status=match_status,
    )
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="faculty-{faculty_id}-publications.csv"'},
    )


@router.get("/{faculty_id}/publications", response_model=PublicationPage)
def faculty_publications(
    faculty_id: UUID,
    year: int | None = Query(default=None, ge=1000, le=3000),
    source: str | None = Query(default=None, max_length=80),
    publication_type: str | None = Query(default=None, max_length=100),
    match_status: str | None = Query(default=None, pattern="^(VERIFIED|REVIEW_NEEDED|REJECTED)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: UserRole = Depends(require_role(UserRole.VIEWER)),
    db: Session = Depends(get_db),
) -> PublicationPage:
    return get_publications(
        db,
        faculty_id,
        year=year,
        source=source,
        publication_type=publication_type,
        match_status=match_status,
        limit=limit,
        offset=offset,
    )


@router.post("/{faculty_id}/sync", response_model=SyncJobRead, status_code=status.HTTP_202_ACCEPTED)
def request_sync(
    faculty_id: UUID,
    payload: SyncJobCreate,
    role: UserRole = Depends(require_role(UserRole.REVIEWER)),
    db: Session = Depends(get_db),
) -> SyncJobRead:
    if payload.year_from and payload.year_to and payload.year_from > payload.year_to:
        raise HTTPException(status_code=422, detail="year_from must not exceed year_to")
    return start_sync(db, faculty_id, payload, role)


@router.get("/{faculty_id}", response_model=FacultyRead)
def get_faculty_profile(
    faculty_id: UUID,
    _: UserRole = Depends(require_role(UserRole.VIEWER)),
    db: Session = Depends(get_db),
) -> FacultyRead:
    return read_faculty(db, faculty_id)
