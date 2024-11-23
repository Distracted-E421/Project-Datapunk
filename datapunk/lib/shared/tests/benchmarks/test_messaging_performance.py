import pytest
import asyncio
from typing import List, Dict
import json
from .conftest import benchmark

@pytest.mark.benchmark
class TestMessagingPerformance:
    
    @pytest.mark.asyncio
    @benchmark(iterations=1000)
    async def test_message_publish(self, services):
        """Benchmark message publishing"""
        await services["mq"].publish(
            "benchmark_exchange",
            "benchmark.test",
            {"data": "test", "timestamp": "2024-03-20T10:00:00Z"}
        )
    
    @pytest.mark.asyncio
    @benchmark(iterations=100)
    async def test_batch_publish(self, services):
        """Benchmark batch message publishing"""
        messages = [
            {"index": i, "data": f"test_{i}"}
            for i in range(100)
        ]
        
        async with services["mq"].channel.transaction():
            for msg in messages:
                await services["mq"].publish(
                    "benchmark_exchange",
                    "benchmark.batch",
                    msg
                )
    
    @pytest.mark.asyncio
    @benchmark(iterations=1000)
    async def test_message_roundtrip(self, services):
        """Benchmark message roundtrip (publish + consume)"""
        received = asyncio.Event()
        
        async def handle_message(message):
            received.set()
        
        await services["mq"].subscribe(
            "benchmark_exchange",
            "benchmark.roundtrip",
            handle_message
        )
        
        await services["mq"].publish(
            "benchmark_exchange",
            "benchmark.roundtrip",
            {"test": "roundtrip"}
        )
        
        await received.wait() 