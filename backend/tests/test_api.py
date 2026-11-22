import csv
import io
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Authorship,
    Faculty,
    FacultyPublication,
    Provider,
    ProviderRecord,
    Publication,
)


VALID_ORCID = "0000-0002-1825-0097"


def create_faculty(client: TestClient) -> str:
    response = client.post(
        "/api/v1/faculty",
        headers={"X-User-Role": "ADMIN"},
        json={
            "full_name": "Alex Morgan",
            "institution": "Example University",
            "department": "Computer Science",
            "institutional_email": "alex@example.edu",
            "orcid": VALID_ORCID,
            "name_variants": ["Alex J. Morgan"],
        },
    )
    assert response.status_code == 201
    return response.json()["faculty_id"]


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_faculty_creation_search_and_email_privacy(client: TestClient) -> None:
    faculty_id = create_faculty(client)
    profile = client.get(f"/api/v1/faculty/{faculty_id}").json()
    assert profile["orcid"] == VALID_ORCID
    assert profile["name_variants"] == ["Alex J. Morgan"]
    assert "institutional_email" not in profile

    search = client.get("/api/v1/faculty", params={"query": "Alex"})
    assert search.status_code == 200
    assert search.json()["total"] == 1


def test_faculty_creation_requires_admin(client: TestClient) -> None:
    response = client.post(
        "/api/v1/faculty",
        json={"full_name": "Alex Morgan", "institution": "Example University"},
    )
    assert response.status_code == 403


def test_invalid_orcid_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/faculty",
        headers={"X-User-Role": "ADMIN"},
        json={"full_name": "Alex Morgan", "institution": "Example University", "orcid": "bad"},
    )
    assert response.status_code == 422


def test_csv_import_reports_valid_and_invalid_rows(client: TestClient) -> None:
    content = (
        "full_name,institution,department,institutional_email,orcid,name_variants\n"
        f"Alex Morgan,Example University,Computer Science,,{VALID_ORCID},Alex M.\n"
        "Invalid Person,,,,,\n"
    )
    response = client.post(
        "/api/v1/faculty/import",
        headers={"X-User-Role": "ADMIN"},
        files={"file": ("faculty.csv", content, "text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["accepted"] == 1
    assert response.json()["rejected"] == 1


def test_publication_retrieval_review_update_and_export(
    client: TestClient, db_session: Session
) -> None:
    faculty = Faculty(full_name="Alex Morgan", institution="Example University")
    publication = Publication(
        doi_normalized="10.1234/fris.1",
        title_normalized="research findings",
        title_display="=Research findings",
        year=2025,
        publication_type="journal-article",
        venue="Example Journal",
    )
    provider = Provider(provider_name="OpenAlex", enabled=True)
    db_session.add_all([faculty, publication, provider])
    db_session.flush()
    db_session.add_all(
        [
            Authorship(publication_id=publication.publication_id, author_name="Alex Morgan", author_position=1),
            ProviderRecord(
                publication_id=publication.publication_id,
                provider_id=provider.provider_id,
                external_record_id="W123",
                retrieved_at=datetime.now(UTC),
                source_url="https://openalex.org/W123",
            ),
            FacultyPublication(
                faculty_id=faculty.faculty_id,
                publication_id=publication.publication_id,
                match_score=72,
                match_status="REVIEW_NEEDED",
                evidence_json={"name": {"score": 14}},
            ),
        ]
    )
    db_session.commit()

    listed = client.get(f"/api/v1/faculty/{faculty.faculty_id}/publications")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["sources"] == ["OpenAlex"]

    queue = client.get("/api/v1/reviews", headers={"X-User-Role": "REVIEWER"})
    assert queue.status_code == 200
    review_id = queue.json()[0]["id"]
    decision = client.patch(
        f"/api/v1/reviews/{review_id}",
        headers={"X-User-Role": "REVIEWER"},
        json={"decision": "accept", "reason": "Verified against the faculty profile."},
    )
    assert decision.status_code == 200
    assert decision.json()["match_status"] == "VERIFIED"

    exported = client.get(f"/api/v1/faculty/{faculty.faculty_id}/export")
    assert exported.status_code == 200
    csv_rows = list(csv.reader(io.StringIO(exported.text)))
    assert csv_rows[1][0] == "'=Research findings"


def test_publication_doi_is_unique(db_session: Session) -> None:
    db_session.add_all(
        [
            Publication(doi_normalized="10.1234/duplicate", title_normalized="one", title_display="One"),
            Publication(doi_normalized="10.1234/duplicate", title_normalized="two", title_display="Two"),
        ]
    )
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
    else:
        raise AssertionError("duplicate DOI should violate the unique constraint")
