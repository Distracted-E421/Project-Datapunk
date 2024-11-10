import pytest
import asyncio
import time
from src.nlp.pipeline import NLPPipeline

@pytest.mark.performance
class TestNLPPerformance:
    @pytest.mark.asyncio
    async def test_latency(self, nlp_pipeline):
        """Test processing latency"""
        start_time = time.time()
        await nlp_pipeline.process("Test text", task="sentiment")
        duration = time.time() - start_time
        
        assert duration < 1.0  # Should process in under 1 second
        
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, nlp_pipeline):
        """Test handling multiple concurrent requests"""
        texts = ["Text " + str(i) for i in range(10)]
        
        start_time = time.time()
        tasks = [nlp_pipeline.process(text, task="sentiment") for text in texts]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        assert len(results) == 10
        assert duration < 5.0  # Should handle 10 requests in under 5 seconds
        
    @pytest.mark.asyncio
    async def test_cache_performance(self, nlp_pipeline):
        """Test cache performance"""
        text = "Cache test text"
        
        # First request (cache miss)
        start_time = time.time()
        await nlp_pipeline.process(text, task="sentiment")
        first_duration = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        await nlp_pipeline.process(text, task="sentiment")
        second_duration = time.time() - start_time
        
        assert second_duration < first_duration * 0.5  # Cache should be at least 2x faster
