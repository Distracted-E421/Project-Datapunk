import pytest
import asyncio
from typing import List, Dict
import json
from .conftest import benchmark

@pytest.mark.benchmark
class TestCachePerformance:
    
    @pytest.mark.asyncio
    @benchmark(iterations=10000)
    async def test_cache_get(self, services):
        """Benchmark cache get operation"""
        await services["cache"].get("benchmark:test:key")
    
    @pytest.mark.asyncio
    @benchmark(iterations=10000)
    async def test_cache_set(self, services):
        """Benchmark cache set operation"""
        await services["cache"].set(
            "benchmark:test:key",
            {"data": "test", "timestamp": "2024-03-20T10:00:00Z"}
        )
    
    @pytest.mark.asyncio
    @benchmark(iterations=1000)
    async def test_cache_pipeline(self, services):
        """Benchmark cache pipeline operations"""
        async with services["cache"].redis.pipeline() as pipe:
            for i in range(100):
                pipe.set(f"benchmark:pipe:{i}", f"value:{i}")
                pipe.expire(f"benchmark:pipe:{i}", 300)
            await pipe.execute() 