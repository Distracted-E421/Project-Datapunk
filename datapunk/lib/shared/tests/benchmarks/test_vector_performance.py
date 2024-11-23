import pytest
import numpy as np
from typing import List
from .conftest import benchmark

@pytest.mark.benchmark
class TestVectorPerformance:
    
    @pytest.mark.asyncio
    @benchmark(iterations=100)
    async def test_vector_insert(self, services):
        """Benchmark vector insertion"""
        vector = np.random.rand(1536).astype(np.float32)  # OpenAI size
        metadata = {
            "source": "benchmark",
            "type": "test_embedding",
            "timestamp": "2024-03-20T10:00:00Z"
        }
        
        await services["db"].execute(
            """
            INSERT INTO vector.embeddings (embedding, metadata)
            VALUES ($1, $2)
            """,
            vector.tolist(),
            metadata
        )
    
    @pytest.mark.asyncio
    @benchmark(iterations=50)
    async def test_vector_similarity_search(self, services):
        """Benchmark vector similarity search"""
        query_vector = np.random.rand(1536).astype(np.float32)
        
        await services["db"].fetch_all(
            """
            SELECT id, metadata, 
                   embedding <-> $1 as distance
            FROM vector.embeddings
            ORDER BY embedding <-> $1
            LIMIT 10
            """,
            query_vector.tolist()
        ) 