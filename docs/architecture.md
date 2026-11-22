# FRIS architecture

FRIS is a monorepo. API routes depend on service interfaces; provider-specific response parsing stays in connectors; matching and deduplication consume provider-neutral schemas; persistence retains each provider record alongside canonical publications.

```text
Faculty profile
  → Connector orchestration
  → WorkCandidate normalization
  → Author match evidence
  → DOI-first deduplication
  → PostgreSQL (canonical work + provider records)
  → FastAPI
  → React dashboard
```

The first milestone establishes contracts and local development. Connector collection, identity scoring, deduplication rules and dashboard workflows are implemented independently by their owners and integrated against the shared schemas.

## Main boundaries

- `backend/app/api`: HTTP request/response handling only.
- `backend/app/services`: orchestration and persistence use cases.
- `backend/app/models` and `backend/app/database`: SQLAlchemy entities and sessions.
- `backend/app/connectors`: external API behavior and provider normalization.
- `backend/app/matching` and `backend/app/deduplication`: provider-independent algorithms.
- `frontend`: typed API client and user interface.
- `infra`: local containers and deployment configuration.

## Data and privacy

Institutional email is an internal faculty-directory field and should not be sent to providers by default or returned in ordinary faculty search responses. Store source links, retrieval timestamps and provider identity for every ingested record. Retain raw provider payloads only where the source terms and project policy allow it.
