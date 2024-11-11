import pytest
import asyncio
import time
import statistics
from src.nlp.pipeline import NLPPipeline

@pytest.fixture
async def nlp_pipeline():
    return NLPPipeline()

@pytest.mark.performance
class TestNLPPerformance:
    @pytest.mark.asyncio
    async def test_latency_distribution(self, nlp_pipeline):
        """Test latency distribution over multiple requests"""
        latencies = []
        for _ in range(100):  # 100 requests
            start_time = time.time()
            await nlp_pipeline.process("Test text", task="sentiment")
            latencies.append((time.time() - start_time) * 1000)  # Convert to ms
            
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        mean_latency = statistics.mean(latencies)
        
        assert mean_latency < 100.0  # Mean latency under 100ms
        assert p95_latency < 200.0  # 95th percentile under 200ms
        
    @pytest.mark.asyncio
    async def test_throughput(self, nlp_pipeline):
        """Test system throughput under load"""
        num_requests = 1000
        texts = [f"Test text {i}" for i in range(num_requests)]
        
        start_time = time.time()
        tasks = [nlp_pipeline.process(text, task="sentiment") for text in texts]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        requests_per_second = num_requests / duration
        assert requests_per_second > 100  # At least 100 RPS
        
    @pytest.mark.asyncio
    async def test_cache_efficiency(self, nlp_pipeline):
        """Test cache hit ratio and performance"""
        text = "Cache test text"
        iterations = 100
        cache_hits = 0
        
        # First request (cache miss)
        await nlp_pipeline.process(text, task="sentiment")
        
        # Subsequent requests
        for _ in range(iterations):
            start_time = time.time()
            await nlp_pipeline.process(text, task="sentiment")
            if (time.time() - start_time) < 0.001:  # Under 1ms indicates cache hit
                cache_hits += 1
                
        hit_ratio = cache_hits / iterations
        assert hit_ratio > 0.95  # Expected 95% cache hit ratio
