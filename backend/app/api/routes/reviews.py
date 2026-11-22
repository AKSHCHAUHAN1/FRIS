from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import UserRole, require_role
from app.database.session import get_db
from app.schemas.review import ReviewQueueItem, ReviewResult, ReviewUpdate
from app.services.reviews import list_reviews, update_review

router = APIRouter()


@router.get("", response_model=list[ReviewQueueItem])
def review_queue(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: UserRole = Depends(require_role(UserRole.REVIEWER)),
    db: Session = Depends(get_db),
) -> list[ReviewQueueItem]:
    return list_reviews(db, limit, offset)


@router.patch("/{review_id}", response_model=ReviewResult)
def review_match(
    review_id: UUID,
    payload: ReviewUpdate,
    role: UserRole = Depends(require_role(UserRole.REVIEWER)),
    db: Session = Depends(get_db),
) -> ReviewResult:
    return update_review(db, review_id, payload.decision, payload.reason, role)
