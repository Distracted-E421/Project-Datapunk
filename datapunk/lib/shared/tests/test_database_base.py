import pytest
import asyncpg
from unittest.mock import AsyncMock, MagicMock, patch
from datapunk_shared.database import DatabasePool

@pytest.fixture
def db_config():
    return {
        'host': 'localhost',
        'port': 5432,
        'user': 'test_user',
        'password': 'test_password',
        'database': 'test_db',
        'min_connections': 5,
        'max_connections': 20,
        'command_timeout': 30.0,
        'max_queries': 1000,
        'max_cached_statement_lifetime': 300,
        'max_cached_statements': 500
    }

@pytest.fixture
def mock_pool():
    pool = AsyncMock()
    # Mock connection context manager
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    # Mock pool statistics attributes
    pool._holders = [1, 2, 3]  # 3 total connections
    pool._free = [1]  # 1 available connection
    pool._maxsize = 20
    return pool

@pytest.fixture
async def db_pool(db_config):
    pool = DatabasePool(db_config)
    yield pool
    await pool.close()

@pytest.mark.asyncio
async def test_database_pool_initialization(db_config):
    """Test database pool initialization with configuration"""
    with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
        pool = DatabasePool(db_config)
        await pool.initialize()
        
        mock_create_pool.assert_called_once_with(
            host='localhost',
            port=5432,
            user='test_user',
            password='test_password',
            database='test_db',
            min_size=5,
            max_size=20,
            command_timeout=30.0,
            max_queries=1000,
            max_cached_statement_lifetime=300,
            max_cached_statements=500
        )

@pytest.mark.asyncio
async def test_database_pool_initialization_retry(db_config):
    """Test database pool initialization with retry on failure"""
    with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.side_effect = [
            asyncpg.PostgresError("Connection failed"),
            AsyncMock()  # Succeed on second attempt
        ]
        
        pool = DatabasePool(db_config)
        await pool.initialize()
        
        assert mock_create_pool.call_count == 2

@pytest.mark.asyncio
async def test_database_execute(db_pool, mock_pool):
    """Test database query execution"""
    db_pool.pool = mock_pool
    query = "INSERT INTO test_table (column) VALUES ($1)"
    args = ("test_value",)
    
    await db_pool.execute(query, *args)
    
    mock_pool.acquire.return_value.__aenter__.return_value.execute.assert_called_once_with(
        query, *args
    )

@pytest.mark.asyncio
async def test_database_fetch(db_pool, mock_pool):
    """Test database query fetch"""
    db_pool.pool = mock_pool
    query = "SELECT * FROM test_table WHERE id = $1"
    args = (1,)
    expected_result = [{"id": 1, "value": "test"}]
    mock_pool.acquire.return_value.__aenter__.return_value.fetch.return_value = expected_result
    
    result = await db_pool.fetch(query, *args)
    
    assert result == expected_result
    mock_pool.acquire.return_value.__aenter__.return_value.fetch.assert_called_once_with(
        query, *args
    )

@pytest.mark.asyncio
async def test_database_execute_retry(db_pool, mock_pool):
    """Test database query execution with retry on failure"""
    db_pool.pool = mock_pool
    mock_conn = mock_pool.acquire.return_value.__aenter__.return_value
    mock_conn.execute.side_effect = [
        asyncpg.PostgresError("Query failed"),
        None  # Succeed on second attempt
    ]
    
    await db_pool.execute("SELECT 1")
    
    assert mock_conn.execute.call_count == 2

@pytest.mark.asyncio
async def test_database_fetch_retry(db_pool, mock_pool):
    """Test database query fetch with retry on failure"""
    db_pool.pool = mock_pool
    mock_conn = mock_pool.acquire.return_value.__aenter__.return_value
    mock_conn.fetch.side_effect = [
        asyncpg.PostgresError("Query failed"),
        []  # Succeed on second attempt
    ]
    
    result = await db_pool.fetch("SELECT 1")
    
    assert mock_conn.fetch.call_count == 2
    assert result == []

@pytest.mark.asyncio
async def test_database_execute_uninitialized():
    """Test handling of uninitialized database pool for execute"""
    pool = DatabasePool({})
    
    with pytest.raises(RuntimeError) as exc_info:
        await pool.execute("SELECT 1")
    assert "Database pool not initialized" in str(exc_info.value)

@pytest.mark.asyncio
async def test_database_fetch_uninitialized():
    """Test handling of uninitialized database pool for fetch"""
    pool = DatabasePool({})
    
    with pytest.raises(RuntimeError) as exc_info:
        await pool.fetch("SELECT 1")
    assert "Database pool not initialized" in str(exc_info.value)

@pytest.mark.asyncio
async def test_database_health_check_healthy(db_pool, mock_pool):
    """Test database health check when healthy"""
    db_pool.pool = mock_pool
    mock_conn = mock_pool.acquire.return_value.__aenter__.return_value
    
    with patch('time.time', side_effect=[0, 0.1]):  # Mock 100ms latency
        health = await db_pool.check_health()
    
    assert health["status"] == "healthy"
    assert health["latency"] == 0.1
    assert health["connections"] == {
        "used": 2,  # 3 total - 1 available
        "available": 1,
        "max": 20
    }
    mock_conn.execute.assert_called_once_with("SELECT 1")

@pytest.mark.asyncio
async def test_database_health_check_unhealthy_uninitialized():
    """Test database health check when pool is not initialized"""
    pool = DatabasePool({})
    
    health = await pool.check_health()
    
    assert health["status"] == "unhealthy"
    assert "Database pool not initialized" in health["error"]

@pytest.mark.asyncio
async def test_database_health_check_unhealthy_error(db_pool, mock_pool):
    """Test database health check when query fails"""
    db_pool.pool = mock_pool
    mock_conn = mock_pool.acquire.return_value.__aenter__.return_value
    mock_conn.execute.side_effect = asyncpg.PostgresError("Connection lost")
    
    health = await db_pool.check_health()
    
    assert health["status"] == "unhealthy"
    assert "Connection lost" in health["error"]

@pytest.mark.asyncio
async def test_database_close(db_pool, mock_pool):
    """Test database pool closure"""
    db_pool.pool = mock_pool
    
    await db_pool.close()
    
    mock_pool.close.assert_called_once()

@pytest.mark.asyncio
async def test_database_close_uninitialized():
    """Test database pool closure when not initialized"""
    pool = DatabasePool({})
    
    # Should not raise any errors
    await pool.close() 