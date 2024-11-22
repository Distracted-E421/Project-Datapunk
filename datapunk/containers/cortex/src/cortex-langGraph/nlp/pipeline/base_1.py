# src/nlp/pipeline/base.py
from typing import Dict, Any, Optional
from datetime import datetime
from ..cache.manager import CacheManager

class BasePipeline:
    """Base class for all NLP pipelines"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or CacheManager()
        
    async def process(self, text: str, task: str) -> Dict[str, Any]:
        """Base processing method to be implemented by subclasses"""
        raise NotImplementedError
        
    async def _cache_lookup(self, key: str) -> Optional[Dict[str, Any]]:
        """Unified cache lookup"""
        if self.cache_manager:
            return await self.cache_manager.get(key)
        return None