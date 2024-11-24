from enum import Enum
from typing import Any, Optional, Dict, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

class CacheStrategy(Enum):
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    WRITE_AROUND = "write_around"
    READ_THROUGH = "read_through"
    CACHE_ASIDE = "cache_aside"

class InvalidationStrategy(Enum):
    TTL = "ttl"
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"

@dataclass
class CacheConfig:
    strategy: CacheStrategy
    invalidation_strategy: InvalidationStrategy
    ttl: int = 3600  # Default 1 hour
    max_size: Optional[int] = None
    write_buffer_size: Optional[int] = None
    write_interval: Optional[int] = None  # For write-behind
    compression: bool = False
    namespace: str = "default"

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    version: int = 1
    metadata: Dict[str, Any] = None 