from typing import Dict, Any
from transformers import pipeline
from ..core.cache import CacheManager

class BasicNLPPipeline:
    """Minimal NLP pipeline for sentiment analysis"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        # Load a lightweight sentiment model
        self.model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            max_length=512
        )
    
    async def process(self, text: str) -> Dict[str, Any]:
        # Check cache first
        cache_key = f"sentiment:{hash(text)}"
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return cached
            
        # Process text
        result = self.model(text)[0]
        
        # Format response
        response = {
            "sentiment": result["label"],
            "confidence": result["score"],
            "text": text
        }
        
        # Cache result
        await self.cache_manager.set(cache_key, response)
        
        return response
