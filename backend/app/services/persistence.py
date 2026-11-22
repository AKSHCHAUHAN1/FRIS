from datetime import UTC, datetime
from typing import Iterable
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Authorship,
    Faculty,
    FacultyPublication,
    Provider,
    ProviderRecord,
    Publication,
)
from app.schemas.contracts import MatchResult, WorkCandidate


def persist_ingested_work(
    db: Session,
    faculty_id: UUID,
    canonical_work: WorkCandidate,
    source_records: Iterable[WorkCandidate],
    match_result: MatchResult,
) -> Publication:
    """Persist a canonical work, its provider provenance and faculty match atomically.

    Deduplication decides which candidates belong to ``source_records``. This function
    preserves those records and only uses normalized DOI as the database identity key.
    """
    records = list(source_records)
    if not records:
        raise ValueError("At least one provider record is required to preserve provenance")
    faculty = db.get(Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty member was not found")

    doi = normalize_doi(canonical_work.doi)
    publication = None
    if doi:
        publication = db.scalar(select(Publication).where(Publication.doi_normalized == doi))
    if publication is None:
        publication = Publication(
            doi_normalized=doi,
            title_normalized=canonical_work.normalized_title or normalize_title(canonical_work.title),
            title_display=canonical_work.title,
            year=canonical_work.year,
            publication_type=canonical_work.publication_type,
            venue=canonical_work.venue,
            abstract=canonical_work.abstract,
            url=str(canonical_work.landing_page_url) if canonical_work.landing_page_url else None,
        )
        db.add(publication)
        db.flush()

    if not publication.authorships:
        for index, author in enumerate(canonical_work.authors, start=1):
            db.add(
                Authorship(
                    publication_id=publication.publication_id,
                    author_name=author.name,
                    author_position=index,
                    external_author_id=author.external_author_id,
                    affiliation_text=author.affiliation,
                )
            )

    for record in records:
        provider_name = record.source.strip()
        provider = db.scalar(
            select(Provider).where(func.lower(Provider.provider_name) == provider_name.lower())
        )
        if provider is None:
            provider = Provider(provider_name=provider_name, enabled=True)
            db.add(provider)
            db.flush()
        provider_record = db.scalar(
            select(ProviderRecord).where(
                ProviderRecord.provider_id == provider.provider_id,
                ProviderRecord.external_record_id == record.source_record_id,
            )
        )
        retrieved_at = record.retrieved_at or datetime.now(UTC)
        source_url = str(record.landing_page_url) if record.landing_page_url else None
        raw_json = record.raw_payload
        if provider_record is None:
            db.add(
                ProviderRecord(
                    publication_id=publication.publication_id,
                    provider_id=provider.provider_id,
                    external_record_id=record.source_record_id,
                    raw_json=raw_json,
                    retrieved_at=retrieved_at,
                    source_url=source_url,
                )
            )
        else:
            provider_record.publication_id = publication.publication_id
            provider_record.raw_json = raw_json
            provider_record.retrieved_at = retrieved_at
            provider_record.source_url = source_url

    link = db.scalar(
        select(FacultyPublication).where(
            FacultyPublication.faculty_id == faculty_id,
            FacultyPublication.publication_id == publication.publication_id,
        )
    )
    evidence = {
        "evidence": match_result.evidence,
        "contradictions": match_result.contradictions,
        "decision_reason": match_result.decision_reason,
    }
    if link is None:
        db.add(
            FacultyPublication(
                faculty_id=faculty_id,
                publication_id=publication.publication_id,
                match_score=match_result.confidence_score,
                match_status=match_result.match_status.value,
                evidence_json=evidence,
            )
        )
    else:
        link.match_score = match_result.confidence_score
        link.match_status = match_result.match_status.value
        link.evidence_json = evidence

    db.commit()
    db.refresh(publication)
    return publication


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    doi = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix) :]
            break
    return doi.strip() or None


def normalize_title(value: str) -> str:
    return " ".join(value.casefold().split())
