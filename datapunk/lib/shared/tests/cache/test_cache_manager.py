import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from datetime import datetime, timedelta
import aioredis

from datapunk_shared.cache.cache_manager import (
    CacheManager,
    CacheConfig,
    CacheStrategy,
    InvalidationStrategy,
    CacheEntry,
    ServiceError,
    ErrorCategory
)

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.close = AsyncMock()
    return redis

@pytest.fixture
def mock_metrics():
    """Mock metrics client."""
    metrics = Mock()
    metrics.increment_counter = AsyncMock()
    metrics.record_histogram = AsyncMock()
    return metrics

@pytest.fixture
def cache_config():
    """Create cache configuration."""
    return CacheConfig(
        strategy=CacheStrategy.WRITE_THROUGH,
        invalidation_strategy=InvalidationStrategy.TTL,
        ttl=3600,
        namespace="test"
    )

@pytest.fixture
def write_behind_config():
    """Create write-behind cache configuration."""
    return CacheConfig(
        strategy=CacheStrategy.WRITE_BEHIND,
        invalidation_strategy=InvalidationStrategy.TTL,
        ttl=3600,
        write_buffer_size=100,
        write_interval=5,
        namespace="test"
    )

@pytest.fixture
async def cache_manager(cache_config, mock_redis, mock_metrics):
    """Create cache manager instance."""
    with patch('aioredis.from_url', return_value=mock_redis):
        manager = CacheManager(
            config=cache_config,
            redis_url="redis://localhost",
            metrics_client=mock_metrics
        )
        yield manager
        await manager.stop()

class TestCacheManager:
    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_manager, mock_redis):
        """Test successful cache get with existing entry."""
        test_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat()
        )
        mock_redis.get.return_value = json.dumps(test_entry.__dict__)
        
        result = await cache_manager.get("test_key")
        
        assert result == "test_value"
        mock_redis.get.assert_called_once_with("test:test_key")

    @pytest.mark.asyncio
    async def test_get_cache_miss_with_fetch(self, cache_manager, mock_redis):
        """Test cache miss with fetch function."""
        mock_redis.get.return_value = None
        fetch_func = AsyncMock(return_value="fetched_value")
        
        result = await cache_manager.get("test_key", fetch_func)
        
        assert result == "fetched_value"
        fetch_func.assert_called_once()
        assert mock_redis.set.called

    @pytest.mark.asyncio
    async def test_get_expired_entry(self, cache_manager, mock_redis):
        """Test handling of expired cache entry."""
        test_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() - timedelta(hours=1)).isoformat()
        )
        mock_redis.get.return_value = json.dumps(test_entry.__dict__)
        
        result = await cache_manager.get("test_key")
        
        assert result is None
        assert mock_redis.delete.called

    @pytest.mark.asyncio
    async def test_set_write_through(self, cache_manager, mock_redis):
        """Test write-through cache set."""
        success = await cache_manager.set("test_key", "test_value")
        
        assert success is True
        assert mock_redis.set.called
        set_args = mock_redis.set.call_args[0]
        assert set_args[0] == "test:test_key"
        entry_dict = json.loads(set_args[1])
        assert entry_dict["value"] == "test_value"

    @pytest.mark.asyncio
    async def test_set_write_behind(self, write_behind_config, mock_redis, mock_metrics):
        """Test write-behind cache set."""
        with patch('aioredis.from_url', return_value=mock_redis):
            manager = CacheManager(
                config=write_behind_config,
                redis_url="redis://localhost",
                metrics_client=mock_metrics
            )
            
            success = await manager.set("test_key", "test_value")
            
            assert success is True
            assert "test:test_key" in manager._write_buffer
            assert manager._write_buffer["test:test_key"] == "test_value"
            
            await manager.stop()

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_manager, mock_redis):
        """Test cache set with custom TTL."""
        custom_ttl = 1800
        success = await cache_manager.set("test_key", "test_value", ttl=custom_ttl)
        
        assert success is True
        mock_redis.set.assert_called_once()
        assert mock_redis.set.call_args[1]["ex"] == custom_ttl

    @pytest.mark.asyncio
    async def test_get_error_handling(self, cache_manager, mock_redis):
        """Test error handling in get operation."""
        mock_redis.get.side_effect = Exception("Redis error")
        
        with pytest.raises(ServiceError) as exc_info:
            await cache_manager.get("test_key")
        
        assert exc_info.value.category == ErrorCategory.CACHE
        assert "Redis error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_set_error_handling(self, cache_manager, mock_redis):
        """Test error handling in set operation."""
        mock_redis.set.side_effect = Exception("Redis error")
        
        with pytest.raises(ServiceError) as exc_info:
            await cache_manager.set("test_key", "test_value")
        
        assert exc_info.value.category == ErrorCategory.CACHE
        assert "Redis error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_metrics_recording(self, cache_manager, mock_redis, mock_metrics):
        """Test metrics recording for cache operations."""
        test_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat()
        )
        mock_redis.get.return_value = json.dumps(test_entry.__dict__)
        
        await cache_manager.get("test_key")
        
        assert mock_metrics.increment_counter.called
        assert mock_metrics.record_histogram.called 