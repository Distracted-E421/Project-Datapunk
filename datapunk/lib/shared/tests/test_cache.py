import pytest
from datetime import timedelta
import json
from datapunk_shared.cache import CacheManager, CacheError

@pytest.fixture
async def cache_manager(config, metrics, redis_client):
    """Create cache manager instance"""
    manager = CacheManager(config, metrics)
    manager.redis = redis_client
    return manager

@pytest.mark.asyncio
async def test_cache_set_get(cache_manager):
    """Test basic cache operations"""
    test_key = "test:key"
    test_value = {"name": "test", "value": 123}
    
    # Test set
    await cache_manager.set(test_key, test_value)
    
    # Test get
    result = await cache_manager.get(test_key)
    assert result == test_value

@pytest.mark.asyncio
async def test_cache_ttl(cache_manager):
    """Test cache TTL functionality"""
    test_key = "test:ttl"
    test_value = {"temporary": True}
    
    # Set with TTL
    await cache_manager.set(test_key, test_value, ttl=timedelta(seconds=1))
    
    # Verify value exists
    result = await cache_manager.get(test_key)
    assert result == test_value
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    
    # Verify value is gone
    result = await cache_manager.get(test_key)
    assert result is None

@pytest.mark.asyncio
async def test_cache_invalidate(cache_manager):
    """Test cache invalidation"""
    test_key = "test:invalidate"
    test_value = {"delete": "me"}
    
    # Set value
    await cache_manager.set(test_key, test_value)
    
    # Verify value exists
    result = await cache_manager.get(test_key)
    assert result == test_value
    
    # Invalidate
    await cache_manager.invalidate(test_key)
    
    # Verify value is gone
    result = await cache_manager.get(test_key)
    assert result is None

@pytest.mark.asyncio
async def test_cache_error_handling(cache_manager):
    """Test error handling"""
    # Force Redis error by closing connection
    await cache_manager.redis.close()
    
    with pytest.raises(CacheError):
        await cache_manager.get("test:error")