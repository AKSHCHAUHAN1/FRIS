# Backend API and database

The backend uses FastAPI, Pydantic v2 and synchronous SQLAlchemy 2.x sessions. PostgreSQL is the development database; the SQLAlchemy session dependency can be overridden for isolated tests.

## Apply database migrations

From the `backend` directory, configure `DATABASE_URL` and run:

```sh
alembic upgrade head
uvicorn app.main:app --reload
```

Docker Compose applies migrations before starting the API. Migration revision `0001_initial_schema` creates the faculty directory, identifiers and name variants, canonical publications, provider provenance, authorship, faculty-publication decisions, sync jobs and audit events. PostgreSQL permits multiple null DOI values while enforcing uniqueness for non-null DOI values. See [`docs/database-schema.md`](../docs/database-schema.md) for the entity relationships.

## Endpoints

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET | `/api/v1/health/ready` | Database readiness |
| GET | `/api/v1/faculty?query=&department=&limit=&offset=` | Viewer |
| POST | `/api/v1/faculty` | Admin |
| POST | `/api/v1/faculty/import` | Admin; CSV upload |
| GET | `/api/v1/faculty/{faculty_id}` | Viewer |
| GET | `/api/v1/faculty/{faculty_id}/publications` | Viewer; year/source/type/status filters |
| POST | `/api/v1/faculty/{faculty_id}/sync` | Reviewer or admin |
| GET | `/api/v1/jobs/{job_id}` | Viewer |
| GET | `/api/v1/reviews` | Reviewer or admin |
| PATCH | `/api/v1/reviews/{id}` | Reviewer or admin |
| GET | `/api/v1/faculty/{faculty_id}/export` | Viewer; CSV |

In development, send `X-User-Role: VIEWER`, `REVIEWER` or `ADMIN` to exercise route guards. The header is deliberately rejected outside `APP_ENV=development`; production authentication must be wired before deployment. Faculty responses omit institutional email.

## Example requests

Create a faculty profile:

```sh
curl -X POST http://localhost:8000/api/v1/faculty \
  -H 'Content-Type: application/json' -H 'X-User-Role: ADMIN' \
  -d '{"full_name":"Alex Morgan","institution":"Example University","department":"Computer Science","orcid":"0000-0002-1825-0097","name_variants":["Alex J. Morgan"]}'
```

Import faculty identities from CSV:

```sh
curl -X POST http://localhost:8000/api/v1/faculty/import \
  -H 'X-User-Role: ADMIN' -F 'file=@../data/sample_faculty.csv'
```

Start a sync job (the job is persisted as `QUEUED` for the ingestion worker):

```sh
curl -X POST http://localhost:8000/api/v1/faculty/FACULTY_UUID/sync \
  -H 'Content-Type: application/json' -H 'X-User-Role: REVIEWER' \
  -d '{"providers":["OpenAlex","Crossref"],"year_from":2018}'
```

Accept an ambiguous attribution:

```sh
curl -X PATCH http://localhost:8000/api/v1/reviews/REVIEW_ID \
  -H 'Content-Type: application/json' -H 'X-User-Role: REVIEWER' \
  -d '{"decision":"accept","reason":"Confirmed against the researcher profile."}'
```

## Integration hooks

- Connectors normalize provider payloads to `WorkCandidate` and keep source IDs, URLs and retrieval timestamps.
- The matching/deduplication pipeline supplies one canonical candidate, its provider records and a `MatchResult` to `services.persistence.persist_ingested_work(...)`. This transaction stores the canonical publication, all source records and the faculty attribution.
- The worker calls `services.jobs.complete_job(...)` with final provider statuses. `start_sync(...)` creates a durable job but does not call providers itself.
- Institutional email is stored for internal use only and is omitted from ordinary faculty APIs and exports.
- Raw payloads are persisted only when connectors are allowed to retain them under the provider terms.

## Tests and environment

Install `requirements-dev.txt` and run `pytest` from this directory. The tests use an in-memory SQLite database, covering faculty creation/search/import, ORCID validation, health, publication retrieval, review decisions, CSV export and DOI uniqueness. `DATABASE_URL`, `CORS_ORIGINS`, `APP_ENV`, `ALLOW_DEV_ROLE_HEADER` and `LOG_LEVEL` are configured in the root `.env`; provider credentials are added by the connector owner.
