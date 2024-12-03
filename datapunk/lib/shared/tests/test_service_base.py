import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from prometheus_client import REGISTRY
from datapunk_shared.service import BaseService

@pytest.fixture
def service_config():
    return {
        'database_enabled': True,
        'cache_enabled': True,
        'messaging_enabled': True,
        'database': {
            'host': 'localhost',
            'port': 5432,
            'user': 'test',
            'password': 'test',
            'database': 'test_db'
        },
        'cache': {
            'host': 'localhost',
            'port': 6379
        },
        'messaging': {
            'host': 'localhost',
            'port': 5672
        },
        'volumes': {
            'data': '/data',
            'logs': '/logs'
        }
    }

@pytest.fixture
def mock_components():
    db_pool = AsyncMock()
    cache_manager = AsyncMock()
    message_broker = AsyncMock()
    metrics_collector = MagicMock()
    health_check = AsyncMock()
    volume_monitor = AsyncMock()
    
    # Configure health check responses
    db_pool.check_health.return_value = {"status": "healthy"}
    cache_manager.check_health.return_value = {"status": "healthy"}
    message_broker.check_health.return_value = {"status": "healthy"}
    volume_monitor.check_volumes.return_value = {
        "data": {"status": "healthy"},
        "logs": {"status": "healthy"}
    }
    
    return {
        'db_pool': db_pool,
        'cache_manager': cache_manager,
        'message_broker': message_broker,
        'metrics_collector': metrics_collector,
        'health_check': health_check,
        'volume_monitor': volume_monitor
    }

@pytest.fixture
async def base_service(service_config):
    service = BaseService("test-service", service_config)
    yield service
    await service.cleanup()

@pytest.mark.asyncio
async def test_service_initialization(base_service, service_config):
    """Test service initialization and component setup"""
    assert base_service.service_name == "test-service"
    assert base_service.config == service_config
    assert base_service.started_at is not None
    
    # Verify Prometheus metrics were created
    assert f'test-service_requests_total' in REGISTRY._names_to_collectors
    assert f'test-service_errors_total' in REGISTRY._names_to_collectors
    assert f'test-service_processing_seconds' in REGISTRY._names_to_collectors
    assert f'test-service_active_connections' in REGISTRY._names_to_collectors

@pytest.mark.asyncio
async def test_service_initialization_with_components(base_service, mock_components):
    """Test initialization of all service components"""
    with patch('datapunk_shared.service.DatabasePool') as mock_db, \
         patch('datapunk_shared.service.CacheManager') as mock_cache, \
         patch('datapunk_shared.service.MessageBroker') as mock_broker, \
         patch('datapunk_shared.service.HealthCheck') as mock_health, \
         patch('datapunk_shared.service.VolumeMonitor') as mock_volume:
        
        mock_db.create.return_value = mock_components['db_pool']
        mock_cache.create.return_value = mock_components['cache_manager']
        mock_broker.create.return_value = mock_components['message_broker']
        
        await base_service.initialize()
        
        # Verify components were initialized
        assert base_service.db is not None
        assert base_service.cache is not None
        assert base_service.broker is not None
        
        # Verify health check registration
        base_service.health.register_check.assert_called_once()

@pytest.mark.asyncio
async def test_service_cleanup(base_service, mock_components):
    """Test service cleanup and resource release"""
    base_service.db = mock_components['db_pool']
    base_service.cache = mock_components['cache_manager']
    base_service.broker = mock_components['message_broker']
    
    await base_service.cleanup()
    
    # Verify all components were closed
    base_service.db.close.assert_called_once()
    base_service.cache.close.assert_called_once()
    base_service.broker.close.assert_called_once()

@pytest.mark.asyncio
async def test_health_check(base_service, mock_components):
    """Test comprehensive health check functionality"""
    base_service.db = mock_components['db_pool']
    base_service.cache = mock_components['cache_manager']
    base_service.broker = mock_components['message_broker']
    base_service.volume_monitor = mock_components['volume_monitor']
    
    health_status = await base_service.check_health()
    
    assert health_status['service'] == "test-service"
    assert health_status['status'] == "healthy"
    assert isinstance(health_status['uptime'], float)
    assert health_status['checks']['database']['status'] == "healthy"
    assert health_status['checks']['cache']['status'] == "healthy"
    assert health_status['checks']['messaging']['status'] == "healthy"
    assert health_status['checks']['volumes']['data']['status'] == "healthy"

@pytest.mark.asyncio
async def test_health_check_with_failures(base_service, mock_components):
    """Test health check behavior with component failures"""
    base_service.db = mock_components['db_pool']
    base_service.cache = mock_components['cache_manager']
    base_service.broker = mock_components['message_broker']
    base_service.volume_monitor = mock_components['volume_monitor']
    
    # Simulate volume failure
    base_service.volume_monitor.check_volumes.return_value = {
        "data": {"status": "error", "message": "Disk full"},
        "logs": {"status": "healthy"}
    }
    
    health_status = await base_service.check_health()
    
    assert health_status['status'] == "unhealthy"
    assert health_status['checks']['volumes']['data']['status'] == "error"

@pytest.mark.asyncio
async def test_initialization_failure(base_service):
    """Test service initialization failure handling"""
    with patch('datapunk_shared.service.DatabasePool') as mock_db:
        mock_db.create.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await base_service.initialize()
        
        assert "Database connection failed" in str(exc_info.value)

def test_error_handling(base_service):
    """Test standardized error handling and metrics"""
    test_error = ValueError("Test error")
    test_context = {"operation": "test_op", "user_id": 123}
    
    # Get initial error count
    initial_count = REGISTRY.get_sample_value(
        'test-service_errors_total'
    ) or 0.0
    
    base_service.handle_error(test_error, test_context)
    
    # Verify error counter was incremented
    new_count = REGISTRY.get_sample_value('test-service_errors_total')
    assert new_count == initial_count + 1.0

@pytest.mark.asyncio
async def test_partial_initialization(service_config):
    """Test service initialization with only some components enabled"""
    # Disable some components
    config = service_config.copy()
    config['cache_enabled'] = False
    config['messaging_enabled'] = False
    
    service = BaseService("test-service", config)
    
    with patch('datapunk_shared.service.DatabasePool') as mock_db:
        mock_db.create.return_value = AsyncMock()
        await service.initialize()
        
        # Verify only database was initialized
        assert service.db is not None
        assert service.cache is None
        assert service.broker is None

@pytest.mark.asyncio
async def test_cleanup_with_errors(base_service, mock_components):
    """Test cleanup behavior when components fail to close"""
    base_service.db = mock_components['db_pool']
    base_service.cache = mock_components['cache_manager']
    base_service.broker = mock_components['message_broker']
    
    # Simulate cleanup failure
    base_service.db.close.side_effect = Exception("Cleanup failed")
    
    # Should not raise exception
    await base_service.cleanup()
    
    # Verify all components were attempted to be closed
    base_service.db.close.assert_called_once()
    base_service.cache.close.assert_called_once()
    base_service.broker.close.assert_called_once()

@pytest.mark.asyncio
async def test_service_uptime(base_service):
    """Test service uptime calculation"""
    # Set a known start time
    base_service.started_at = datetime.utcnow() - timedelta(hours=1)
    
    health_status = await base_service.check_health()
    
    # Uptime should be approximately 3600 seconds (1 hour)
    assert 3500 <= health_status['uptime'] <= 3700 