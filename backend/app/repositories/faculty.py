from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Faculty, FacultyNameVariant


def get_faculty(db: Session, faculty_id: UUID) -> Faculty | None:
    return db.get(Faculty, faculty_id)


def search_faculty(
    db: Session, query: str | None, department: str | None, limit: int, offset: int
) -> tuple[list[Faculty], int]:
    statement = select(Faculty)
    count_statement = select(func.count()).select_from(Faculty)
    filters = []
    if query:
        pattern = f"%{query.strip()}%"
        filters.append(
            or_(
                Faculty.full_name.ilike(pattern),
                Faculty.institution.ilike(pattern),
                Faculty.orcid.ilike(pattern),
                Faculty.name_variants.any(FacultyNameVariant.name.ilike(pattern)),
            )
        )
    if department:
        filters.append(Faculty.department.ilike(f"%{department.strip()}%"))
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    total = db.scalar(count_statement) or 0
    rows = db.scalars(statement.order_by(Faculty.full_name).limit(limit).offset(offset)).all()
    return list(rows), total
