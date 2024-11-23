import pytest
import asyncio
from typing import List, Dict
import json
from .conftest import benchmark

@pytest.mark.benchmark
class TestDatabasePerformance:
    
    @pytest.mark.asyncio
    @benchmark(iterations=1000)
    async def test_single_insert(self, services):
        """Benchmark single record insert"""
        await services["db"].execute(
            """
            INSERT INTO test_events (event_type, payload)
            VALUES ($1, $2)
            """,
            "benchmark_test",
            json.dumps({"test": "data"})
        )
    
    @pytest.mark.asyncio
    @benchmark(iterations=100)
    async def test_bulk_insert(self, services):
        """Benchmark bulk insert operations"""
        test_data = [
            ("benchmark_bulk", json.dumps({"index": i}))
            for i in range(1000)
        ]
        
        await services["db"].execute(
            """
            INSERT INTO test_events (event_type, payload)
            SELECT * FROM UNNEST($1::text[], $2::jsonb[])
            """,
            [r[0] for r in test_data],
            [r[1] for r in test_data]
        )
    
    @pytest.mark.asyncio
    @benchmark(iterations=1000)
    async def test_complex_query(self, services):
        """Benchmark complex query performance"""
        await services["db"].fetch_all(
            """
            WITH ranked_events AS (
                SELECT 
                    event_type,
                    payload,
                    created_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY event_type 
                        ORDER BY created_at DESC
                    ) as rn
                FROM test_events
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            )
            SELECT 
                event_type,
                COUNT(*) as event_count,
                MAX(created_at) as last_seen
            FROM ranked_events
            WHERE rn <= 10
            GROUP BY event_type
            ORDER BY event_count DESC
            LIMIT 5
            """
        ) 