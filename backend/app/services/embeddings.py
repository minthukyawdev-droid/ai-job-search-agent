import hashlib
import json
import math
from typing import Sequence

from openai import OpenAI

from app.config import get_settings
from app.services.text import tokenize


LOCAL_DIMENSIONS = 384


def dumps_vector(vector: Sequence[float]) -> str:
    return json.dumps([round(float(value), 8) for value in vector])


def loads_vector(raw: str | None) -> list[float] | None:
    if not raw:
        return None
    try:
        return [float(value) for value in json.loads(raw)]
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[i] * right[i] for i in range(size))
    left_norm = math.sqrt(sum(left[i] * left[i] for i in range(size)))
    right_norm = math.sqrt(sum(right[i] * right[i] for i in range(size)))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def embed(self, text: str) -> list[float]:
        if self.client:
            try:
                response = self.client.embeddings.create(
                    model=self.settings.openai_embedding_model,
                    input=text,
                )
                return response.data[0].embedding
            except Exception:
                return self._local_embed(text)
        return self._local_embed(text)

    def _local_embed(self, text: str) -> list[float]:
        vector = [0.0] * LOCAL_DIMENSIONS
        tokens = tokenize(text)
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % LOCAL_DIMENSIONS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector
