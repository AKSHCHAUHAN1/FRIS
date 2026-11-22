# Shared API and data contracts

The API is versioned under `/api/v1`. Public scholarly metadata is represented using provider-neutral Pydantic schemas in `backend/app/schemas/contracts.py`.

## Faculty profile

`FacultyProfile` includes an internal faculty ID, full name, institution, optional department, institutional email, ORCID, known name variants and provider-specific identifiers. Email is restricted profile data and is not part of ordinary public responses.

## Work candidate

Every connector maps provider records to `WorkCandidate`: source and source record ID, display and normalized title, DOI, year, publication type, venue, abstract, authors, affiliations, external author IDs, source URLs, raw payload when permitted, and retrieval time.

## Author matching

The matching interface accepts a `FacultyProfile` and `WorkCandidate`, then returns a `MatchResult` with a 0–100 confidence score, a `VERIFIED`, `REVIEW_NEEDED` or `REJECTED` status, structured evidence, contradictions and a decision reason. A high score alone is not sufficient for automatic verification.

## Connector interface

Connectors expose faculty search, author lookup, work listing, normalization and health check operations. Unsupported provider operations should return a clear unsupported result rather than fabricated data.

## Planned HTTP routes

- `GET /health`
- `GET /api/v1/faculty` and `GET /api/v1/faculty/{faculty_id}`
- `GET /api/v1/faculty/{faculty_id}/publications`
- `POST /api/v1/faculty/{faculty_id}/sync`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/reviews` and `PATCH /api/v1/reviews/{id}`
- `GET /api/v1/faculty/{faculty_id}/export`

Responses should use stable status values, pagination where lists may grow, and safe error messages without raw provider responses or secrets.
