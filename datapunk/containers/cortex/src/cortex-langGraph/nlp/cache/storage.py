# src/nlp/cache/storage.py
from typing import Dict, Any, Optional
from datetime import datetime
import json
import hashlib

class CacheStorage:
    """Cache storage implementation"""
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.data: Dict[str, Any] = {}
        
    def _generate_key(self, data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()