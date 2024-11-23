import pytest
from datetime import datetime, timezone
import json
from .conftest import benchmark

@pytest.mark.benchmark
class TestTransformPerformance:
    
    @pytest.mark.asyncio
    @benchmark(iterations=1000)
    async def test_json_transform(self, services):
        """Benchmark JSON transformation operations"""
        raw_data = {
            "user": {
                "id": "test123",
                "preferences": {
                    "theme": "dark",
                    "notifications": ["email", "push"]
                },
                "history": [
                    {"action": "login", "timestamp": "2024-03-20T10:00:00Z"},
                    {"action": "view", "timestamp": "2024-03-20T10:01:00Z"}
                ]
            },
            "metadata": {
                "source": "benchmark",
                "version": "1.0"
            }
        }
        
        # Transform and store
        await services["db"].execute(
            """
            INSERT INTO test_events (
                event_type,
                payload,
                metadata
            )
            VALUES (
                'json_transform',
                $1,
                jsonb_build_object(
                    'processed_at', NOW(),
                    'source', $2->>'source',
                    'user_id', $3->>'id'
                )
            )
            """,
            json.dumps(raw_data),
            raw_data["metadata"],
            raw_data["user"]
        )
    
    @pytest.mark.asyncio
    @benchmark(iterations=100)
    async def test_timeseries_transform(self, services):
        """Benchmark time series data transformation"""
        # Generate time series data
        series_data = [
            {
                "timestamp": (
                    datetime.now(timezone.utc)
                    .replace(minute=i, second=0, microsecond=0)
                    .isoformat()
                ),
                "value": float(i),
                "tags": ["benchmark", f"series_{i % 5}"]
            }
            for i in range(60)  # 1 hour of minute data
        ]
        
        # Transform and store
        await services["db"].execute(
            """
            INSERT INTO timeseries.metrics (
                timestamp,
                value,
                tags,
                metadata
            )
            SELECT 
                (d->>'timestamp')::timestamptz,
                (d->>'value')::float,
                d->'tags',
                jsonb_build_object(
                    'source', 'benchmark',
                    'type', 'timeseries_transform'
                )
            FROM jsonb_array_elements($1::jsonb) d
            """,
            json.dumps(series_data)
        ) 