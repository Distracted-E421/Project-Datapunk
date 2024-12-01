import pytest
import asyncio
import aioredis
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from ..src.storage.cache import Cache, CacheConfig, CacheStrategy
from ..src.storage.cache_strategies import (
    AccessPattern,
    TimeBasedWarming,
    RelatedKeyWarming,
    HybridWarming,
    ReplicationManager,
    EnhancedMetrics
)
from ..src.ingestion.monitoring import HandlerMetrics, MetricType
from sklearn.ensemble import RandomForestRegressor

@pytest.fixture
async def redis():
    redis = await aioredis.from_url("redis://localhost")
    await redis.flushall()
    yield redis
    await redis.close()

@pytest.fixture
def metrics():
    return Mock(spec=HandlerMetrics)

@pytest.fixture
async def cache(redis, metrics):
    config = CacheConfig(
        strategy=CacheStrategy.LRU,
        ttl=3600,
        max_size=1000,
        compression=True,
        warming_strategies=["time", "related"],
        access_pattern_window=3600
    )
    cache = Cache(redis, config, metrics)
    await cache.start()
    yield cache
    await cache.stop()

@pytest.mark.asyncio
async def test_cache_basic_operations(cache):
    """Test basic cache operations"""
    # Set
    assert await cache.set("test_key", {"value": 123})
    
    # Get
    value = await cache.get("test_key")
    assert value == {"value": 123}
    
    # Delete
    assert await cache.delete("test_key")
    assert await cache.get("test_key") is None

@pytest.mark.asyncio
async def test_cache_ttl(cache):
    """Test TTL expiration"""
    await cache.set("ttl_key", "value", ttl=1)
    assert await cache.get("ttl_key") == "value"
    
    await asyncio.sleep(1.1)
    assert await cache.get("ttl_key") is None

@pytest.mark.asyncio
async def test_cache_compression(cache):
    """Test data compression"""
    large_data = "x" * 1000
    await cache.set("compressed_key", large_data)
    
    # Get raw data from Redis to verify compression
    raw_data = await cache.redis.get("compressed_key")
    assert len(raw_data) < len(large_data.encode())
    
    # Verify decompression works
    value = await cache.get("compressed_key")
    assert value == large_data

@pytest.mark.asyncio
async def test_fifo_strategy(redis, metrics):
    """Test FIFO eviction strategy"""
    config = CacheConfig(
        strategy=CacheStrategy.FIFO,
        max_size=2
    )
    cache = Cache(redis, config, metrics)
    await cache.start()
    
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")  # Should trigger eviction
    
    assert await cache.get("key1") is None  # First in, first out
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"
    
    await cache.stop()

@pytest.mark.asyncio
async def test_random_strategy(redis, metrics):
    """Test random eviction strategy"""
    config = CacheConfig(
        strategy=CacheStrategy.RANDOM,
        max_size=2
    )
    cache = Cache(redis, config, metrics)
    await cache.start()
    
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")  # Should trigger eviction
    
    # At least one key should remain
    remaining = sum(
        1 for key in ["key1", "key2", "key3"]
        if await cache.get(key) is not None
    )
    assert remaining >= 1
    
    await cache.stop()

@pytest.mark.asyncio
async def test_distributed_cache(redis, metrics):
    """Test distributed cache functionality"""
    nodes = [
        {"host": "localhost", "port": 6379},
        {"host": "localhost", "port": 6380}
    ]
    config = CacheConfig(
        distributed=True,
        nodes=nodes
    )
    cache = Cache(redis, config, metrics)
    await cache.start()
    
    # Test consistent hashing
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    
    # Test node failure handling
    with patch("aioredis.from_url") as mock_redis:
        mock_redis.side_effect = ConnectionError
        # Should fall back to next available node
        assert await cache.get("key1") == "value1"
    
    await cache.stop()

@pytest.mark.asyncio
async def test_cache_warming(redis, metrics):
    """Test cache warming functionality"""
    async def fetch_handler(key: str):
        return f"warmed_{key}"
    
    config = CacheConfig(
        warm_patterns={
            "test:*": {
                "ttl": 3600,
                "warm_interval": 1,
                "batch_size": 10
            }
        }
    )
    cache = Cache(redis, config, metrics)
    cache._fetch_missing = fetch_handler
    await cache.start()
    
    # Add some test keys
    await cache.set("test:1", "value1")
    await cache.set("test:2", "value2")
    
    # Delete one key to simulate expiration
    await cache.delete("test:1")
    
    # Wait for warming
    await asyncio.sleep(1.1)
    
    # Verify warming
    assert await cache.get("test:1") == "warmed_test:1"
    assert await cache.get("test:2") == "value2"
    
    await cache.stop()

@pytest.mark.asyncio
async def test_metrics_recording(cache, metrics):
    """Test metrics recording"""
    # Test hit
    await cache.set("metrics_key", "value")
    await cache.get("metrics_key")
    
    metrics.record_metric.assert_any_call(
        "cache_hit",
        1,
        MetricType.COUNTER,
        {"key": "metrics_key"}
    )
    
    # Test miss
    await cache.get("nonexistent")
    metrics.record_metric.assert_any_call(
        "cache_miss",
        1,
        MetricType.COUNTER,
        {"key": "nonexistent"}
    )

@pytest.mark.asyncio
async def test_serialization_formats(cache):
    """Test different serialization formats"""
    # Test JSON
    json_data = {"key": "value", "nested": {"list": [1, 2, 3]}}
    await cache.set("json_key", json_data, format="json")
    assert await cache.get("json_key") == json_data
    
    # Test Pickle
    class CustomObject:
        def __init__(self, value):
            self.value = value
            
        def __eq__(self, other):
            return isinstance(other, CustomObject) and self.value == other.value
    
    obj = CustomObject("test")
    await cache.set("pickle_key", obj, format="pickle")
    result = await cache.get("pickle_key", format="pickle")
    assert result == obj

@pytest.mark.asyncio
async def test_namespace_operations(cache):
    """Test namespace operations"""
    # Set keys in different namespaces
    await cache.set("ns1:key1", "value1")
    await cache.set("ns1:key2", "value2")
    await cache.set("ns2:key1", "value3")
    
    # Clear specific namespace
    cleared = await cache.clear("ns1")
    assert cleared == 2
    
    assert await cache.get("ns1:key1") is None
    assert await cache.get("ns1:key2") is None
    assert await cache.get("ns2:key1") == "value3"

@pytest.mark.asyncio
async def test_error_handling(cache):
    """Test error handling"""
    # Test invalid serialization
    with pytest.raises(ValueError):
        await cache.set("error_key", "value", format="invalid")
    
    # Test connection error
    with patch.object(cache.redis, "get") as mock_get:
        mock_get.side_effect = ConnectionError
        assert await cache.get("any_key") is None
        
    # Test serialization error
    with patch("json.dumps") as mock_dumps:
        mock_dumps.side_effect = TypeError
        with pytest.raises(Exception):
            await cache.set("error_key", {"circular": {}})

@pytest.mark.asyncio
async def test_access_pattern_tracking(cache):
    """Test access pattern tracking and analysis"""
    # Simulate periodic access pattern
    now = time.time()
    period = 300  # 5 minutes
    
    for i in range(5):
        await cache.set(f"periodic_key", f"value_{i}")
        cache.access_pattern.record_access(
            "periodic_key",
            now + i * period
        )
    
    patterns = cache.access_pattern.get_periodic_patterns("periodic_key")
    assert patterns
    assert abs(patterns[0][0] - period) < period * 0.1  # Within 10%
    assert patterns[0][1] > 0.7  # High confidence

@pytest.mark.asyncio
async def test_time_based_warming(redis, metrics):
    """Test time-based cache warming"""
    config = CacheConfig(
        warm_patterns={
            "test:*": {
                "warm_window": 300,
                "batch_size": 10
            }
        },
        warming_strategies=["time"]
    )
    cache = Cache(redis, config, metrics)
    
    # Simulate periodic access
    now = time.time()
    period = 300
    
    for i in range(5):
        await cache.set(f"test:key", f"value_{i}")
        cache.access_pattern.record_access(
            "test:key",
            now + i * period
        )
    
    # Wait for warming
    await asyncio.sleep(1)
    
    # Verify warming candidates
    strategy = TimeBasedWarming(redis, cache.access_pattern)
    candidates = await strategy.get_warming_candidates(
        "test:*",
        {"warm_window": 300}
    )
    assert "test:key" in candidates

@pytest.mark.asyncio
async def test_related_key_warming(redis, metrics):
    """Test related key warming"""
    config = CacheConfig(
        warm_patterns={
            "test:*": {
                "correlation_threshold": 0.8,
                "batch_size": 10
            }
        },
        warming_strategies=["related"]
    )
    cache = Cache(redis, config, metrics)
    
    # Simulate related access
    now = time.time()
    for i in range(5):
        await cache.set("test:key1", "value1")
        await cache.set("test:key2", "value2")
        cache.access_pattern.record_access("test:key1", now + i)
        cache.access_pattern.record_access("test:key2", now + i + 0.1)
    
    # Delete one key
    await cache.delete("test:key2")
    
    # Verify warming candidates
    strategy = RelatedKeyWarming(redis, cache.access_pattern)
    candidates = await strategy.get_warming_candidates(
        "test:*",
        {"correlation_threshold": 0.8}
    )
    assert "test:key2" in candidates

@pytest.mark.asyncio
async def test_hybrid_warming(redis, metrics):
    """Test hybrid warming strategy"""
    config = CacheConfig(
        warm_patterns={
            "test:*": {
                "warm_window": 300,
                "correlation_threshold": 0.8,
                "batch_size": 10
            }
        },
        warming_strategies=["time", "related"]
    )
    cache = Cache(redis, config, metrics)
    
    # Simulate both periodic and related access
    now = time.time()
    period = 300
    
    for i in range(5):
        await cache.set("test:periodic", f"value_{i}")
        await cache.set("test:related1", "value1")
        await cache.set("test:related2", "value2")
        
        # Periodic access
        cache.access_pattern.record_access(
            "test:periodic",
            now + i * period
        )
        
        # Related access
        cache.access_pattern.record_access(
            "test:related1",
            now + i
        )
        cache.access_pattern.record_access(
            "test:related2",
            now + i + 0.1
        )
    
    # Delete keys
    await cache.delete("test:periodic")
    await cache.delete("test:related2")
    
    # Verify warming candidates include both types
    candidates = await cache.warmer._get_warming_candidates(
        "test:*",
        {
            "warm_window": 300,
            "correlation_threshold": 0.8,
            "batch_size": 10
        }
    )
    assert "test:periodic" in candidates
    assert "test:related2" in candidates

@pytest.mark.asyncio
async def test_replication(redis, metrics):
    """Test cache replication"""
    nodes = [
        {"host": "localhost", "port": 6379},
        {"host": "localhost", "port": 6380}
    ]
    config = CacheConfig(
        distributed=True,
        nodes=nodes,
        replication_factor=2
    )
    cache = Cache(redis, config, metrics)
    await cache.start()
    
    # Mock Redis connections
    redis_instances = {
        "localhost:6379": MagicMock(),
        "localhost:6380": MagicMock()
    }
    
    with patch("aioredis.from_url") as mock_redis:
        mock_redis.side_effect = lambda url: redis_instances[
            url.replace("redis://", "")
        ]
        
        # Test set with replication
        await cache.set("test_key", "value")
        
        for instance in redis_instances.values():
            instance.set.assert_called_once()
        
        # Test get with failover
        redis_instances["localhost:6379"].get.side_effect = ConnectionError
        redis_instances["localhost:6380"].get.return_value = b"value"
        
        result = await cache.get("test_key")
        assert result == "value"
    
    await cache.stop()

@pytest.mark.asyncio
async def test_enhanced_metrics(cache):
    """Test enhanced metrics collection"""
    # Test operation timing
    await cache.set("metrics_key", "value")
    await cache.get("metrics_key")
    await cache.delete("metrics_key")
    
    # Verify metric calls
    cache.enhanced_metrics.metrics.record_metric.assert_any_call(
        "cache_set_latency",
        mock.ANY,  # Duration
        MetricType.HISTOGRAM,
        {"key": "metrics_key"}
    )
    
    cache.enhanced_metrics.metrics.record_metric.assert_any_call(
        "cache_get_latency",
        mock.ANY,  # Duration
        MetricType.HISTOGRAM,
        {"key": "metrics_key"}
    )
    
    cache.enhanced_metrics.metrics.record_metric.assert_any_call(
        "cache_delete_latency",
        mock.ANY,  # Duration
        MetricType.HISTOGRAM,
        {"key": "metrics_key"}
    )

@pytest.mark.asyncio
async def test_error_handling(cache):
    """Test error handling and metrics"""
    # Test serialization error
    with patch("json.dumps") as mock_dumps:
        mock_dumps.side_effect = TypeError("Circular reference")
        success = await cache.set("error_key", {"circular": {}})
        assert not success
        
        cache.enhanced_metrics.metrics.record_metric.assert_any_call(
            "cache_set",
            1,
            MetricType.COUNTER,
            {
                "key": "error_key",
                "success": "False",
                "error": "Circular reference"
            }
        )
    
    # Test connection error
    with patch.object(cache.redis, "get") as mock_get:
        mock_get.side_effect = ConnectionError("Connection failed")
        result = await cache.get("any_key")
        assert result is None
        
        cache.enhanced_metrics.metrics.record_metric.assert_any_call(
            "cache_get",
            1,
            MetricType.COUNTER,
            {
                "key": "any_key",
                "success": "False",
                "error": "Connection failed"
            }
        )

@pytest.mark.asyncio
async def test_cleanup_and_maintenance(cache):
    """Test cleanup and maintenance operations"""
    # Fill cache beyond max size
    for i in range(cache.config.max_size + 10):
        await cache.set(f"key_{i}", f"value_{i}")
        
    # Trigger cleanup
    await cache._enforce_max_size()
    
    # Verify eviction metrics
    cache.enhanced_metrics.metrics.record_metric.assert_any_call(
        "cache_eviction",
        mock.ANY,  # Number of evicted keys
        MetricType.COUNTER,
        {"strategy": cache.config.strategy.value}
    )
    
    # Verify total keys is within limit
    total_keys = await cache.redis.dbsize()
    assert total_keys <= cache.config.max_size

@pytest.mark.asyncio
async def test_ml_based_warming(redis, metrics):
    """Test ML-based cache warming"""
    config = CacheConfig(
        warm_patterns={
            "test:*": {
                "probability_threshold": 0.7,
                "batch_size": 10
            }
        },
        warming_strategies=["ml"],
        ml_update_interval=60
    )
    cache = Cache(redis, config, metrics)
    
    # Generate training data with clear pattern
    now = time.time()
    for i in range(24):  # 24 hours of data
        hour = i % 24
        if 9 <= hour <= 17:  # Business hours
            # Simulate high activity
            for j in range(5):
                await cache.set(f"test:key{j}", f"value_{i}_{j}")
                cache.access_pattern.record_access(
                    f"test:key{j}",
                    now + i * 3600 + j * 60
                )
    
    # Wait for model update
    await asyncio.sleep(1)
    
    # Test prediction during business hours
    cache.access_pattern.record_access(
        "test:key0",
        now + 25 * 3600  # Next day
    )
    
    strategy = MLBasedWarming(redis, cache.access_pattern)
    candidates = await strategy.get_warming_candidates(
        "test:*",
        {"probability_threshold": 0.7}
    )
    
    # Should predict access for related keys
    assert any(k.startswith("test:key") for k in candidates)

@pytest.mark.asyncio
async def test_seasonal_warming(redis, metrics):
    """Test seasonal pattern based warming"""
    config = CacheConfig(
        warm_patterns={
            "test:*": {
                "seasonal_threshold": 0.7,
                "batch_size": 10
            }
        },
        warming_strategies=["seasonal"]
    )
    cache = Cache(redis, config, metrics)
    
    # Generate data with weekly pattern
    now = time.time()
    for week in range(4):  # 4 weeks of data
        for day in range(7):
            if day < 5:  # Weekdays
                for hour in range(24):
                    if 9 <= hour <= 17:  # Business hours
                        await cache.set("test:key", f"value_{week}_{day}_{hour}")
                        cache.access_pattern.record_access(
                            "test:key",
                            now + week * 7 * 24 * 3600 +
                            day * 24 * 3600 +
                            hour * 3600
                        )
    
    # Delete key and test warming
    await cache.delete("test:key")
    
    strategy = SeasonalWarming(redis, cache.access_pattern)
    candidates = await strategy.get_warming_candidates(
        "test:*",
        {"seasonal_threshold": 0.7}
    )
    
    # Should predict warming during business hours on weekdays
    current_time = datetime.now()
    if (
        0 <= current_time.weekday() <= 4 and
        9 <= current_time.hour <= 17
    ):
        assert "test:key" in candidates
    else:
        assert "test:key" not in candidates

@pytest.mark.asyncio
async def test_quorum_replication(redis, metrics):
    """Test quorum-based replication"""
    nodes = [
        {"host": "localhost", "port": 6379},
        {"host": "localhost", "port": 6380},
        {"host": "localhost", "port": 6381}
    ]
    config = CacheConfig(
        distributed=True,
        nodes=nodes,
        read_quorum=2,
        write_quorum=2
    )
    cache = Cache(redis, config, metrics)
    await cache.start()
    
    # Mock Redis connections
    redis_instances = {
        "localhost:6379": MagicMock(),
        "localhost:6380": MagicMock(),
        "localhost:6381": MagicMock()
    }
    
    with patch("aioredis.from_url") as mock_redis:
        mock_redis.side_effect = lambda url: redis_instances[
            url.replace("redis://", "")
        ]
        
        # Test write quorum
        await cache.set("test_key", "value")
        
        write_success = sum(
            1 for instance in redis_instances.values()
            if instance.set.called
        )
        assert write_success >= config.write_quorum
        
        # Test read quorum with consistency
        value = b"value"
        redis_instances["localhost:6379"].get.return_value = value
        redis_instances["localhost:6380"].get.return_value = value
        redis_instances["localhost:6381"].get.return_value = value
        
        result = await cache.get("test_key")
        assert result == "value"
        
        read_attempts = sum(
            1 for instance in redis_instances.values()
            if instance.get.called
        )
        assert read_attempts >= config.read_quorum
        
        # Test read quorum with inconsistency
        redis_instances["localhost:6380"].get.return_value = b"different"
        
        with pytest.warns(UserWarning, match="Inconsistent values"):
            result = await cache.get("test_key")
            assert result in ["value", "different"]
        
        # Test write quorum failure
        redis_instances["localhost:6379"].set.side_effect = ConnectionError
        redis_instances["localhost:6380"].set.side_effect = ConnectionError
        
        success = await cache.set("test_key", "value")
        assert not success
    
    await cache.stop()

@pytest.mark.asyncio
async def test_hybrid_warming_strategies(redis, metrics):
    """Test combination of multiple warming strategies"""
    config = CacheConfig(
        warm_patterns={
            "test:*": {
                "probability_threshold": 0.7,
                "seasonal_threshold": 0.7,
                "batch_size": 10
            }
        },
        warming_strategies=["ml", "seasonal", "time", "related"]
    )
    cache = Cache(redis, config, metrics)
    
    # Generate data with multiple patterns
    now = time.time()
    
    # Time-based pattern
    period = 300
    for i in range(5):
        await cache.set("test:time", f"value_{i}")
        cache.access_pattern.record_access(
            "test:time",
            now + i * period
        )
    
    # Related keys pattern
    for i in range(5):
        await cache.set("test:related1", "value1")
        await cache.set("test:related2", "value2")
        cache.access_pattern.record_access(
            "test:related1",
            now + i
        )
        cache.access_pattern.record_access(
            "test:related2",
            now + i + 0.1
        )
    
    # Seasonal pattern (business hours)
    for day in range(5):  # Weekdays
        for hour in range(24):
            if 9 <= hour <= 17:
                await cache.set(
                    "test:seasonal",
                    f"value_{day}_{hour}"
                )
                cache.access_pattern.record_access(
                    "test:seasonal",
                    now + day * 24 * 3600 + hour * 3600
                )
    
    # ML pattern (specific features)
    for i in range(100):
        key = f"test:ml_{i % 5}"
        await cache.set(key, f"value_{i}")
        if i % 10 == 0:  # Create pattern
            cache.access_pattern.record_access(
                key,
                now + i * 60
            )
    
    # Delete keys
    await cache.delete("test:time")
    await cache.delete("test:related2")
    await cache.delete("test:seasonal")
    await cache.delete("test:ml_0")
    
    # Wait for model updates
    await asyncio.sleep(1)
    
    # Test warming
    candidates = await cache.warmer._get_warming_candidates(
        "test:*",
        {
            "probability_threshold": 0.7,
            "seasonal_threshold": 0.7,
            "warm_window": 300,
            "correlation_threshold": 0.8,
            "batch_size": 10
        }
    )
    
    # Should find candidates from different strategies
    patterns = {
        "time": "test:time" in candidates,
        "related": "test:related2" in candidates,
        "seasonal": "test:seasonal" in candidates,
        "ml": any(
            c.startswith("test:ml_") for c in candidates
        )
    }
    
    # At least two strategies should find candidates
    assert sum(patterns.values()) >= 2

@pytest.mark.asyncio
async def test_predictive_analytics(redis, metrics):
    """Test predictive analytics capabilities"""
    config = CacheConfig(
        warm_patterns={
            "test:*": {
                "probability_threshold": 0.7,
                "batch_size": 10
            }
        },
        warming_strategies=["ml"]
    )
    cache = Cache(redis, config, metrics)
    
    # Generate training data
    now = time.time()
    
    # Pattern 1: Hourly access during business hours
    for day in range(5):
        for hour in range(24):
            if 9 <= hour <= 17:
                await cache.set("test:pattern1", f"value_{day}_{hour}")
                cache.access_pattern.record_access(
                    "test:pattern1",
                    now + day * 24 * 3600 + hour * 3600
                )
    
    # Pattern 2: Periodic access every 5 minutes
    for i in range(100):
        if i % 5 == 0:
            await cache.set("test:pattern2", f"value_{i}")
            cache.access_pattern.record_access(
                "test:pattern2",
                now + i * 60
            )
    
    # Pattern 3: Random access with bursts
    for i in range(100):
        if random.random() < 0.3:
            await cache.set("test:pattern3", f"value_{i}")
            for _ in range(random.randint(1, 5)):
                cache.access_pattern.record_access(
                    "test:pattern3",
                    now + i * 60 + random.random() * 60
                )
    
    # Wait for model update
    await asyncio.sleep(1)
    
    # Test predictions
    strategy = MLBasedWarming(redis, cache.access_pattern)
    
    # Should predict business hours access
    current_time = datetime.now()
    if 9 <= current_time.hour <= 17:
        candidates = await strategy.get_warming_candidates(
            "test:pattern1",
            {"probability_threshold": 0.7}
        )
        assert "test:pattern1" in candidates
    
    # Should predict 5-minute periodic access
    candidates = await strategy.get_warming_candidates(
        "test:pattern2",
        {"probability_threshold": 0.7}
    )
    assert "test:pattern2" in candidates
    
    # Should handle random patterns appropriately
    candidates = await strategy.get_warming_candidates(
        "test:pattern3",
        {"probability_threshold": 0.9}  # Higher threshold for random
    )
    # Random pattern should be harder to predict
    assert len(candidates) <= 1