# Project Documentation & Handoff Summary

Last reviewed: 2026-07-04  
Repository: `job_search_agent`

## 1. Executive Summary

`job_search_agent` is an AI-assisted job search workspace. It combines a FastAPI backend, SQL persistence, optional Redis caching, optional OpenAI-powered parsing/embeddings/explanations, provider-based job ingestion, and a Next.js frontend for searching jobs, creating a candidate profile, viewing recommendations, saving jobs, and tracking application statuses.

Primary purpose:

- Help a job seeker turn job listings into a smaller ranked set of opportunities.
- Explain why jobs match a search or profile.
- Maintain a lightweight saved/application pipeline.

Current implementation status:

- Implemented as a working private-beta style prototype.
- Backend API, database models, Alembic migration, ingestion connectors, ranking logic, and frontend screens exist.
- CI exists for backend smoke checks and frontend production build.
- Authentication, ownership isolation, profile deletion, analytics, scheduled ingestion, editable profile persistence, and richer pipeline workflow are planned but not implemented.

Key implemented features:

- Natural-language job search with extracted filters.
- Job import from JSON, Remotive, Adzuna, Greenhouse, and Lever.
- Job upsert/deduplication by source/external id, URL, or title/company/location.
- Local deterministic embedding fallback and optional OpenAI embeddings.
- Optional OpenAI query parsing and match explanations with heuristic fallbacks.
- Hybrid ranking using semantic similarity, skill match, keyword match, and location match.
- Candidate profile creation.
- Profile-based recommendations.
- Save job and update application status.
- Next.js pages for home, search, recommendations/dashboard, profile, saved jobs, and job detail.

## 2. Architecture Overview

High-level architecture:

```mermaid
flowchart LR
  U["Browser / Next.js UI"] --> API["FastAPI backend"]
  API --> DB["SQL database via SQLAlchemy"]
  API --> Redis["Redis cache, optional"]
  API --> OpenAI["OpenAI, optional"]
  API --> Providers["Remotive / Adzuna / Greenhouse / Lever"]
  API --> LocalAI["Heuristic parser + local hash embeddings"]
```

Major modules:

- Backend API: `backend/app/main.py`
- Backend configuration: `backend/app/config.py`
- SQLAlchemy database setup: `backend/app/database.py`
- ORM models: `backend/app/models.py`
- Pydantic schemas: `backend/app/schemas.py`
- Services: `backend/app/services/*.py`
- Database migrations: `backend/migrations/`
- Frontend app routes: `frontend/app/`
- Frontend shared components: `frontend/components/`
- Frontend API client/profile storage: `frontend/lib/`
- CI: `.github/workflows/ci.yml`

Directory structure:

```text
.
|-- .github/workflows/ci.yml        GitHub Actions workflow
|-- backend/                        FastAPI application
|   |-- app/                        API, models, schemas, services
|   |-- data/sample_jobs.json       Local test/demo job payload
|   |-- migrations/                 Alembic migration environment and revisions
|   |-- scripts/ci_smoke.py         Backend smoke test
|   |-- alembic.ini                 Alembic config
|   `-- requirements.txt            Python dependencies
|-- frontend/                       Next.js app
|   |-- app/                        App Router pages and global layout/styles
|   |-- components/                 Reusable UI components
|   |-- lib/                        API client and local profile-id helpers
|   |-- package.json                Node scripts and dependencies
|   |-- package-lock.json           Locked npm dependency tree
|   |-- tailwind.config.ts          Tailwind content/theme config
|   |-- tsconfig.json               TypeScript config
|   |-- postcss.config.js           Tailwind/PostCSS config
|   `-- next.config.ts              Next.js config
|-- docker-compose.yml              Local Postgres and Redis
|-- README.md                       Setup and feature overview
|-- PRODUCT.md                      Product strategy and roadmap
`-- .gitignore                      Ignored local artifacts
```

Data flow:

1. Job data enters through `POST /jobs/import` as JSON or through external providers.
2. `JobIngestionService` normalizes provider payloads to `JobCreate`.
3. `_upsert_jobs` deduplicates, computes embeddings, stores jobs, and clears search/recommendation caches.
4. Search uses `AIService.parse_query`, SQLAlchemy filtering, optional PostgreSQL full-text filtering, embedding search, and `rank_jobs`.
5. Recommendations load a profile, ensure profile embedding, parse profile text into filters, rank all jobs, and cache results.
6. Frontend calls the API through `frontend/lib/api.ts` and stores only the active profile id in browser local storage.

Control flow:

- FastAPI dependency injection provides a SQLAlchemy `Session` via `get_db`.
- `Base.metadata.create_all(bind=engine)` runs at backend startup in `backend/app/main.py`.
- Alembic also defines the initial schema; production-like environments should prefer migrations.
- Frontend server components fetch search/job data directly through the API client.
- Client components manage form submission, local profile id, save/apply actions, and refresh behavior.

Important design patterns:

- Service layer for ingestion, AI, embeddings, cache, matching, text normalization, and vector search.
- Pydantic request/response schemas separate API contracts from ORM objects.
- Best-effort optional integrations: Redis and OpenAI failures fall back locally or no-op.
- Adapter-style `VectorSearchService` can be replaced by FAISS/Pinecone while preserving the ranking contract.

## 3. Technology Stack

| Technology | Where | Why used |
| --- | --- | --- |
| Python | `backend/` | Backend API and service logic. |
| FastAPI | `backend/app/main.py` | HTTP API, validation, OpenAPI docs, dependency injection. |
| SQLAlchemy 2 | `backend/app/database.py`, `models.py` | ORM, sessions, portable SQL access. |
| Pydantic 2 | `backend/app/schemas.py`, `config.py` | API schemas and settings. |
| Alembic | `backend/migrations/` | Database migrations. |
| PostgreSQL | `docker-compose.yml`, default `DATABASE_URL` | Primary persisted database and optional full-text search. |
| SQLite | CI env in `.github/workflows/ci.yml` | Lightweight smoke-test database. |
| Redis | `docker-compose.yml`, `cache.py` | Optional search/recommendation response caching. |
| OpenAI Python SDK | `ai.py`, `embeddings.py` | Optional LLM query parsing, match explanation, and embeddings. |
| httpx | `ingestion.py` | Async HTTP calls to job providers. |
| NumPy | `requirements.txt` | Installed dependency; not currently used directly by source files. |
| Next.js 16 | `frontend/app/` | Frontend app framework with App Router. |
| React 19 | `frontend/` | UI component model. |
| TypeScript | `frontend/*.ts`, `*.tsx` | Typed frontend code. |
| Tailwind CSS | `frontend/app/globals.css`, `tailwind.config.ts` | Utility/CSS styling pipeline. |
| lucide-react | Frontend components/layout | Icons. |
| Docker Compose | `docker-compose.yml` | Local Postgres and Redis infrastructure. |
| GitHub Actions | `.github/workflows/ci.yml` | CI for backend smoke test and frontend build. |
| npm | `frontend/package.json` | Frontend package manager/scripts. |
| pip | `backend/requirements.txt` | Backend package installation. |

## 4. Project Structure

### Root

- `README.md`: Human setup guide, feature overview, infrastructure notes, API docs URL, AI mode notes, and CI/CD notes.
- `PRODUCT.md`: Product thesis, target user, risk gaps, MVP journey, metrics, roadmap, research sprint, non-goals, and decision log. This is planning/product direction, not all implemented code.
- `docker-compose.yml`: Defines `postgres` and `redis` services with ports, volumes, credentials, and health checks.
- `.gitignore`: Excludes Python venv/cache/db files, Node/Next build artifacts, logs, env files, and editor/OS files.
- `.github/workflows/ci.yml`: Runs backend compile/smoke test and frontend build on pushes/pull requests to `master`.

### Backend

- `backend/app/main.py`: FastAPI app, CORS, route definitions, job import/search/detail, profile create/read, recommendations, save/apply/saved job endpoints.
- `backend/app/config.py`: `Settings` class and env variables.
- `backend/app/database.py`: SQLAlchemy engine/session/base setup.
- `backend/app/models.py`: ORM tables for jobs, profiles, applications, and saved jobs.
- `backend/app/schemas.py`: Pydantic schemas for jobs, searches, profiles, imports, applications, and stats.
- `backend/app/services/ai.py`: Optional OpenAI query parsing/explanations and heuristic fallbacks.
- `backend/app/services/embeddings.py`: Optional OpenAI embeddings and local hash-based embeddings.
- `backend/app/services/matching.py`: Serialization, embedding assurance, ranking, scoring, explanations.
- `backend/app/services/ingestion.py`: Provider connectors and normalization helpers.
- `backend/app/services/cache.py`: Optional Redis JSON cache.
- `backend/app/services/text.py`: CSV/tag/token/text helpers.
- `backend/app/services/vector_search.py`: Pure-Python cosine-similarity vector search adapter.
- `backend/data/sample_jobs.json`: Six sample jobs for import/demo/smoke test.
- `backend/migrations/env.py`: Alembic runtime configuration that uses `Settings.database_url`.
- `backend/migrations/versions/20260701_0001_initial.py`: Initial schema migration.
- `backend/scripts/ci_smoke.py`: API smoke test using FastAPI `TestClient`.
- `backend/alembic.ini`: Alembic defaults.
- `backend/requirements.txt`: Python dependency pins.

### Frontend

- `frontend/app/layout.tsx`: Global app shell, metadata, top navigation.
- `frontend/app/globals.css`: Tailwind directives and custom global styles.
- `frontend/app/page.tsx`: Home page with search box and workflow/example cards.
- `frontend/app/search/page.tsx`: Search results page, extracted filters, job stats, provider import control.
- `frontend/app/recommendations/page.tsx`: Client page that loads recommendations for stored profile id.
- `frontend/app/dashboard/page.tsx`: Re-exports recommendations page.
- `frontend/app/profile/page.tsx`: Profile creation form; stores returned profile id in local storage.
- `frontend/app/saved/page.tsx`: Saved/application tracker and status update buttons.
- `frontend/app/job/[id]/page.tsx`: Job detail page with source link.
- `frontend/app/jobs/[id]/page.tsx`: Duplicate job detail route without source link.
- `frontend/components/SearchBox.tsx`: Natural-language search form and navigation.
- `frontend/components/JobCard.tsx`: Result card, match explanation, score breakdown, save/apply/source actions.
- `frontend/components/ImportJobsButton.tsx`: Provider import UI.
- `frontend/lib/api.ts`: Typed frontend API wrapper.
- `frontend/lib/profile.ts`: Local-storage active profile id helper.
- `frontend/package.json`: Scripts, dependencies, and PostCSS override.
- `frontend/next.config.ts`: Enables `reactStrictMode`.
- `frontend/tsconfig.json`: Strict TypeScript and `@/*` path alias.
- `frontend/tailwind.config.ts`: Tailwind content scanning and brand colors.
- `frontend/postcss.config.js`: Tailwind and autoprefixer plugins.

## 5. Features

### Natural-Language Search

- Purpose: Let users search with phrases such as "senior AI PM remote jobs in APAC".
- How it works: `GET /jobs/search` calls `AIService.parse_query`; applies SQL filters; optionally applies PostgreSQL full-text search; ranks results with `rank_jobs`.
- Main files: `backend/app/main.py`, `backend/app/services/ai.py`, `backend/app/services/matching.py`, `frontend/app/search/page.tsx`, `frontend/components/SearchBox.tsx`.
- Dependencies: FastAPI, SQLAlchemy, optional OpenAI, Redis cache.
- Limitations: Heuristic parser is regex/token based; search falls back to all jobs when filters return none; PostgreSQL full-text clause is only used for Postgres; no user-editable filters in UI.

### Job Ingestion

- Purpose: Load job listings from local JSON or external providers.
- How it works: `POST /jobs/import` accepts a list of jobs or `JobImportRequest`; `JobIngestionService.fetch` normalizes provider results; `_upsert_jobs` deduplicates and stores embeddings.
- Main files: `backend/app/main.py`, `backend/app/services/ingestion.py`, `backend/data/sample_jobs.json`, `frontend/components/ImportJobsButton.tsx`.
- Dependencies: httpx, external provider APIs, optional Adzuna credentials.
- Limitations: No scheduled ingestion; provider controls are visible in the candidate search UI; provider freshness/health is not persisted; no stale-job expiration.

### Hybrid Ranking

- Purpose: Rank search/recommendation results by estimated fit.
- How it works: Combines semantic similarity, skill match, keyword match, and location match. Formula in `rank_jobs`: `0.5 * semantic + 0.2 * skill + 0.2 * keyword + 0.1 * location`, capped at `1.0`, returned as percentage.
- Main files: `backend/app/services/matching.py`, `backend/app/services/vector_search.py`, `backend/app/services/embeddings.py`.
- Dependencies: optional OpenAI embeddings, local hash embeddings, SQLAlchemy session.
- Limitations: Score is not calibrated; no ranking version stored; application `match_score` field exists but is not populated.

### Match Explanations

- Purpose: Explain why a job matched.
- How it works: OpenAI generates a short explanation when configured; otherwise a deterministic explanation is built from matched skills/location/seniority signals.
- Main files: `backend/app/services/ai.py`, `backend/app/services/matching.py`, `frontend/components/JobCard.tsx`.
- Dependencies: optional OpenAI chat model.
- Limitations: OpenAI errors are silently swallowed; local explanation is coarse.

### Profile Creation

- Purpose: Capture user skills, experience, preferred roles, location preference, and resume text.
- How it works: `POST /user/profile` always creates a new `UserProfile`, computes embedding, returns id; frontend stores id in local storage.
- Main files: `backend/app/main.py`, `backend/app/models.py`, `frontend/app/profile/page.tsx`, `frontend/lib/profile.ts`.
- Dependencies: SQLAlchemy, embeddings.
- Limitations: No edit/update route; no delete route; no auth/user ownership; repeated saves create new profiles.

### Recommendations

- Purpose: Rank all jobs against the active profile.
- How it works: `GET /recommendations/{user_id}` loads profile, ensures embedding, parses profile text into filters, overlays `location_preference`, ranks all jobs, caches response.
- Main files: `backend/app/main.py`, `backend/app/services/matching.py`, `frontend/app/recommendations/page.tsx`.
- Dependencies: profiles, jobs, embeddings, optional Redis/OpenAI.
- Limitations: Requires browser local-storage profile id; no onboarding guard beyond message; no dismiss/report feedback loop.

### Save and Application Tracking

- Purpose: Let users save jobs and track statuses.
- How it works: `POST /jobs/save` sets status `saved`; `POST /jobs/apply` upserts an `Application` with one of `saved`, `applied`, `interview`, `rejected`; `GET /jobs/saved/{user_id}` lists applications.
- Main files: `backend/app/main.py`, `backend/app/models.py`, `frontend/components/JobCard.tsx`, `frontend/app/saved/page.tsx`.
- Dependencies: `user_profiles`, `jobs`, `applications`, `saved_jobs`.
- Limitations: "Apply" button marks internal status only; no notes editing in UI; no follow-up dates; no `offer` or `withdrawn` status; no auth checks.

### Job Detail Pages

- Purpose: Show full job description, requirements, tags, and metadata.
- How it works: Server page fetches `GET /jobs/{id}`.
- Main files: `frontend/app/job/[id]/page.tsx`, `frontend/app/jobs/[id]/page.tsx`, `backend/app/main.py`.
- Dependencies: API availability at render time.
- Limitations: Duplicate routes diverge; `/job/[id]` includes source link, `/jobs/[id]` does not.

## 6. Data Models

Database tables are defined in `backend/app/models.py` and initial migration `backend/migrations/versions/20260701_0001_initial.py`.

### `jobs`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Indexed primary key. |
| `title` | string(255) | Required, indexed. |
| `company` | string(255) | Required, indexed. |
| `location` | string(255) | Required, indexed. |
| `salary` | string(120), nullable | Provider/sample text. |
| `description` | text | Required. |
| `requirements` | text | Required. |
| `tags` | text | JSON list stored as text by current helpers. |
| `seniority` | string(80), nullable | Indexed. |
| `remote` | boolean | Default false, indexed. |
| `url` | text, nullable | Original posting. |
| `external_id` | string(255), nullable | Provider id. |
| `source` | string(120) | Default `json`; unique with `external_id`. |
| `embedding` | text, nullable | JSON vector string. |
| `created_at`, `updated_at` | datetime | ORM defaults. |

Relationships:

- `Job.applications` to `Application`
- `Job.saved_by` to `SavedJob`

### `user_profiles`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Active id is stored in frontend local storage. |
| `name` | string(255) | Required. |
| `skills` | text | Comma-separated string. |
| `experience` | text | Free text. |
| `preferred_roles` | text | Comma-separated string. |
| `location_preference` | string(255) | Free text. |
| `resume_text` | text, nullable | Sensitive user data; no auth/deletion yet. |
| `embedding` | text, nullable | JSON vector string. |
| `created_at`, `updated_at` | datetime | ORM defaults. |

Relationships:

- `UserProfile.applications` to `Application`
- `UserProfile.saved_jobs` to `SavedJob`

### `applications`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Application row id. |
| `user_id` | FK `user_profiles.id` | Indexed. |
| `job_id` | FK `jobs.id` | Indexed. |
| `status` | string(40) | Validated in route as `saved`, `applied`, `interview`, or `rejected`. |
| `notes` | text, nullable | API accepts notes; UI does not edit them. |
| `match_score` | float, nullable | Present but not written by ranking/save/apply logic. |
| `created_at`, `updated_at` | datetime | ORM defaults. |

Constraints:

- Unique `(user_id, job_id)` as `uq_user_job`.

### `saved_jobs`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Saved row id. |
| `user_id` | FK `user_profiles.id` | Indexed in model, no explicit migration index besides FK table definition. |
| `job_id` | FK `jobs.id` | Indexed in model, no explicit migration index besides FK table definition. |
| `created_at` | datetime | ORM default. |

Constraints:

- Unique `(user_id, job_id)` as `uq_saved_user_job`.

Validation rules:

- Pydantic request schemas require core job/profile fields.
- `JobImportRequest.limit` is `1..200`.
- Search `limit` and recommendations `limit` are `1..50`.
- `GET /jobs/search` requires `query` length at least 2.
- `POST /jobs/apply` manually restricts status values.

Migrations:

- One initial Alembic revision: `20260701_0001_initial.py`.
- `backend/app/main.py` also calls `Base.metadata.create_all`, which can hide missing migration application in development.

## 7. API Documentation

FastAPI interactive docs are available at `/docs` when the backend is running.

### `GET /health`

- Input: none.
- Output: `{"status": "ok"}`.
- Auth: none.
- Errors: none expected.

### `GET /jobs/stats`

- Input: none.
- Output: `JobStats`.
- Example response:

```json
{
  "total": 6,
  "by_source": { "sample": 6 },
  "providers": {
    "remotive": true,
    "adzuna": false,
    "greenhouse": true,
    "lever": true
  }
}
```

### `POST /jobs/import`

- Input: either a JSON array of `JobCreate` or a `JobImportRequest`.
- Supported sources: `json`, `remotive`, `adzuna`, `greenhouse`, `lever`.
- Output: `ImportResponse`.
- Auth: none.
- Error handling:
  - `400` for unsupported source or missing required provider settings/company.
  - `502` for provider import failures.

Example JSON import:

```json
{
  "source": "json",
  "limit": 1,
  "jobs": [
    {
      "title": "AI Product Manager",
      "company": "ExampleCo",
      "location": "Remote",
      "description": "Own AI product workflows.",
      "requirements": "Product management and AI experience.",
      "tags": ["AI", "Product Management"],
      "remote": true,
      "source": "json"
    }
  ]
}
```

Example provider import:

```json
{ "source": "remotive", "query": "python", "limit": 25 }
```

### `GET /jobs/search`

- Query params:
  - `query`: required string, min length 2.
  - `limit`: optional integer, default 20, range 1..50.
- Output: `SearchResponse` with extracted filters and `JobMatch[]`.
- Auth: none.
- Error handling: schema/query validation via FastAPI; cache failures are ignored by service construction.

Example request:

```text
GET /jobs/search?query=senior%20AI%20PM%20remote%20jobs%20in%20APAC
```

### `GET /jobs/{job_id}`

- Path params: `job_id` integer.
- Output: `JobRead`.
- Auth: none.
- Errors: `404` if job not found.

### `POST /user/profile`

- Input: `UserProfileCreate`.
- Output: `UserProfileRead`.
- Auth: none.
- Important behavior: always creates a new profile; it does not update an existing active profile.

Example:

```json
{
  "name": "Ada Lovelace",
  "skills": ["AI", "Product Management"],
  "experience": "Built AI products.",
  "preferred_roles": ["AI Product Manager"],
  "location_preference": "Remote APAC",
  "resume_text": "Resume text..."
}
```

### `GET /user/profile/{user_id}`

- Path params: `user_id` integer.
- Output: `UserProfileRead`.
- Auth: none.
- Errors: `404` if profile not found.

### `GET /recommendations/{user_id}`

- Path params: `user_id` integer.
- Query params: `limit` optional integer, default 20, range 1..50.
- Output: `JobMatch[]`.
- Auth: none.
- Errors: `404` if profile not found.

### `POST /jobs/save`

- Input: `SaveJobRequest` with `user_id`, `job_id`, optional `notes`.
- Output: `ApplicationRead`.
- Auth: none.
- Errors: `404` for missing profile/job.

### `POST /jobs/apply`

- Input: `ApplyJobRequest` with `user_id`, `job_id`, `status`, optional `notes`.
- Output: `ApplicationRead`.
- Auth: none.
- Errors:
  - `400` if status is outside `saved`, `applied`, `interview`, `rejected`.
  - `404` for missing profile/job.

### `GET /jobs/saved/{user_id}`

- Path params: `user_id` integer.
- Output: `ApplicationRead[]`.
- Auth: none.
- Behavior: returns all applications for a profile ordered by `updated_at` descending.

## 8. Configuration

Backend settings in `backend/app/config.py`:

| Env var | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `AI Job Search System` | FastAPI title. |
| `DATABASE_URL` | `postgresql+psycopg2://jobsearch:jobsearch@localhost:5432/jobsearch` | SQLAlchemy database URL. |
| `REDIS_URL` | `redis://localhost:6379/0` | Optional Redis cache URL. |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | CORS allow-list. |
| `OPENAI_API_KEY` | unset | Enables OpenAI parser, embeddings, explanations. |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model. |
| `OPENAI_CHAT_MODEL` | `gpt-4.1-mini` | Chat model. |
| `ADZUNA_APP_ID` | unset | Required for Adzuna ingestion. |
| `ADZUNA_APP_KEY` | unset | Required for Adzuna ingestion. |
| `ADZUNA_COUNTRY` | `us` | Adzuna country endpoint. |

Frontend settings:

| Env var | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | API base URL used by `frontend/lib/api.ts`. |

Configuration files:

- `docker-compose.yml`: Postgres/Redis local infrastructure.
- `backend/alembic.ini`: Alembic config, overridden at runtime by `Settings.database_url`.
- `frontend/next.config.ts`: Next config.
- `frontend/tsconfig.json`: TypeScript config.
- `frontend/tailwind.config.ts`: Tailwind config.
- `frontend/postcss.config.js`: PostCSS config.

Secrets required:

- `OPENAI_API_KEY` for AI mode.
- `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` for Adzuna.
- Database/Redis credentials for deployed environments.

Feature flags:

- No explicit feature-flag system exists.
- Optional behavior is controlled by presence/absence of OpenAI, Adzuna, Redis, and database configuration.

Notable config gap:

- `README.md` references `backend/.env.example`, but that file is not present in the repository file list.

## 9. Build & Run Instructions

### Local infrastructure

```powershell
docker compose up -d
```

Starts:

- PostgreSQL at `localhost:5432`
- Redis at `localhost:6379`

### Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

If no `.env` is present, defaults point to local Docker Postgres/Redis.

### Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Import sample jobs

PowerShell example from repo root after backend is running:

```powershell
$body = Get-Content backend\data\sample_jobs.json -Raw
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs/import -ContentType application/json -Body $body
```

### Import real jobs

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs/import -ContentType application/json -Body '{"source":"remotive","query":"python","limit":25}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs/import -ContentType application/json -Body '{"source":"greenhouse","company":"airbnb","limit":25}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs/import -ContentType application/json -Body '{"source":"lever","company":"netlify","limit":25}'
```

Adzuna requires credentials.

### Testing

Backend smoke test:

```powershell
cd backend
$env:DATABASE_URL="sqlite:///./ci_test.db"
$env:REDIS_URL="redis://127.0.0.1:6379/0"
python scripts/ci_smoke.py
```

Backend compile check:

```powershell
cd backend
python -m compileall app
```

Frontend build:

```powershell
cd frontend
npm run build
```

### Production build/deployment

- Frontend CI runs `npm ci` and `npm run build`.
- Backend CI installs `requirements.txt`, compiles `app`, and runs smoke test.
- `README.md` says Railway and Vercel are connected to `master`, but deployment config files for those platforms are not present in the repository.

## 10. Dependencies

External services:

- PostgreSQL database.
- Redis cache, optional.
- OpenAI API, optional.
- Remotive public API.
- Adzuna API with credentials.
- Greenhouse job board API.
- Lever postings API.

Critical backend packages:

- `fastapi`, `uvicorn`: API server.
- `sqlalchemy`, `psycopg2-binary`, `alembic`: persistence and migrations.
- `pydantic`, `pydantic-settings`: schemas/settings.
- `openai`: optional AI calls.
- `httpx`: provider ingestion.
- `redis`: optional caching.

Critical frontend packages:

- `next`, `react`, `react-dom`: app framework/runtime.
- `typescript`: static typing.
- `tailwindcss`, `autoprefixer`: styling.
- `lucide-react`: icons.

Internal dependencies:

- `main.py` depends on all backend service modules and models/schemas.
- `matching.py` depends on `AIService`, `EmbeddingService`, `VectorSearchService`, and text helpers.
- Frontend pages depend on `frontend/lib/api.ts`.
- Save/recommendation pages depend on `frontend/lib/profile.ts` local-storage id.

## 11. Important Decisions

Source-backed decisions evident in code/docs:

- Use FastAPI and Next.js: implements a separate API/backend and UI/frontend split.
- Use Postgres as default database and SQLite for CI smoke testing: seen in defaults and CI env.
- Keep OpenAI optional: `AIService` and `EmbeddingService` instantiate clients only when `OPENAI_API_KEY` exists and fall back locally on errors.
- Keep Redis optional: `CacheService` disables itself if connection/ping fails.
- Store embeddings as JSON text: simple DB portability, but inefficient for large-scale vector search.
- Use a replaceable vector-search adapter: `VectorSearchService` comment explicitly says production can swap it for persisted FAISS or Pinecone.
- Treat product as candidate-controlled rather than autonomous applicant: documented in `PRODUCT.md`; current UI still has an "Apply" button that only marks internal status.
- Initial target is individual job seekers: documented in `PRODUCT.md`.

Tradeoffs:

- Optional fallbacks make local development easy but can hide production integration failures.
- `Base.metadata.create_all` simplifies startup but reduces migration discipline.
- Local-storage profile id avoids auth complexity but provides no security or multi-device continuity.
- Text/JSON storage for tags and embeddings is simple but not normalized or optimized.

Alternatives evident or mentioned:

- FAISS or Pinecone can replace current vector search adapter.
- Product roadmap proposes background ingestion/admin workflow instead of candidate-facing import controls.
- Product roadmap proposes one editable active profile before adding accounts.

## 12. Current State

Completed work:

- Backend API with core job/profile/recommendation/application routes.
- SQLAlchemy ORM models and first Alembic migration.
- External provider ingestion connectors.
- Search/recommendation ranking and explanations.
- Frontend pages and shared components for core flows.
- Local Docker infrastructure for Postgres/Redis.
- GitHub Actions CI for backend smoke and frontend build.
- Product direction and roadmap in `PRODUCT.md`.

Partially completed work:

- AI mode: implemented but optional; failures silently fallback.
- Caching: implemented but optional and best-effort.
- Application tracking: basic statuses only.
- Profile persistence: creation and read exist; update/delete do not.
- Provider ingestion: manual import exists; scheduling/health/freshness do not.
- Job details: duplicated routes exist with inconsistent source-link behavior.

TODO/FIXME search:

- No literal `TODO` or `FIXME` comments were found by `rg`.
- `pass` appears in legitimate fallback/empty-class/template contexts:
  - `backend/app/database.py` declarative base class.
  - `backend/app/schemas.py` empty subclass.
  - exception fallback blocks in `backend/app/services/ai.py` and `text.py`.
  - Alembic template.

Stub or missing implementations:

- Authentication and authorization.
- Profile update/delete.
- User accounts.
- Analytics/event tracking.
- Background ingestion.
- Dismiss/report jobs.
- Follow-up reminders.
- Saved search persistence.
- Ranking calibration/versioning.
- Privacy/data-use notice.

## 13. Known Issues

Bugs/behavioral risks:

- `POST /user/profile` creates a new profile every save; returning users can accumulate orphan profiles.
- `JobCard` button text says `Apply` while the action only marks the internal application status as applied.
- Duplicate frontend job detail routes may diverge: `/job/[id]` has a source link, `/jobs/[id]` does not.
- `README.md` references `backend/.env.example`, but no such file is present.
- OpenAI errors are swallowed, which makes AI production issues hard to observe.
- Redis errors disable caching silently.
- `Application.match_score` exists but is not populated.

Technical debt:

- `Base.metadata.create_all` is used alongside Alembic.
- Embeddings are stored as text JSON in the main jobs/profile tables.
- Tags and profile skills/roles are stored as text rather than normalized tables.
- Search SQL filtering uses broad OR logic and falls back to all jobs.
- Provider import UI is in the candidate search page.
- Browser `alert()` is used for save/apply feedback.

Security/privacy considerations:

- No authentication.
- No ownership checks on profile, saved jobs, applications, or recommendations.
- Resume text is accepted and stored without deletion controls.
- CORS allows local frontend origins only by default, but API endpoints themselves are unauthenticated.
- No rate limiting for provider imports or OpenAI-backed endpoints.

Performance concerns:

- Recommendations rank all jobs in memory.
- Vector search computes/loads job embeddings for all candidate jobs.
- Redis cache invalidation scans keys by pattern.
- Embedding storage and retrieval as JSON text does not scale well.

Edge cases:

- Provider APIs may change shape or fail; route returns `502`.
- Adzuna provider is unavailable without credentials.
- Heuristic query parser can misinterpret roles/locations.
- Server-rendered frontend pages depend on API availability at render time.

## 14. Testing

Existing tests/checks:

- `backend/scripts/ci_smoke.py` imports sample jobs, verifies stats/provider availability, and checks extracted filters for a sample query.
- `.github/workflows/ci.yml` compiles backend source with `python -m compileall app`.
- `.github/workflows/ci.yml` builds frontend with `npm run build`.

Coverage:

- Smoke-level backend API coverage only.
- No unit tests for ranking, ingestion normalization, cache behavior, profile/app workflows, or error cases.
- No frontend component/page tests.
- No end-to-end browser tests.

How to run:

```powershell
cd backend
$env:DATABASE_URL="sqlite:///./ci_test.db"
$env:REDIS_URL="redis://127.0.0.1:6379/0"
python scripts/ci_smoke.py
```

```powershell
cd frontend
npm run build
```

Missing tests to prioritize:

- `AIService._heuristic_parse` cases.
- `JobIngestionService` normalization for each provider with mocked responses.
- `_upsert_jobs` deduplication behavior.
- `rank_jobs` score ordering and breakdown.
- Profile creation/update once implemented.
- Save/apply status transitions and invalid statuses.
- Frontend saved/recommendation behavior with no profile id.

## 15. Developer Workflow

Recommended workflow:

1. Start local infrastructure with `docker compose up -d`.
2. Run backend with virtualenv and `uvicorn app.main:app --reload --port 8000`.
3. Run frontend with `npm run dev` in `frontend/`.
4. Import sample jobs before testing search/recommendations.
5. Create a profile in the UI before testing recommendations/save/apply.
6. Run backend smoke and frontend build before merging.

Coding conventions/patterns:

- Keep backend request/response shapes in `schemas.py`.
- Put business logic in `backend/app/services/` rather than growing route handlers.
- Use SQLAlchemy 2 typed ORM style in models.
- Use typed frontend API functions in `frontend/lib/api.ts`.
- Use the existing CSS class system in `frontend/app/globals.css` and lucide icons.
- Keep optional integrations resilient, but add observability for production.

Reusable utilities:

- `normalize_text`, `tokenize`, `tags_to_storage`, `tags_from_storage` in `text.py`.
- `dumps_vector`, `loads_vector`, `cosine_similarity` in `embeddings.py`.
- `serialize_job`, `profile_to_text`, `rank_jobs` in `matching.py`.
- `request<T>` in `frontend/lib/api.ts`.

Common pitfalls:

- Bracketed Next.js route paths need literal path handling in PowerShell.
- Saving a profile returns a new id; old saved jobs remain tied to the previous id.
- Search and recommendation pages need backend availability.
- CI uses SQLite, while default local/dev config uses Postgres.
- Product roadmap items in `PRODUCT.md` are not necessarily implemented.

## 16. Improvement Opportunities

Refactoring:

- Split `backend/app/main.py` into routers: jobs, profiles, recommendations, applications.
- Remove duplicate job detail route or make one redirect/re-export the other.
- Replace broad exception swallowing in AI/cache paths with structured logging.
- Move provider import UI to admin/operator flow.

Performance:

- Persist vector index or use pgvector/FAISS/Pinecone.
- Avoid ranking all jobs for recommendations.
- Add pagination to search and saved jobs.
- Replace Redis pattern scans with tracked cache key namespaces or versioned cache keys.

Maintainability:

- Add `.env.example`.
- Add test suite with pytest and mocked provider responses.
- Generate API client types from OpenAPI or keep frontend/backend schema contract tests.
- Add migration policy and remove startup `create_all` outside local-only mode.

Scalability:

- Add user accounts and ownership scoping.
- Add background ingestion jobs with provider health/freshness tables.
- Add stale job expiration.
- Store ranking impressions and user feedback for learning-to-rank experiments.

Product:

- Rename `Apply` to `Mark applied` and make source opening the primary application action.
- Add active profile edit/delete.
- Add guided onboarding.
- Add notes, next-action date, follow-up reminders, and more pipeline statuses.

## 17. Handoff Guide for Another AI Coding Agent

Project objective:

- Build a trustworthy candidate-controlled AI job search workspace that imports listings, ranks them against searches/profiles, explains matches, and tracks pursuit status.

Current progress:

- Core prototype works end-to-end: import jobs, search, create profile, get recommendations, save/apply, view saved jobs.
- Product roadmap identifies the next high-risk fixes.

Remaining high-priority tasks:

1. Correct application semantics: rename UI action to `Mark applied`; keep `Apply on source` as external source link.
2. Implement persistent editable active profile and profile deletion.
3. Add authentication/ownership checks before public usage.
4. Move ingestion out of candidate search UI or clearly mark it as admin/development.
5. Add tests around ranking, ingestion, and application/profile flows.

High-priority files:

- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/services/matching.py`
- `backend/app/services/ingestion.py`
- `frontend/lib/api.ts`
- `frontend/components/JobCard.tsx`
- `frontend/app/profile/page.tsx`
- `frontend/app/saved/page.tsx`
- `frontend/app/search/page.tsx`
- `PRODUCT.md`

Files safe to modify:

- Frontend pages/components/lib files for UX changes.
- Backend service modules for parsing/ranking/ingestion improvements.
- `schemas.py` and `models.py` when paired with a migration.
- Tests/scripts under `backend/scripts/` or a new test directory.

Files requiring caution:

- `backend/migrations/versions/20260701_0001_initial.py`: Do not edit after environments have applied it; add a new migration.
- `backend/app/models.py`: Schema changes require migration and API/schema updates.
- `frontend/package-lock.json`: Let npm update it, avoid hand edits.
- `docker-compose.yml`: Changes affect local developer setup.
- `PRODUCT.md`: Product direction, not code; preserve distinction between planned and implemented.

Recommended implementation order:

1. Add `.env.example`.
2. Fix application semantics in UI and API names if desired.
3. Add profile update/delete routes and load existing profile in UI.
4. Consolidate duplicate job detail route.
5. Add auth/ownership model.
6. Add pytest tests and provider mocks.
7. Add background ingestion and provider health.
8. Improve vector storage/search.

Important assumptions:

- The current single-user-ish local-storage model is only acceptable for private/local use.
- `PRODUCT.md` describes direction; code is the source of truth for implemented behavior.
- OpenAI and Redis must remain optional unless product/deployment requirements change.
- The app should not claim it submitted an external job application.

Project conventions:

- Keep API models in Pydantic schemas.
- Keep reusable backend logic in services.
- Keep frontend API access centralized in `frontend/lib/api.ts`.
- Use existing visual language and class names unless doing a broader UI pass.

## 18. Resume Prompt

Use this prompt to continue development:

```text
You are continuing work on `job_search_agent`, a FastAPI + Next.js AI job search workspace.

Current architecture:
- Backend is in `backend/app/` with `main.py` routes, SQLAlchemy models in `models.py`, Pydantic schemas in `schemas.py`, settings in `config.py`, and service modules for AI parsing/explanations, embeddings, matching, ingestion, Redis cache, text helpers, and vector search.
- Frontend is in `frontend/` using Next.js App Router, React, TypeScript, Tailwind/global CSS, lucide-react icons, API helpers in `frontend/lib/api.ts`, and local profile id storage in `frontend/lib/profile.ts`.
- Local infra is `docker-compose.yml` with Postgres and Redis. CI is `.github/workflows/ci.yml`, running backend smoke test and frontend build.

Implemented behavior:
- `POST /jobs/import` imports JSON, Remotive, Adzuna, Greenhouse, or Lever jobs and upserts them.
- `GET /jobs/search` parses natural-language filters, searches jobs, ranks with semantic/skill/keyword/location scoring, and returns explanations.
- `POST /user/profile` creates a new profile and embedding.
- `GET /recommendations/{user_id}` ranks jobs against a profile.
- `POST /jobs/save`, `POST /jobs/apply`, and `GET /jobs/saved/{user_id}` support basic saved/application tracking.
- Frontend has home, search, recommendations/dashboard, profile, saved, and job detail pages.

Important constraints:
- Base statements on code, not roadmap claims.
- Preserve optional OpenAI and Redis fallbacks.
- Do not imply the app submits external applications.
- Schema changes require Alembic migrations.
- Use existing service-layer and frontend API-client patterns.

High-priority next tasks:
1. Rename/fix application UI semantics: `Apply` should become `Mark applied`; source link should be the external application path.
2. Add editable/deletable active profile instead of always creating new profiles.
3. Consolidate duplicate job detail routes: `frontend/app/job/[id]/page.tsx` and `frontend/app/jobs/[id]/page.tsx`.
4. Add `.env.example`.
5. Add tests for profile flow, save/apply statuses, ranking, and ingestion normalization.

Key files:
- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/services/matching.py`
- `backend/app/services/ingestion.py`
- `frontend/lib/api.ts`
- `frontend/components/JobCard.tsx`
- `frontend/app/profile/page.tsx`
- `frontend/app/saved/page.tsx`
- `frontend/app/search/page.tsx`
- `PRODUCT.md`

Before finishing, run:
- Backend smoke test with SQLite if backend logic changed.
- `npm run build` if frontend changed.
```

## 19. File Map

| File path | Purpose | Key classes/functions | Dependencies |
| --- | --- | --- | --- |
| `README.md` | Setup/features overview | n/a | Project code/docs |
| `PRODUCT.md` | Product strategy/roadmap | n/a | Product decisions |
| `docker-compose.yml` | Local Postgres/Redis | `postgres`, `redis` services | Docker |
| `.gitignore` | Ignore local artifacts | n/a | Git |
| `.github/workflows/ci.yml` | CI workflow | `backend`, `frontend` jobs | GitHub Actions, Python, Node |
| `backend/requirements.txt` | Backend deps | n/a | pip |
| `backend/alembic.ini` | Alembic config | n/a | Alembic |
| `backend/app/__init__.py` | Package marker | n/a | Python |
| `backend/app/config.py` | App settings | `Settings`, `get_settings` | pydantic-settings |
| `backend/app/database.py` | DB engine/session/base | `Base`, `engine`, `SessionLocal`, `get_db` | SQLAlchemy |
| `backend/app/models.py` | ORM schema | `Job`, `UserProfile`, `Application`, `SavedJob` | SQLAlchemy |
| `backend/app/schemas.py` | API schemas | `JobCreate`, `JobRead`, `JobMatch`, `SearchFilters`, `UserProfileCreate`, `ApplicationRead`, `JobImportRequest`, `JobStats` | Pydantic |
| `backend/app/main.py` | FastAPI app/routes | `health`, `job_stats`, `import_jobs`, `search_jobs`, `get_job`, `upsert_profile`, `get_profile`, `recommendations`, `save_job`, `apply_job`, `saved_jobs` | FastAPI, SQLAlchemy, services |
| `backend/app/services/__init__.py` | Package marker | n/a | Python |
| `backend/app/services/ai.py` | Query parsing/explanations | `AIService`, `_heuristic_parse` | OpenAI, regex, schemas |
| `backend/app/services/embeddings.py` | Embedding utilities | `EmbeddingService`, `dumps_vector`, `loads_vector`, `cosine_similarity` | OpenAI, hashlib, math |
| `backend/app/services/matching.py` | Ranking and serialization | `rank_jobs`, `serialize_job`, `job_to_text`, `profile_to_text`, `ensure_job_embedding`, `ensure_profile_embedding` | Models, schemas, AI, embeddings |
| `backend/app/services/ingestion.py` | Provider import adapters | `JobIngestionService`, `_remotive`, `_adzuna`, `_greenhouse`, `_lever` | httpx, settings, schemas |
| `backend/app/services/cache.py` | Redis cache wrapper | `CacheService` | redis |
| `backend/app/services/text.py` | Text/list helpers | `split_csv`, `list_to_csv`, `tags_from_storage`, `tags_to_storage`, `tokenize`, `normalize_text` | json, regex |
| `backend/app/services/vector_search.py` | Vector search adapter | `VectorSearchService.search` | embeddings, models |
| `backend/data/sample_jobs.json` | Demo/test jobs | n/a | Import API |
| `backend/migrations/env.py` | Alembic environment | `run_migrations_offline`, `run_migrations_online` | Alembic, SQLAlchemy, settings |
| `backend/migrations/script.py.mako` | Alembic revision template | n/a | Alembic |
| `backend/migrations/versions/20260701_0001_initial.py` | Initial schema migration | `upgrade`, `downgrade` | Alembic, SQLAlchemy |
| `backend/scripts/ci_smoke.py` | Backend smoke test | FastAPI `TestClient` flow | app, sample jobs |
| `frontend/package.json` | Frontend scripts/deps | `dev`, `build`, `start`, `lint` scripts | npm |
| `frontend/package-lock.json` | Locked deps | n/a | npm |
| `frontend/next.config.ts` | Next config | `nextConfig` | Next.js |
| `frontend/tsconfig.json` | TypeScript config | path alias `@/*` | TypeScript, Next |
| `frontend/tailwind.config.ts` | Tailwind config | `config` | Tailwind |
| `frontend/postcss.config.js` | PostCSS config | Tailwind/autoprefixer plugins | PostCSS |
| `frontend/next-env.d.ts` | Next type declarations | n/a | Next.js |
| `frontend/app/layout.tsx` | Root layout/nav | `RootLayout`, metadata | Next, lucide-react |
| `frontend/app/globals.css` | Global CSS | CSS classes and variables | Tailwind |
| `frontend/app/page.tsx` | Home page | `HomePage` | SearchBox |
| `frontend/app/search/page.tsx` | Search results | `SearchPage` | JobCard, ImportJobsButton, SearchBox, API |
| `frontend/app/dashboard/page.tsx` | Dashboard alias | default re-export | Recommendations page |
| `frontend/app/profile/page.tsx` | Profile form | `ProfilePage`, `split` | API, local storage |
| `frontend/app/recommendations/page.tsx` | Recommendations UI | `RecommendationsPage`, `load` | API, profile helper, JobCard |
| `frontend/app/saved/page.tsx` | Saved/application tracker | `SavedPage`, `load`, `update` | API, profile helper |
| `frontend/app/job/[id]/page.tsx` | Job detail route | `JobDetailPage` | API, lucide-react |
| `frontend/app/jobs/[id]/page.tsx` | Duplicate job detail route | `JobDetailPage` | API, lucide-react |
| `frontend/components/SearchBox.tsx` | Search form | `SearchBox`, `onSubmit` | Next router |
| `frontend/components/JobCard.tsx` | Job result card | `JobCard`, `handleSave`, `handleApply` | API, profile helper, lucide-react |
| `frontend/components/ImportJobsButton.tsx` | Provider import control | `ImportJobsButton`, `importJobs` | API, Next router |
| `frontend/lib/api.ts` | Typed API client | `request`, `searchJobs`, `importRealJobs`, `getJobStats`, `getJob`, `saveProfile`, `getRecommendations`, `saveJob`, `applyJob`, `getSavedJobs` | fetch |
| `frontend/lib/profile.ts` | Local profile id storage | `getStoredProfileId`, `storeProfileId` | browser localStorage |

## 20. Overall Assessment

Project maturity:

- Solid prototype/private-beta foundation.
- End-to-end core flow exists, but public-production requirements are incomplete.

Code quality:

- Clear module boundaries and readable service abstractions.
- Backend schemas/models are straightforward.
- Frontend is compact and consistent.
- Main route file is becoming dense and should be split as features grow.

Maintainability:

- Good enough for continued rapid iteration.
- Needs tests, logging, route organization, and migration discipline.
- Product/code distinction is important because `PRODUCT.md` includes future plans.

Risks:

- Privacy/security risk from unauthenticated resume/profile/application data.
- Trust risk from application semantics.
- Data quality risk from manual ingestion and provider variability.
- Scale risk from in-memory ranking and text-stored embeddings.
- Maintenance risk from duplicated job detail routes and missing `.env.example`.

Suggested roadmap:

1. Trust fixes: application semantics, source link prominence, profile update/delete.
2. Safety baseline: auth, ownership checks, privacy/deletion.
3. Reliability: tests, logging, `.env.example`, route splitting.
4. Product workflow: guided onboarding, richer application tracker, dismiss/report.
5. Data operations: background ingestion, provider health, stale job expiry.
6. Ranking scale: vector index, ranking versioning, feedback instrumentation.
