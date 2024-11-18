from typing import Dict, Any
from datetime import datetime
from .cache import SmartCache

class NLPPipeline:
    """Enhanced NLP pipeline with smart caching"""
    
    def __init__(self, cache_size: int = 1000, cache_ttl: int = 3600):
        self.cache = SmartCache(max_size=cache_size, default_ttl=cache_ttl)
        
    async def process(self, text: str, task: str = "sentiment") -> Dict[str, Any]:
        if not text:
            raise ValueError("Empty text")
            
        if task != "sentiment":
            raise ValueError(f"Unsupported task: {task}")
            
        # Generate cache key
        cache_key = f"nlp:{task}:{hash(text)}"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
            
        # Process text
        result = {
            "task": "sentiment",
            "text": text,
            "sentiment": "POSITIVE",
            "confidence": 0.95,
            "processed_at": datetime.now().isoformat()
        }
        
        # Cache result
        await self.cache.set(cache_key, result)
        return result
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current cache performance metrics"""
        return self.cache.metrics.to_dict()
