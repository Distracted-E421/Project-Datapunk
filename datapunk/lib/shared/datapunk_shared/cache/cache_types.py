from enum import Enum
from typing import Any, Optional, Dict, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

# Cache strategies define how data is written and read between the cache and the underlying storage
class CacheStrategy(Enum):
    # Synchronously writes data to both cache and storage
    WRITE_THROUGH = "write_through"
    # Asynchronously writes to storage while immediately updating cache
    WRITE_BEHIND = "write_behind"
    # Writes directly to storage, bypassing cache
    WRITE_AROUND = "write_around"
    # Loads missing cache entries from storage automatically
    READ_THROUGH = "read_through"
    # Application manages cache misses explicitly
    CACHE_ASIDE = "cache_aside"

# Defines how entries are removed from cache when it reaches capacity or entries expire
class InvalidationStrategy(Enum):
    # Time-based expiration
    TTL = "ttl"
    # Removes least recently used entries
    LRU = "lru"
    # Removes least frequently used entries
    LFU = "lfu"
    # Removes oldest entries first
    FIFO = "fifo"

@dataclass
class CacheConfig:
    """
    Configuration for cache behavior and performance characteristics.
    
    NOTE: When using WRITE_BEHIND strategy, both write_buffer_size and write_interval
    should be configured to control batch writes to the underlying storage.
    """
    strategy: CacheStrategy
    invalidation_strategy: InvalidationStrategy
    ttl: int = 3600  # Default 1 hour
    max_size: Optional[int] = None  # Maximum number of entries in cache
    write_buffer_size: Optional[int] = None  # Number of entries to buffer before writing
    write_interval: Optional[int] = None  # Seconds between write-behind flushes
    compression: bool = False  # Enable data compression to reduce memory usage
    namespace: str = "default"  # Logical partition for cache entries

@dataclass
class CacheEntry:
    """
    Represents a single cache entry with metadata for managing its lifecycle.
    
    The metadata dict can store custom attributes like:
    - source: origin of the data
    - checksum: data integrity verification
    - compression_type: if compression is used
    - priority: custom prioritization for invalidation
    """
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0  # Used by LFU invalidation strategy
    last_accessed: Optional[datetime] = None  # Used by LRU invalidation strategy
    version: int = 1  # Supports optimistic locking and conflict resolution
    metadata: Dict[str, Any] = None  # Extensible metadata for custom cache behaviors