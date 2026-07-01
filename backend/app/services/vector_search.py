from app import models
from app.services.embeddings import cosine_similarity


class VectorSearchService:
    """Small FAISS-compatible adapter with a pure-Python fallback.

    Production can swap this class for a persisted FAISS or Pinecone index while
    preserving the ranking contract used by the API.
    """

    def search(self, query_vector: list[float], jobs: list[tuple[models.Job, list[float]]], limit: int) -> list[tuple[models.Job, float]]:
        scored = [(job, max(0.0, cosine_similarity(query_vector, vector))) for job, vector in jobs]
        return sorted(scored, key=lambda item: item[1], reverse=True)[:limit]
