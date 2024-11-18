from typing import Any, Optional
from .lru_cache import LRUCache

class CacheManager:
    def __init__(self, capacity: int = 1000):
        self.cache = LRUCache(capacity)
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[Any]:
        result = self.cache.get(key)
        if result is not None:
            self.hits += 1
        else:
            self.misses += 1
        return result

    async def set(self, key: str, value: Any) -> None:
        self.cache.put(key, value)

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0