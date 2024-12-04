import pytest
import asyncio
import asyncpg
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from datapunk_shared.database.pool import PoolConfig, ConnectionPool
from datapunk_shared.monitoring import MetricsCollector

@pytest.fixture
async def pool_config():
    return PoolConfig(
        min_size=2,
        max_size=5,
        max_queries=1000
    )

@pytest.fixture
async def metrics_collector():
    return Mock(spec=MetricsCollector)

@pytest.fixture
async def connection_pool(pool_config, metrics_collector):
    pool = ConnectionPool(
        config=pool_config,
        metrics_collector=metrics_collector,
        dsn="postgresql://test:test@localhost:5432/test_db"
    )
    yield pool
    await pool.close()

@pytest.mark.asyncio
async def test_pool_initialization(connection_pool, pool_config):
    assert connection_pool.config == pool_config
    assert connection_pool.size == 0
    assert not connection_pool.is_closed

@pytest.mark.asyncio
async def test_pool_connection_acquisition():
    with patch('asyncpg.create_pool') as mock_create_pool:
        mock_pool = Mock()
        mock_create_pool.return_value = mock_pool
        
        config = PoolConfig(min_size=1, max_size=2)
        pool = ConnectionPool(
            config=config,
            metrics_collector=Mock(),
            dsn="postgresql://test:test@localhost:5432/test_db"
        )
        
        await pool.initialize()
        mock_create_pool.assert_called_once()

@pytest.mark.asyncio
async def test_pool_health_check(connection_pool):
    with patch.object(connection_pool, '_validate_connection') as mock_validate:
        mock_validate.return_value = True
        assert await connection_pool.check_health()
        
        mock_validate.return_value = False
        assert not await connection_pool.check_health()

@pytest.mark.asyncio
async def test_pool_metrics_collection(connection_pool, metrics_collector):
    await connection_pool.initialize()
    metrics_collector.record_pool_size.assert_called()
    metrics_collector.record_connection_latency.assert_called()

@pytest.mark.asyncio
async def test_pool_max_connections(connection_pool):
    with patch('asyncpg.create_pool'):
        await connection_pool.initialize()
        connections = []
        
        # Try to acquire more than max_size connections
        for _ in range(connection_pool.config.max_size + 1):
            if len(connections) < connection_pool.config.max_size:
                conn = await connection_pool.acquire()
                connections.append(conn)
            else:
                with pytest.raises(Exception):
                    await connection_pool.acquire()

@pytest.mark.asyncio
async def test_pool_connection_release(connection_pool):
    with patch('asyncpg.create_pool'):
        await connection_pool.initialize()
        conn = await connection_pool.acquire()
        
        initial_size = connection_pool.size
        await connection_pool.release(conn)
        assert connection_pool.size == initial_size

@pytest.mark.asyncio
async def test_pool_prepared_statements(connection_pool):
    with patch('asyncpg.create_pool'):
        await connection_pool.initialize()
        
        # Test prepared statement caching
        stmt_name = "test_stmt"
        stmt_query = "SELECT 1"
        
        conn = await connection_pool.acquire()
        await connection_pool.prepare_statement(conn, stmt_name, stmt_query)
        assert stmt_name in connection_pool.prepared_statements
        
        await connection_pool.release(conn)

@pytest.mark.asyncio
async def test_pool_cleanup(connection_pool):
    with patch('asyncpg.create_pool'):
        await connection_pool.initialize()
        await connection_pool.close()
        
        assert connection_pool.is_closed
        with pytest.raises(Exception):
            await connection_pool.acquire() 