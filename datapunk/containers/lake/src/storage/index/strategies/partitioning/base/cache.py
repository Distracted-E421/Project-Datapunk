from typing import Dict, Any, Optional
import threading

class SpatialCache:
    """Thread-safe cache for spatial data with LRU eviction"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            return self.cache.get(key)
            
    def set(self, key: str, value: Any):
        """Set value in cache with LRU eviction"""
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[key] = value
            
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear() 