import pytest
from datetime import timedelta
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datapunk_shared.cache import CacheManager, CacheError
from datapunk_shared.config import BaseServiceConfig
from datapunk_shared.metrics import MetricsCollector

@pytest.fixture
def mock_redis():
    with patch('redis.asyncio.Redis') as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_config():
    config = MagicMock(spec=BaseServiceConfig)
    config.REDIS_HOST = "localhost"
    config.REDIS_PORT = 6379
    return config

@pytest.fixture
def mock_metrics():
    return MagicMock(spec=MetricsCollector)

@pytest.fixture
async def cache_manager(mock_config, mock_metrics, mock_redis):
    manager = CacheManager(mock_config, mock_metrics, prefix="test")
    await manager.initialize()
    return manager

@pytest.mark.asyncio
async def test_cache_initialization(mock_config, mock_metrics, mock_redis):
    """Test cache manager initialization and connection verification"""
    manager = CacheManager(mock_config, mock_metrics)
    await manager.initialize()
    
    mock_redis.ping.assert_called_once()
    assert manager.redis is not None

@pytest.mark.asyncio
async def test_cache_get_hit(cache_manager, mock_redis):
    """Test successful cache get operation"""
    test_data = {"key": "value"}
    mock_redis.get.return_value = json.dumps(test_data)
    
    result = await cache_manager.get("test_key")
    
    mock_redis.get.assert_called_once_with("test:test_key")
    assert result == test_data
    cache_manager.metrics.track_operation.assert_called_with(
        operation_type="cache_get",
        status="success"
    )

@pytest.mark.asyncio
async def test_cache_get_miss(cache_manager, mock_redis):
    """Test cache miss scenario"""
    mock_redis.get.return_value = None
    
    result = await cache_manager.get("test_key")
    
    assert result is None
    cache_manager.metrics.track_operation.assert_called_with(
        operation_type="cache_get",
        status="miss"
    )

@pytest.mark.asyncio
async def test_cache_get_error(cache_manager, mock_redis):
    """Test error handling in get operation"""
    mock_redis.get.side_effect = Exception("Redis error")
    
    with pytest.raises(CacheError) as exc_info:
        await cache_manager.get("test_key")
    
    assert "Failed to get key" in str(exc_info.value)
    cache_manager.metrics.track_operation.assert_called_with(
        operation_type="cache_get",
        status="error"
    )

@pytest.mark.asyncio
async def test_cache_set_success(cache_manager, mock_redis):
    """Test successful cache set operation"""
    test_data = {"key": "value"}
    
    await cache_manager.set("test_key", test_data)
    
    mock_redis.set.assert_called_once_with(
        "test:test_key",
        json.dumps(test_data),
        ex=None
    )
    cache_manager.metrics.track_operation.assert_called_with(
        operation_type="cache_set",
        status="success"
    )

@pytest.mark.asyncio
async def test_cache_set_with_ttl(cache_manager, mock_redis):
    """Test cache set with TTL specified"""
    test_data = {"key": "value"}
    ttl = timedelta(minutes=5)
    
    await cache_manager.set("test_key", test_data, ttl=ttl)
    
    mock_redis.set.assert_called_once_with(
        "test:test_key",
        json.dumps(test_data),
        ex=300  # 5 minutes in seconds
    )

@pytest.mark.asyncio
async def test_cache_set_error(cache_manager, mock_redis):
    """Test error handling in set operation"""
    mock_redis.set.side_effect = Exception("Redis error")
    
    with pytest.raises(CacheError) as exc_info:
        await cache_manager.set("test_key", "test_value")
    
    assert "Failed to set key" in str(exc_info.value)
    cache_manager.metrics.track_operation.assert_called_with(
        operation_type="cache_set",
        status="error"
    )

@pytest.mark.asyncio
async def test_cache_invalidate_success(cache_manager, mock_redis):
    """Test successful cache invalidation"""
    await cache_manager.invalidate("test_key")
    
    mock_redis.delete.assert_called_once_with("test:test_key")
    cache_manager.metrics.track_operation.assert_called_with(
        operation_type="cache_invalidate",
        status="success"
    )

@pytest.mark.asyncio
async def test_cache_invalidate_error(cache_manager, mock_redis):
    """Test error handling in invalidate operation"""
    mock_redis.delete.side_effect = Exception("Redis error")
    
    with pytest.raises(CacheError) as exc_info:
        await cache_manager.invalidate("test_key")
    
    assert "Failed to invalidate key" in str(exc_info.value)
    cache_manager.metrics.track_operation.assert_called_with(
        operation_type="cache_invalidate",
        status="error"
    )

@pytest.mark.asyncio
async def test_cache_prefix_handling(cache_manager, mock_redis):
    """Test proper handling of cache key prefixes"""
    await cache_manager.get("key1")
    await cache_manager.set("key2", "value")
    await cache_manager.invalidate("key3")
    
    mock_redis.get.assert_called_with("test:key1")
    mock_redis.set.assert_called_with("test:key2", '"value"', ex=None)
    mock_redis.delete.assert_called_with("test:key3") 