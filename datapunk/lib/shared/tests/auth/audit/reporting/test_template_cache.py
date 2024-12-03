"""
Template Cache Tests
----------------

Tests the template caching functionality including:
- Cache operations
- Cache strategies
- Cache invalidation
- Performance optimization
- Error handling
- Metrics collection

Run with: pytest -v test_template_cache.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json

from datapunk_shared.auth.audit.reporting.template_cache import (
    TemplateCache,
    CacheConfig,
    CacheEntry
)
from datapunk_shared.auth.audit.reporting.template_cache_utils import (
    CacheUtils,
    CacheStrategy,
    CacheMetrics
)

# Test Fixtures

@pytest.fixture
def redis_client():
    """Mock Redis client for testing."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.exists = AsyncMock(return_value=False)
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def cache_config():
    """Create cache configuration for testing."""
    return CacheConfig(
        ttl=timedelta(hours=1),
        max_size=1000,
        strategy=CacheStrategy.LRU,
        namespace="test_cache"
    )

@pytest.fixture
def template_cache(redis_client, metrics_client, cache_config):
    """Create template cache for testing."""
    return TemplateCache(
        redis=redis_client,
        metrics=metrics_client,
        config=cache_config
    )

@pytest.fixture
def template_data():
    """Create template data for testing."""
    return {
        "id": "test_template",
        "version": "1.0",
        "content": {
            "sections": ["summary"],
            "fields": {"test": {"type": "string"}}
        }
    }

# Cache Operations Tests

@pytest.mark.asyncio
async def test_cache_set_get(template_cache, template_data):
    """Test basic cache set and get operations."""
    # Set template in cache
    await template_cache.set("test_key", template_data)
    
    # Mock Redis response
    template_cache.redis.get.return_value = json.dumps(template_data)
    
    # Get template from cache
    result = await template_cache.get("test_key")
    
    assert result == template_data
    template_cache.redis.set.assert_called_once()
    template_cache.metrics.increment.assert_called_with(
        "cache_sets",
        tags={"namespace": "test_cache"}
    )

@pytest.mark.asyncio
async def test_cache_miss(template_cache):
    """Test cache miss handling."""
    template_cache.redis.get.return_value = None
    
    result = await template_cache.get("nonexistent_key")
    
    assert result is None
    template_cache.metrics.increment.assert_called_with(
        "cache_misses",
        tags={"namespace": "test_cache"}
    )

@pytest.mark.asyncio
async def test_cache_invalidation(template_cache):
    """Test cache invalidation."""
    await template_cache.invalidate("test_key")
    
    template_cache.redis.delete.assert_called_once_with("test_key")
    template_cache.metrics.increment.assert_called_with(
        "cache_invalidations",
        tags={"namespace": "test_cache"}
    )

# Cache Strategy Tests

@pytest.mark.asyncio
async def test_lru_strategy(template_cache, template_data):
    """Test LRU cache strategy."""
    # Fill cache to max size
    for i in range(1000):
        await template_cache.set(f"key_{i}", template_data)
    
    # Add one more item
    await template_cache.set("new_key", template_data)
    
    # Verify LRU eviction
    template_cache.metrics.increment.assert_called_with(
        "cache_evictions",
        tags={"strategy": "LRU", "namespace": "test_cache"}
    )

@pytest.mark.asyncio
async def test_ttl_expiration(template_cache, template_data):
    """Test TTL-based expiration."""
    # Set item with TTL
    await template_cache.set("test_key", template_data)
    
    # Verify TTL set
    template_cache.redis.set.assert_called_with(
        "test_key",
        mock.ANY,
        ex=3600  # 1 hour in seconds
    )

# Performance Tests

@pytest.mark.asyncio
async def test_bulk_operations(template_cache, template_data):
    """Test bulk cache operations performance."""
    # Bulk set
    items = {f"key_{i}": template_data for i in range(100)}
    await template_cache.set_many(items)
    
    # Verify batch processing
    assert template_cache.redis.set.call_count == 100
    
    # Bulk get
    template_cache.redis.get.return_value = json.dumps(template_data)
    results = await template_cache.get_many(items.keys())
    
    assert len(results) == 100
    assert all(v == template_data for v in results.values())

@pytest.mark.asyncio
async def test_cache_performance(template_cache, template_data):
    """Test cache performance metrics."""
    # Perform operations
    await template_cache.set("test_key", template_data)
    template_cache.redis.get.return_value = json.dumps(template_data)
    await template_cache.get("test_key")
    
    # Verify timing metrics
    template_cache.metrics.timing.assert_called_with(
        "cache_operation_time",
        mock.ANY,
        tags={"operation": mock.ANY, "namespace": "test_cache"}
    )

# Error Handling Tests

@pytest.mark.asyncio
async def test_redis_connection_error(template_cache, template_data):
    """Test handling of Redis connection errors."""
    template_cache.redis.set.side_effect = Exception("Connection error")
    
    with pytest.raises(Exception) as exc:
        await template_cache.set("test_key", template_data)
    assert "connection error" in str(exc.value).lower()
    
    template_cache.metrics.increment.assert_called_with(
        "cache_errors",
        tags={"type": "connection", "namespace": "test_cache"}
    )

@pytest.mark.asyncio
async def test_serialization_error(template_cache):
    """Test handling of serialization errors."""
    # Create un-serializable data
    data = {"function": lambda x: x}  # Functions can't be JSON serialized
    
    with pytest.raises(Exception) as exc:
        await template_cache.set("test_key", data)
    assert "serialization" in str(exc.value).lower()
    
    template_cache.metrics.increment.assert_called_with(
        "cache_errors",
        tags={"type": "serialization", "namespace": "test_cache"}
    )

# Cache Utils Tests

def test_cache_key_generation():
    """Test cache key generation utilities."""
    utils = CacheUtils()
    
    # Generate cache key
    key = utils.generate_key(
        template_id="test",
        version="1.0",
        context={"user": "test_user"}
    )
    
    assert "test" in key
    assert "1.0" in key
    assert "test_user" in key

def test_cache_metrics_aggregation(metrics_client):
    """Test cache metrics aggregation."""
    metrics = CacheMetrics(metrics_client)
    
    # Record operations
    metrics.record_hit("test_cache")
    metrics.record_miss("test_cache")
    metrics.record_set("test_cache")
    
    # Verify metrics
    metrics_client.increment.assert_has_calls([
        mock.call("cache_hits", tags={"namespace": "test_cache"}),
        mock.call("cache_misses", tags={"namespace": "test_cache"}),
        mock.call("cache_sets", tags={"namespace": "test_cache"})
    ])

# Namespace Tests

@pytest.mark.asyncio
async def test_namespace_isolation(template_cache, template_data):
    """Test cache namespace isolation."""
    # Create caches with different namespaces
    cache1 = TemplateCache(
        redis=AsyncMock(),
        metrics=AsyncMock(),
        config=CacheConfig(namespace="cache1")
    )
    cache2 = TemplateCache(
        redis=AsyncMock(),
        metrics=AsyncMock(),
        config=CacheConfig(namespace="cache2")
    )
    
    # Set same key in both caches
    await cache1.set("test_key", template_data)
    await cache2.set("test_key", template_data)
    
    # Verify keys are namespaced
    cache1.redis.set.assert_called_with(
        mock.ANY,  # Key should include namespace
        mock.ANY,
        ex=mock.ANY
    )
    assert "cache1" in cache1.redis.set.call_args[0][0]
    assert "cache2" in cache2.redis.set.call_args[0][0]

# Configuration Tests

def test_cache_configuration():
    """Test cache configuration validation."""
    # Valid config
    config = CacheConfig(
        ttl=timedelta(hours=1),
        max_size=1000,
        strategy=CacheStrategy.LRU
    )
    assert config.ttl.total_seconds() == 3600
    
    # Invalid config
    with pytest.raises(ValueError):
        CacheConfig(
            ttl=timedelta(seconds=-1),  # Negative TTL
            max_size=0,  # Invalid size
            strategy="invalid"  # Invalid strategy
        )

def test_strategy_selection():
    """Test cache strategy selection."""
    # LRU strategy
    cache = TemplateCache(
        redis=AsyncMock(),
        metrics=AsyncMock(),
        config=CacheConfig(strategy=CacheStrategy.LRU)
    )
    assert cache.strategy == CacheStrategy.LRU
    
    # LFU strategy
    cache = TemplateCache(
        redis=AsyncMock(),
        metrics=AsyncMock(),
        config=CacheConfig(strategy=CacheStrategy.LFU)
    )
    assert cache.strategy == CacheStrategy.LFU 