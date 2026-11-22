from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, Faculty, FacultyPublication, Publication
from app.repositories.publications import get_faculty_publication
from app.core.security import UserRole
from app.schemas.review import ReviewQueueItem, ReviewResult


def list_reviews(db: Session, limit: int, offset: int) -> list[ReviewQueueItem]:
    rows = db.execute(
        select(FacultyPublication, Faculty, Publication)
        .join(Faculty, Faculty.faculty_id == FacultyPublication.faculty_id)
        .join(Publication, Publication.publication_id == FacultyPublication.publication_id)
        .where(FacultyPublication.match_status == "REVIEW_NEEDED")
        .order_by(Publication.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [
        ReviewQueueItem(
            id=link.id,
            faculty_id=faculty.faculty_id,
            faculty_name=faculty.full_name,
            publication_id=publication.publication_id,
            title=publication.title_display,
            year=publication.year,
            match_score=link.match_score,
            evidence=link.evidence_json,
            created_at=publication.created_at,
        )
        for link, faculty, publication in rows
    ]


def update_review(
    db: Session, link_id: UUID, decision: str, reason: str, reviewer_role: UserRole
) -> ReviewResult:
    link = get_faculty_publication(db, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Review item was not found")
    if link.match_status != "REVIEW_NEEDED":
        raise HTTPException(status_code=409, detail="Review item has already been decided")

    previous_status = link.match_status
    decision_status = "VERIFIED" if decision == "accept" else "REJECTED"
    now = datetime.now(UTC)
    reviewer = f"development:{reviewer_role.value}"
    link.match_status = decision_status
    link.reviewed_by = reviewer
    link.reviewed_at = now
    db.add(
        AuditEvent(
            actor_id=reviewer,
            actor_role=reviewer_role.value,
            action=f"review.{decision}",
            resource_type="faculty_publication",
            resource_id=str(link.id),
            event_data={
                "previous_status": previous_status,
                "new_status": decision_status,
                "reason": reason,
            },
        )
    )
    db.commit()
    db.refresh(link)
    return ReviewResult(
        id=link.id,
        faculty_id=link.faculty_id,
        publication_id=link.publication_id,
        match_score=link.match_score,
        match_status=link.match_status,
        reviewed_by=reviewer,
        reviewed_at=link.reviewed_at or now,
        reason=reason,
    )
