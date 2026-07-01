from sqlalchemy.orm import Session

from app import models
from app.schemas import JobMatch, JobRead, SearchFilters
from app.services.ai import AIService
from app.services.embeddings import EmbeddingService, cosine_similarity, dumps_vector, loads_vector
from app.services.text import normalize_text, tags_from_storage, tokenize
from app.services.vector_search import VectorSearchService


def job_to_text(job: models.Job) -> str:
    return normalize_text(job.title, job.company, job.location, job.description, job.requirements, ", ".join(tags_from_storage(job.tags)), job.url)


def profile_to_text(profile: models.UserProfile) -> str:
    return normalize_text(profile.skills, profile.experience, profile.preferred_roles, profile.location_preference, profile.resume_text)


def ensure_job_embedding(db: Session, job: models.Job, embeddings: EmbeddingService) -> list[float]:
    vector = loads_vector(job.embedding)
    if vector is None:
        vector = embeddings.embed(job_to_text(job))
        job.embedding = dumps_vector(vector)
        db.add(job)
        db.commit()
        db.refresh(job)
    return vector


def ensure_profile_embedding(db: Session, profile: models.UserProfile, embeddings: EmbeddingService) -> list[float]:
    vector = loads_vector(profile.embedding)
    if vector is None:
        vector = embeddings.embed(profile_to_text(profile))
        profile.embedding = dumps_vector(vector)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return vector


def serialize_job(job: models.Job) -> JobRead:
    return JobRead(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        salary=job.salary,
        description=job.description,
        requirements=job.requirements,
        tags=tags_from_storage(job.tags),
        seniority=job.seniority,
        remote=job.remote,
        url=job.url,
        external_id=job.external_id,
        source=job.source,
    )


def rank_jobs(
    db: Session,
    jobs: list[models.Job],
    query_vector: list[float],
    filters: SearchFilters,
    limit: int = 20,
    profile_context: str = "",
) -> list[JobMatch]:
    embeddings = EmbeddingService()
    ai = AIService()
    wanted_skills = {skill.lower() for skill in filters.skills}
    results: list[JobMatch] = []
    vector_rows = [(job, ensure_job_embedding(db, job, embeddings)) for job in jobs]
    semantic_scores = {job.id: score for job, score in VectorSearchService().search(query_vector, vector_rows, max(limit * 5, len(vector_rows)))}

    for job in jobs:
        text = job_to_text(job)
        text_tokens = set(tokenize(text))
        semantic = semantic_scores.get(job.id, 0.0)

        matched_skills = []
        for skill in wanted_skills:
            skill_tokens = set(tokenize(skill))
            if skill_tokens and skill_tokens.intersection(text_tokens):
                matched_skills.append(skill.title() if skill != "ai" else "AI")

        skill_match = len(matched_skills) / max(1, len(wanted_skills)) if wanted_skills else 0.0
        query_terms = set(tokenize(normalize_text(filters.role, " ".join(filters.skills), filters.seniority)))
        keyword_match = len(query_terms.intersection(text_tokens)) / max(1, len(query_terms)) if query_terms else 0.0
        location_match = bool(filters.location and filters.location.lower() in job.location.lower())
        if filters.remote is True and job.remote:
            location_match = True
        location_score = 1.0 if location_match else 0.0
        seniority_match = bool(filters.seniority and job.seniority and filters.seniority.lower() == job.seniority.lower())
        if seniority_match:
            keyword_match = min(1.0, keyword_match + 0.1)
        score = min(1.0, 0.5 * semantic + 0.2 * skill_match + 0.2 * keyword_match + 0.1 * location_score)
        breakdown = {
            "semantic_similarity": round(semantic, 3),
            "skill_match": round(skill_match, 3),
            "keyword_match": round(keyword_match, 3),
            "location_match": round(location_score, 3),
        }

        results.append(
            JobMatch(
                **serialize_job(job).model_dump(),
                match_score=round(score * 100, 1),
                explanation=ai.explain_match(job.title, text, profile_context, matched_skills, location_match, seniority_match),
                matched_skills=matched_skills,
                score_breakdown=breakdown,
            )
        )

    return sorted(results, key=lambda item: item.match_score, reverse=True)[:limit]
