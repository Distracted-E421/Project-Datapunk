"""Integration tests for distributed cache system
Validates cache functionality across multiple Redis nodes as defined in sys-arch.mmd

Key test areas:
- Multi-node Redis cluster operations
- Cache invalidation strategies
- Data consistency across nodes
- Failure recovery scenarios
- Performance under load

TODO: Add tests for:
- Cache warm-up strategies
- Memory pressure handling
- Cross-datacenter replication
- Custom eviction policies
"""

import pytest
import asyncio
import time
import random
import string
from typing import List
import aioredis
from datapunk_shared.cache.cache_types import (
    CacheConfig, CacheStrategy, InvalidationStrategy
)
from datapunk_shared.cache.cache_manager import CacheManager
from datapunk_shared.cache.cluster_manager import ClusterNode
from datapunk_shared.cache.cache_features import CacheFeatureManager

@pytest.fixture
async def redis_nodes() -> List[aioredis.Redis]:
    """Setup Redis cluster for integration testing
    
    NOTE: Requires local Redis instances on specified ports
    FIXME: Add container orchestration for test Redis instances
    """
    nodes = []
    ports = [6379, 6380, 6381]  # Standard Redis cluster ports
    
    for port in ports:
        try:
            redis = await aioredis.from_url(f"redis://localhost:{port}")
            await redis.ping()
            nodes.append(redis)
        except Exception as e:
            pytest.skip(f"Redis not available on port {port}: {str(e)}")
    
    yield nodes
    
    # Cleanup
    for redis in nodes:
        await redis.flushall()
        await redis.close()

@pytest.fixture
async def cache_manager(redis_nodes):
    """Setup cache manager with real Redis cluster"""
    if not redis_nodes:
        pytest.skip("No Redis nodes available")

    config = CacheConfig(
        strategy=CacheStrategy.WRITE_THROUGH,
        invalidation_strategy=InvalidationStrategy.TTL,
        ttl=300,
        namespace="test_integration"
    )
    
    cluster_nodes = [
        ClusterNode(f"node{i}", "localhost", 6379+i)
        for i in range(len(redis_nodes))
    ]
    
    manager = CacheManager(
        config=config,
        redis_url="redis://localhost:6379",
        cluster_nodes=cluster_nodes
    )
    await manager.start()
    
    yield manager
    
    await manager.stop()

class TestCacheIntegration:
    @pytest.mark.asyncio
    async def test_basic_cache_operations(self, cache_manager):
        """Test basic cache operations with real Redis"""
        # Set value
        key = "test_key"
        value = {"data": "test_value"}
        
        await cache_manager.set(key, value)
        
        # Get value
        cached = await cache_manager.get(key)
        assert cached == value
        
        # Invalidate
        await cache_manager.invalidate(key)
        cached = await cache_manager.get(key)
        assert cached is None

    @pytest.mark.asyncio
    async def test_cluster_operations(self, cache_manager):
        """Test cluster operations with real Redis nodes"""
        # Set multiple values
        test_data = {
            f"key_{i}": f"value_{i}"
            for i in range(100)
        }
        
        # Write data
        for key, value in test_data.items():
            await cache_manager.set(key, value)
        
        # Verify data across cluster
        for key, expected in test_data.items():
            value = await cache_manager.get(key)
            assert value == expected

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, cache_manager):
        """Test concurrent cache operations"""
        async def worker(prefix: str, count: int):
            for i in range(count):
                key = f"{prefix}_{i}"
                value = f"value_{i}"
                await cache_manager.set(key, value)
                cached = await cache_manager.get(key)
                assert cached == value

        # Run multiple workers concurrently
        workers = [
            worker(f"worker_{i}", 100)
            for i in range(5)
        ]
        await asyncio.gather(*workers)

    @pytest.mark.asyncio
    async def test_feature_integration(self, cache_manager):
        """Test compression and encryption integration"""
        feature_manager = CacheFeatureManager(
            compression_enabled=True,
            encryption_enabled=True,
            encryption_key="test_key_123"
        )
        
        # Large data to test compression
        data = {
            'key': 'value',
            'large_field': ''.join(
                random.choices(string.ascii_letters, k=10000)
            )
        }
        
        # Process and cache data
        processed = await feature_manager.process_for_cache(data)
        await cache_manager.set("test_features", processed)
        
        # Retrieve and verify
        cached = await cache_manager.get("test_features")
        recovered = await feature_manager.process_from_cache(cached)
        assert recovered == data 