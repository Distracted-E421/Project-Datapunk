import pytest
from datetime import datetime
from datapunk_shared.database import DatabaseManager, DatabaseError

@pytest.fixture
async def db_manager(config, metrics, pg_pool):
    """Create database manager instance"""
    manager = DatabaseManager(config, metrics)
    manager.pool = pg_pool
    return manager

@pytest.mark.asyncio
async def test_execute(db_manager):
    """Test basic query execution"""
    # Create test table
    await db_manager.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Insert data
    result = await db_manager.execute(
        "INSERT INTO test_table (name) VALUES ($1) RETURNING id",
        "test_record"
    )
    
    assert isinstance(result, int)
    assert result > 0

@pytest.mark.asyncio
async def test_fetch_all(db_manager):
    """Test fetching multiple rows"""
    # Insert test data
    await db_manager.execute(
        "INSERT INTO test_table (name) VALUES ($1), ($2)",
        "record1", "record2"
    )
    
    # Fetch all records
    results = await db_manager.fetch_all(
        "SELECT * FROM test_table ORDER BY id"
    )
    
    assert len(results) >= 2
    assert all(isinstance(r, dict) for r in results)
    assert results[-2]["name"] == "record1"
    assert results[-1]["name"] == "record2"

@pytest.mark.asyncio
async def test_fetch_one(db_manager):
    """Test fetching single row"""
    # Insert test data
    await db_manager.execute(
        "INSERT INTO test_table (name) VALUES ($1)",
        "single_record"
    )
    
    # Fetch one record
    result = await db_manager.fetch_one(
        "SELECT * FROM test_table WHERE name = $1",
        "single_record"
    )
    
    assert isinstance(result, dict)
    assert result["name"] == "single_record"

@pytest.mark.asyncio
async def test_database_error_handling(db_manager):
    """Test error handling"""
    with pytest.raises(DatabaseError):
        await db_manager.execute("SELECT * FROM nonexistent_table") 