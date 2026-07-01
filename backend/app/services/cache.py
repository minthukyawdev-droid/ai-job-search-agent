import json
from typing import Any

import redis

from app.config import get_settings


class CacheService:
    def __init__(self) -> None:
        self.settings = get_settings()
        try:
            self.client = redis.from_url(self.settings.redis_url, decode_responses=True)
            self.client.ping()
        except Exception:
            self.client = None

    def get_json(self, key: str) -> Any | None:
        if not self.client:
            return None
        raw = self.client.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if not self.client:
            return
        self.client.setex(key, ttl_seconds, json.dumps(value))

    def delete_pattern(self, pattern: str) -> None:
        if not self.client:
            return
        for key in self.client.scan_iter(pattern):
            self.client.delete(key)
