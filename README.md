# AI Job Search System

An AI-powered job search web app with a FastAPI backend, PostgreSQL persistence, Redis caching, hybrid search, profile-based recommendations, real job ingestion connectors, and a Next.js + Tailwind frontend.

Product strategy, success metrics, and the prioritized delivery plan are maintained in [PRODUCT.md](PRODUCT.md).

## What is included

- Natural-language job search with structured filter extraction
- Real job ingestion from Remotive, Adzuna, Greenhouse boards, and Lever boards
- JSON import for local development and controlled tests
- Profile storage with skills, experience, preferred roles, location, and resume text
- OpenAI-powered query parsing, embeddings, and explanations with deterministic local fallbacks
- Hybrid ranking formula: semantic similarity, skill match, keyword match, and location match
- Save/apply tracking with statuses: `saved`, `applied`, `interview`, `rejected`
- Clean SaaS-style Next.js UI for search, job details, profile, saved jobs, and recommendations

## Project layout

```text
backend/
  app/
    main.py
    database.py
    models.py
    schemas.py
    services/
  data/sample_jobs.json
  migrations/
  requirements.txt
  .env.example
frontend/
  app/
  components/
  lib/
  package.json
```

## Infrastructure

Start production-like services:

```powershell
docker compose up -d
```

PostgreSQL runs on `localhost:5432`, Redis on `localhost:6379`.

## Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Import real jobs:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs/import -ContentType application/json -Body '{"source":"remotive","query":"python","limit":25}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs/import -ContentType application/json -Body '{"source":"greenhouse","company":"airbnb","limit":25}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs/import -ContentType application/json -Body '{"source":"lever","company":"netlify","limit":25}'
```

Adzuna requires `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in `backend/.env`.

Import local test jobs:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/jobs/import -ContentType application/json -Body (Get-Content .\data\sample_jobs.json -Raw)
```

Open API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## AI mode

Production should use OpenAI for query understanding, embeddings, and RAG-style explanations:

```env
OPENAI_API_KEY=your_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

When configured, the backend uses OpenAI for query understanding, embeddings, and explanation generation. Local fallbacks remain available for offline development.

## Notes

- `POST /jobs/import` supports real provider ingestion and JSON payloads.
- Vector search is implemented behind a FAISS-compatible adapter with a pure-Python fallback; the adapter can be replaced by a persisted FAISS or Pinecone index.
- PostgreSQL full-text search is used automatically when `DATABASE_URL` points at Postgres.

## CI/CD

GitHub Actions runs backend smoke checks and a production frontend build for every push and pull request to `master`.
Railway and Vercel are connected to the same GitHub branch and deploy new commits automatically.
