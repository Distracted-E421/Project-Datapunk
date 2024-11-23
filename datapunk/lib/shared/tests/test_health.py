import pytest
from datetime import datetime
from datapunk_shared.health import HealthCheck

@pytest.fixture
async def health_check():
    return HealthCheck("test-service")

@pytest.mark.asyncio
async def test_health_check(health_check):
    result = await health_check.check_health()
    
    assert result['status'] == 'healthy'
    assert 'timestamp' in result
    assert result['service'] == 'test-service'
    assert 'system' in result
    
    system_metrics = result['system']
    assert 'cpu_percent' in system_metrics
    assert 'memory_percent' in system_metrics
    assert 'disk_percent' in system_metrics

@pytest.mark.asyncio
async def test_dependency_check(health_check):
    # Mock dependency
    with aioresponses() as m:
        m.get('http://test-service/health', status=200)
        
        result = await health_check.check_dependency(
            'test-dependency',
            'http://test-service'
        )
        
        assert result['status'] == 'healthy'
        assert result['name'] == 'test-dependency'
        assert 'response_time' in result