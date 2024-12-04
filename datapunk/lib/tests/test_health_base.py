import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import psutil
import aiohttp
from prometheus_client import REGISTRY
from datapunk_shared.health import HealthCheck

@pytest.fixture
def health_checker():
    return HealthCheck("test-service")

@pytest.fixture
def mock_psutil():
    with patch('psutil.cpu_percent') as cpu_mock, \
         patch('psutil.virtual_memory') as mem_mock, \
         patch('psutil.disk_usage') as disk_mock:
        
        # Mock CPU usage
        cpu_mock.return_value = 45.2
        
        # Mock memory usage
        memory = MagicMock()
        memory.percent = 60.5
        mem_mock.return_value = memory
        
        # Mock disk usage
        disk = MagicMock()
        disk.percent = 75.8
        disk_mock.return_value = disk
        
        yield {
            'cpu': cpu_mock,
            'memory': mem_mock,
            'disk': disk_mock
        }

@pytest.fixture
def mock_aiohttp_session():
    async def mock_get(url):
        response = AsyncMock()
        if url.endswith("/health"):
            response.status = 200
            response.elapsed.total_seconds.return_value = 0.1
        else:
            response.status = 404
        return response
    
    session = AsyncMock()
    session.get = mock_get
    return session

@pytest.mark.asyncio
async def test_health_check_initialization(health_checker):
    """Test health checker initialization and metrics setup"""
    assert health_checker.service_name == "test-service"
    assert health_checker.last_check is None
    
    # Verify Prometheus metrics were created
    assert 'health_check_total' in REGISTRY._names_to_collectors
    assert 'health_status' in REGISTRY._names_to_collectors

@pytest.mark.asyncio
async def test_health_check_success(health_checker, mock_psutil):
    """Test successful health check with system metrics"""
    health_data = await health_checker.check_health()
    
    assert health_data['status'] == 'healthy'
    assert health_data['service'] == 'test-service'
    assert isinstance(health_data['timestamp'], str)
    
    system_metrics = health_data['system']
    assert system_metrics['cpu_percent'] == 45.2
    assert system_metrics['memory_percent'] == 60.5
    assert system_metrics['disk_percent'] == 75.8
    
    # Verify last check timestamp was updated
    assert health_checker.last_check is not None
    assert isinstance(health_checker.last_check, datetime)

@pytest.mark.asyncio
async def test_health_check_metrics_update(health_checker, mock_psutil):
    """Test Prometheus metrics updates during health check"""
    await health_checker.check_health()
    
    # Get current metric values
    counter = REGISTRY.get_sample_value(
        'health_check_total',
        {'service': 'test-service', 'status': 'success'}
    )
    status = REGISTRY.get_sample_value(
        'health_status',
        {'service': 'test-service', 'component': 'system'}
    )
    
    assert counter == 1.0  # One successful check
    assert status == 1.0  # System is healthy

@pytest.mark.asyncio
async def test_health_check_failure(health_checker):
    """Test health check behavior during system metric collection failure"""
    with patch('psutil.cpu_percent', side_effect=Exception("CPU check failed")):
        health_data = await health_checker.check_health()
        
        assert health_data['status'] == 'unhealthy'
        assert 'CPU check failed' in health_data['error']
        
        # Verify failure metrics
        counter = REGISTRY.get_sample_value(
            'health_check_total',
            {'service': 'test-service', 'status': 'failure'}
        )
        status = REGISTRY.get_sample_value(
            'health_status',
            {'service': 'test-service', 'component': 'system'}
        )
        
        assert counter == 1.0  # One failed check
        assert status == 0.0  # System is unhealthy

@pytest.mark.asyncio
async def test_dependency_check_success(health_checker):
    """Test successful dependency health check"""
    with patch('aiohttp.ClientSession') as mock_session:
        session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = session_instance
        
        response = AsyncMock()
        response.status = 200
        response.elapsed.total_seconds.return_value = 0.1
        
        session_instance.get.return_value.__aenter__.return_value = response
        
        health_data = await health_checker.check_dependency(
            name="test-dependency",
            url="http://test-service"
        )
        
        assert health_data['status'] == 'healthy'
        assert health_data['name'] == 'test-dependency'
        assert health_data['response_time'] == 0.1
        
        # Verify dependency health metric
        status = REGISTRY.get_sample_value(
            'health_status',
            {'service': 'test-service', 'component': 'test-dependency'}
        )
        assert status == 1.0

@pytest.mark.asyncio
async def test_dependency_check_failure(health_checker):
    """Test dependency health check failure handling"""
    with patch('aiohttp.ClientSession') as mock_session:
        session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = session_instance
        
        # Simulate connection error
        session_instance.get.side_effect = aiohttp.ClientError("Connection failed")
        
        health_data = await health_checker.check_dependency(
            name="test-dependency",
            url="http://test-service"
        )
        
        assert health_data['status'] == 'unhealthy'
        assert health_data['name'] == 'test-dependency'
        assert 'Connection failed' in health_data['error']
        
        # Verify dependency health metric
        status = REGISTRY.get_sample_value(
            'health_status',
            {'service': 'test-service', 'component': 'test-dependency'}
        )
        assert status == 0.0

@pytest.mark.asyncio
async def test_dependency_check_unhealthy_status(health_checker):
    """Test dependency health check with unhealthy HTTP status"""
    with patch('aiohttp.ClientSession') as mock_session:
        session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = session_instance
        
        response = AsyncMock()
        response.status = 500
        response.elapsed.total_seconds.return_value = 0.1
        
        session_instance.get.return_value.__aenter__.return_value = response
        
        health_data = await health_checker.check_dependency(
            name="test-dependency",
            url="http://test-service"
        )
        
        assert health_data['status'] == 'unhealthy'
        assert health_data['name'] == 'test-dependency'
        
        # Verify dependency health metric
        status = REGISTRY.get_sample_value(
            'health_status',
            {'service': 'test-service', 'component': 'test-dependency'}
        )
        assert status == 0.0

@pytest.mark.asyncio
async def test_multiple_health_checks(health_checker, mock_psutil):
    """Test multiple health checks and metric accumulation"""
    # Perform multiple health checks
    for _ in range(3):
        await health_checker.check_health()
    
    # Verify metrics accumulated correctly
    counter = REGISTRY.get_sample_value(
        'health_check_total',
        {'service': 'test-service', 'status': 'success'}
    )
    assert counter == 3.0  # Three successful checks

@pytest.mark.asyncio
async def test_system_metrics_thresholds(health_checker):
    """Test system metrics with different threshold values"""
    with patch('psutil.cpu_percent') as cpu_mock, \
         patch('psutil.virtual_memory') as mem_mock, \
         patch('psutil.disk_usage') as disk_mock:
        
        # Set high resource usage
        cpu_mock.return_value = 95.0
        memory = MagicMock()
        memory.percent = 90.0
        mem_mock.return_value = memory
        disk = MagicMock()
        disk.percent = 95.0
        disk_mock.return_value = disk
        
        health_data = await health_checker.check_health()
        
        assert health_data['status'] == 'healthy'  # Still healthy despite high usage
        assert health_data['system']['cpu_percent'] == 95.0
        assert health_data['system']['memory_percent'] == 90.0
        assert health_data['system']['disk_percent'] == 95.0 