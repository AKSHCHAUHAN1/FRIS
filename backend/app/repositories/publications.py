from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import FacultyPublication, Provider, ProviderRecord, Publication


def list_faculty_publications(
    db: Session,
    faculty_id: UUID,
    *,
    year: int | None,
    source: str | None,
    publication_type: str | None,
    match_status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[FacultyPublication], int]:
    statement = select(FacultyPublication).join(FacultyPublication.publication)
    count_statement = select(func.count()).select_from(FacultyPublication).join(FacultyPublication.publication)
    filters = [FacultyPublication.faculty_id == faculty_id]
    if year is not None:
        filters.append(Publication.year == year)
    if publication_type:
        filters.append(Publication.publication_type.ilike(publication_type))
    if match_status:
        filters.append(FacultyPublication.match_status == match_status.upper())
    if source:
        source_exists = Publication.provider_records.any(
            ProviderRecord.provider.has(Provider.provider_name.ilike(source))
        )
        filters.append(source_exists)
    statement = statement.where(*filters)
    count_statement = count_statement.where(*filters)
    total = db.scalar(count_statement) or 0
    rows = db.scalars(
        statement.order_by(Publication.year.desc().nullslast(), Publication.title_display)
        .limit(limit)
        .offset(offset)
    ).all()
    return list(rows), total


def get_faculty_publication(db: Session, link_id: UUID) -> FacultyPublication | None:
    return db.get(FacultyPublication, link_id)
