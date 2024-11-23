import pytest
import asyncio
from typing import List
import json
from .conftest import benchmark

@pytest.mark.benchmark
class TestConcurrentPerformance:
    
    @pytest.mark.asyncio
    @benchmark(iterations=10)
    async def test_parallel_cache_ops(self, services):
        """Benchmark parallel cache operations"""
        async def cache_operation(i: int):
            key = f"bench:parallel:{i}"
            await services["cache"].set(key, {"index": i})
            await services["cache"].get(key)
            
        tasks = [cache_operation(i) for i in range(100)]
        await asyncio.gather(*tasks)
    
    @pytest.mark.asyncio
    @benchmark(iterations=10)
    async def test_mixed_operations(self, services):
        """Benchmark mixed concurrent operations"""
        async def mixed_op(i: int):
            # Cache operation
            await services["cache"].set(f"bench:mixed:{i}", {"index": i})
            
            # Database operation
            await services["db"].execute(
                """
                INSERT INTO test_events (event_type, payload)
                VALUES ($1, $2)
                """,
                "benchmark_mixed",
                json.dumps({"index": i})
            )
            
            # Message operation
            await services["mq"].publish(
                "benchmark_exchange",
                "benchmark.mixed",
                {"index": i}
            )
        
        tasks = [mixed_op(i) for i in range(10)]
        await asyncio.gather(*tasks) 