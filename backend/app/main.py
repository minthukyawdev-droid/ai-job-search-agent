from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app import models
from app.config import get_settings
from app.database import Base, engine, get_db
from app.schemas import (
    ApplicationRead,
    ApplyJobRequest,
    ImportResponse,
    JobCreate,
    JobImportRequest,
    JobMatch,
    JobRead,
    JobStats,
    SaveJobRequest,
    SearchResponse,
    UserProfileCreate,
    UserProfileRead,
)
from app.services.ai import AIService
from app.services.cache import CacheService
from app.services.embeddings import EmbeddingService, dumps_vector
from app.services.ingestion import JobIngestionService
from app.services.matching import ensure_profile_embedding, profile_to_text, rank_jobs, serialize_job
from app.services.text import list_to_csv, normalize_text, tags_to_storage


settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs/stats", response_model=JobStats)
def job_stats(db: Session = Depends(get_db)) -> JobStats:
    rows = db.execute(
        select(models.Job.source, func.count(models.Job.id))
        .group_by(models.Job.source)
        .order_by(models.Job.source)
    ).all()
    by_source = {str(source): int(count) for source, count in rows}
    return JobStats(total=sum(by_source.values()), by_source=by_source)


@app.post("/jobs/import", response_model=ImportResponse)
async def import_jobs(
    payload: list[JobCreate] | JobImportRequest = Body(...),
    db: Session = Depends(get_db),
) -> ImportResponse:
    if isinstance(payload, list):
        request = JobImportRequest(source="json", jobs=payload, limit=len(payload) or 1)
    else:
        request = payload
    try:
        imported_payload = await JobIngestionService().fetch(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not import jobs from {request.source}: {exc}") from exc

    jobs, updated = _upsert_jobs(db, imported_payload.jobs)
    CacheService().delete_pattern("search:*")
    CacheService().delete_pattern("recommendations:*")
    return ImportResponse(source=request.source, imported=len(jobs) - updated, updated=updated, jobs=[serialize_job(job) for job in jobs])


def _upsert_jobs(db: Session, payload: list[JobCreate]) -> tuple[list[models.Job], int]:
    embeddings = EmbeddingService()
    imported: list[models.Job] = []
    updated = 0
    for item in payload:
        existing = None
        if item.external_id:
            existing = db.scalar(select(models.Job).where(models.Job.source == item.source, models.Job.external_id == item.external_id))
        if not existing and item.url:
            existing = db.scalar(select(models.Job).where(models.Job.url == item.url))
        if not existing:
            existing = db.scalar(
                select(models.Job).where(
                    models.Job.title == item.title,
                    models.Job.company == item.company,
                    models.Job.location == item.location,
                )
            )
        job_text = normalize_text(item.title, item.company, item.location, item.description, item.requirements, ", ".join(item.tags))
        vector = dumps_vector(embeddings.embed(job_text))
        if existing:
            updated += 1
            existing.salary = item.salary
            existing.description = item.description
            existing.requirements = item.requirements
            existing.tags = tags_to_storage(item.tags)
            existing.seniority = item.seniority
            existing.remote = item.remote
            existing.url = item.url
            existing.external_id = item.external_id
            existing.source = item.source
            existing.embedding = vector
            imported.append(existing)
        else:
            imported.append(
                models.Job(
                    title=item.title,
                    company=item.company,
                    location=item.location,
                    salary=item.salary,
                    description=item.description,
                    requirements=item.requirements,
                    tags=tags_to_storage(item.tags),
                    seniority=item.seniority,
                    remote=item.remote,
                    url=item.url,
                    external_id=item.external_id,
                    source=item.source,
                    embedding=vector,
                )
            )
    db.add_all(imported)
    db.commit()
    for job in imported:
        db.refresh(job)
    return imported, updated


@app.get("/jobs/search", response_model=SearchResponse)
def search_jobs(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> SearchResponse:
    cache = CacheService()
    cache_key = f"search:{query}:{limit}"
    cached = cache.get_json(cache_key)
    if cached:
        return SearchResponse.model_validate(cached)
    ai = AIService()
    embeddings = EmbeddingService()
    filters = ai.parse_query(query)
    stmt = select(models.Job)

    clauses = []
    if filters.location:
        clauses.append(models.Job.location.ilike(f"%{filters.location}%"))
    if filters.seniority:
        clauses.append(models.Job.seniority.ilike(f"%{filters.seniority}%"))
    if filters.remote is True:
        clauses.append(models.Job.remote.is_(True))
    if filters.role:
        role_query = f"%{filters.role}%"
        clauses.append(or_(models.Job.title.ilike(role_query), models.Job.description.ilike(role_query)))
    if clauses:
        stmt = stmt.where(or_(*clauses))
    if db.bind and db.bind.dialect.name == "postgresql":
        document = func.to_tsvector(
            "english",
            func.concat_ws(" ", models.Job.title, models.Job.company, models.Job.description, models.Job.requirements, models.Job.tags),
        )
        stmt = stmt.where(document.op("@@")(func.plainto_tsquery("english", query)))

    jobs = list(db.scalars(stmt).all())
    if not jobs:
        jobs = list(db.scalars(select(models.Job)).all())

    query_text = normalize_text(query, filters.role, " ".join(filters.skills), filters.location, filters.seniority)
    ranked = rank_jobs(db, jobs, embeddings.embed(query_text), filters, limit=limit)
    response = SearchResponse(filters=filters, results=ranked)
    cache.set_json(cache_key, response.model_dump(), ttl_seconds=180)
    return response


@app.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobRead:
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(job)


@app.post("/user/profile", response_model=UserProfileRead)
def upsert_profile(payload: UserProfileCreate, db: Session = Depends(get_db)) -> UserProfileRead:
    embeddings = EmbeddingService()
    profile = models.UserProfile(
        name=payload.name,
        skills=list_to_csv(payload.skills),
        experience=payload.experience,
        preferred_roles=list_to_csv(payload.preferred_roles),
        location_preference=payload.location_preference,
        resume_text=payload.resume_text,
    )
    profile.embedding = dumps_vector(embeddings.embed(profile_to_text(profile)))
    db.add(profile)
    db.commit()
    db.refresh(profile)
    CacheService().delete_pattern(f"recommendations:{profile.id}:*")
    return _profile_read(profile)


@app.get("/user/profile/{user_id}", response_model=UserProfileRead)
def get_profile(user_id: int, db: Session = Depends(get_db)) -> UserProfileRead:
    profile = db.get(models.UserProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _profile_read(profile)


@app.get("/recommendations/{user_id}", response_model=list[JobMatch])
def recommendations(user_id: int, limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    cache = CacheService()
    cache_key = f"recommendations:{user_id}:{limit}"
    cached = cache.get_json(cache_key)
    if cached:
        return [JobMatch.model_validate(item) for item in cached]
    profile = db.get(models.UserProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    embeddings = EmbeddingService()
    profile_vector = ensure_profile_embedding(db, profile, embeddings)
    filters = AIService().parse_query(profile_to_text(profile))
    if profile.location_preference:
        filters.location = profile.location_preference
    jobs = list(db.scalars(select(models.Job)).all())
    ranked = rank_jobs(db, jobs, profile_vector, filters, limit=limit, profile_context=profile_to_text(profile))
    cache.set_json(cache_key, [item.model_dump() for item in ranked], ttl_seconds=300)
    return ranked


@app.post("/jobs/save", response_model=ApplicationRead)
def save_job(payload: SaveJobRequest, db: Session = Depends(get_db)) -> ApplicationRead:
    return _upsert_application(db, payload.user_id, payload.job_id, "saved", payload.notes)


@app.post("/jobs/apply", response_model=ApplicationRead)
def apply_job(payload: ApplyJobRequest, db: Session = Depends(get_db)) -> ApplicationRead:
    valid_statuses = {"saved", "applied", "interview", "rejected"}
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {sorted(valid_statuses)}")
    return _upsert_application(db, payload.user_id, payload.job_id, payload.status, payload.notes)


@app.get("/jobs/saved/{user_id}", response_model=list[ApplicationRead])
def saved_jobs(user_id: int, db: Session = Depends(get_db)) -> list[ApplicationRead]:
    rows = db.scalars(
        select(models.Application)
        .options(joinedload(models.Application.job))
        .where(models.Application.user_id == user_id)
        .order_by(models.Application.updated_at.desc())
    ).all()
    return [_application_read(row) for row in rows]


def _upsert_application(db: Session, user_id: int, job_id: int, status: str, notes: str | None) -> models.Application:
    if not db.get(models.UserProfile, user_id):
        raise HTTPException(status_code=404, detail="Profile not found")
    if not db.get(models.Job, job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    saved = db.scalar(select(models.SavedJob).where(models.SavedJob.user_id == user_id, models.SavedJob.job_id == job_id))
    if not saved:
        db.add(models.SavedJob(user_id=user_id, job_id=job_id))
    application = db.scalar(
        select(models.Application).where(
            models.Application.user_id == user_id,
            models.Application.job_id == job_id,
        )
    )
    if application:
        application.status = status
        application.notes = notes if notes is not None else application.notes
    else:
        application = models.Application(user_id=user_id, job_id=job_id, status=status, notes=notes)
    db.add(application)
    db.commit()
    saved = db.scalar(
        select(models.Application)
        .options(joinedload(models.Application.job))
        .where(models.Application.id == application.id)
    )
    if not saved:
        raise HTTPException(status_code=500, detail="Could not persist application")
    return _application_read(saved)


def _profile_read(profile: models.UserProfile) -> UserProfileRead:
    return UserProfileRead(
        id=profile.id,
        name=profile.name,
        skills=[item.strip() for item in profile.skills.split(",") if item.strip()],
        experience=profile.experience,
        preferred_roles=[item.strip() for item in profile.preferred_roles.split(",") if item.strip()],
        location_preference=profile.location_preference,
        resume_text=profile.resume_text,
    )


def _application_read(application: models.Application) -> ApplicationRead:
    return ApplicationRead(
        id=application.id,
        user_id=application.user_id,
        job_id=application.job_id,
        status=application.status,
        notes=application.notes,
        match_score=application.match_score,
        job=serialize_job(application.job),
    )
