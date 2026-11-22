import csv
import io
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Faculty, FacultyPublication
from app.repositories.publications import list_faculty_publications
from app.schemas.publication import PublicationPage, PublicationRead


def to_publication_read(link: FacultyPublication) -> PublicationRead:
    publication = link.publication
    records = publication.provider_records
    retrieved_at = max((record.retrieved_at for record in records), default=None)
    return PublicationRead(
        publication_id=publication.publication_id,
        title=publication.title_display,
        doi=publication.doi_normalized,
        year=publication.year,
        publication_type=publication.publication_type,
        venue=publication.venue,
        abstract=publication.abstract,
        url=publication.url,
        authors=[author.author_name for author in publication.authorships],
        sources=sorted({record.provider.provider_name for record in records}),
        source_urls=sorted({record.source_url for record in records if record.source_url}),
        retrieved_at=retrieved_at,
        match_score=link.match_score,
        match_status=link.match_status,
        evidence=link.evidence_json,
    )


def get_publications(
    db: Session,
    faculty_id: UUID,
    *,
    year: int | None,
    source: str | None,
    publication_type: str | None,
    match_status: str | None,
    limit: int,
    offset: int,
) -> PublicationPage:
    if db.get(Faculty, faculty_id) is None:
        raise HTTPException(status_code=404, detail="Faculty member was not found")
    rows, total = list_faculty_publications(
        db,
        faculty_id,
        year=year,
        source=source,
        publication_type=publication_type,
        match_status=match_status,
        limit=limit,
        offset=offset,
    )
    return PublicationPage(
        items=[to_publication_read(row) for row in rows], total=total, limit=limit, offset=offset
    )


def export_faculty_publications(
    db: Session,
    faculty_id: UUID,
    *,
    year: int | None = None,
    source: str | None = None,
    publication_type: str | None = None,
    match_status: str | None = None,
) -> str:
    if db.get(Faculty, faculty_id) is None:
        raise HTTPException(status_code=404, detail="Faculty member was not found")
    rows, _ = list_faculty_publications(
        db,
        faculty_id,
        year=year,
        source=source,
        publication_type=publication_type,
        match_status=match_status,
        limit=10000,
        offset=0,
    )
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "title",
            "year",
            "venue",
            "publication_type",
            "doi",
            "authors",
            "sources",
            "source_urls",
            "match_score",
            "match_status",
            "retrieved_at",
        ]
    )
    for link in rows:
        item = to_publication_read(link)
        writer.writerow(
            [
                _spreadsheet_safe(item.title),
                item.year or "",
                _spreadsheet_safe(item.venue or ""),
                _spreadsheet_safe(item.publication_type or ""),
                _spreadsheet_safe(item.doi or ""),
                "; ".join(_spreadsheet_safe(author) for author in item.authors),
                "; ".join(item.sources),
                "; ".join(_spreadsheet_safe(url) for url in item.source_urls),
                item.match_score,
                item.match_status,
                item.retrieved_at.isoformat() if item.retrieved_at else "",
            ]
        )
    return buffer.getvalue()


def _spreadsheet_safe(value: str) -> str:
    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value
