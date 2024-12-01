import pytest
import os
import tempfile
from typing import Dict, Any

# ... existing code ...

@pytest.fixture(scope="session")
def test_db_config() -> Dict[str, Any]:
    """Database configuration for tests."""
    return {
        'host': os.getenv('TEST_DB_HOST', 'localhost'),
        'port': int(os.getenv('TEST_DB_PORT', '5432')),
        'database': os.getenv('TEST_DB_NAME', 'test_db'),
        'user': os.getenv('TEST_DB_USER', 'test_user'),
        'password': os.getenv('TEST_DB_PASSWORD', 'test_pass')
    }

@pytest.fixture(scope="session")
def vector_dimension() -> int:
    """Default vector dimension for pgvector tests."""
    return 384  # Standard dimension for many embedding models

@pytest.fixture(scope="function")
def temp_table_name() -> str:
    """Generate temporary table name for tests."""
    return f"test_table_{next(tempfile._get_candidate_names())}"

# Add more fixtures as needed... 