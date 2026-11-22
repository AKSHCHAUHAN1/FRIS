# Faculty Research Intelligence System (FRIS)

FRIS discovers faculty publications from permitted scholarly metadata APIs, evaluates author identity with explainable evidence, preserves provider provenance, and presents a searchable publication profile.

The system accepts faculty identity details as input. It discovers publication metadata itself. Automated Google Scholar scraping and paywalled full-text collection are out of scope.

## Repository map

| Path | Responsibility |
| --- | --- |
| `backend/app/api`, `models`, `schemas`, `database`, `services`, `alembic` | Aksh: FastAPI, PostgreSQL, faculty/publication APIs and persistence |
| `backend/app/connectors` | Prince: provider clients and ingestion |
| `backend/app/matching`, `deduplication` | Yash: identity evidence and conservative duplicate handling |
| `frontend` | Shivanya: React dashboard and API client |
| `infra`, `.github/workflows` | Shared local containers and CI/CD integration |
| `data/sample_faculty.csv` | Example faculty identity input; use fictional/sample values only |

All members should agree on the contracts in `backend/app/schemas` and `docs/api-contract.md` before implementing their modules. Provider records must retain their source and retrieval metadata when canonical publications are stored.

## Run the development skeleton

1. Copy `.env.example` to `.env` and adjust values for your environment.
2. Start the services with `docker compose up --build`.
3. Open the frontend at <http://localhost:5173> and the API docs at <http://localhost:8000/docs>.
4. Check API liveness at <http://localhost:8000/health>.

For local backend work without Docker, apply migrations before starting the API:

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The backend API, schema and persistence integration notes are in [`backend/README.md`](backend/README.md).

For local frontend work:

```sh
cd frontend
npm install
npm run dev
```

The backend contract uses `/api/v1`. `DATABASE_URL`, CORS origins and provider credentials are configured through environment variables. Never commit a real `.env` file or API key.

## Project flow

Faculty identity → provider connectors → normalized `WorkCandidate` records → author matching → deduplication → PostgreSQL with source provenance → FastAPI → React dashboard.

OpenAlex, Crossref, Semantic Scholar and ORCID are the planned sources. Provider failures should be recorded independently so one source outage does not discard results from other sources.
