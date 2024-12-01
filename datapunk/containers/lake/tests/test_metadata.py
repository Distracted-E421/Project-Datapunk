import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, patch
import json
import asyncpg

from ..src.metadata.core import (
    SchemaMetadata, StatisticsMetadata, LineageMetadata,
    QualityMetadata, QualityMetric, LineageNode, LineageEdge
)
from ..src.metadata.store import PostgresMetadataStore
from ..src.metadata.analyzer import MetadataAnalyzer

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test database configuration."""
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_pass'
    }

@pytest.fixture
async def metadata_store(test_config):
    """Create and initialize metadata store."""
    store = PostgresMetadataStore(test_config)
    await store.initialize()
    yield store
    await store.close()

@pytest.fixture
def metadata_analyzer(test_config):
    """Create metadata analyzer."""
    return MetadataAnalyzer(test_config)

class TestSchemaMetadata:
    """Test cases for schema metadata management."""
    
    @pytest.mark.asyncio
    async def test_schema_crud(self, metadata_store):
        """Test CRUD operations for schema metadata."""
        schema = SchemaMetadata(
            name="test_table",
            columns={
                "id": {
                    "type": "integer",
                    "nullable": False,
                    "primary_key": True
                },
                "name": {
                    "type": "varchar",
                    "nullable": True
                }
            },
            primary_key=["id"],
            foreign_keys=[],
            indexes=[],
            constraints=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1
        )
        
        # Test create/update
        await metadata_store.update_schema(schema)
        
        # Test read
        retrieved = await metadata_store.get_schema("test_table")
        assert retrieved is not None
        assert retrieved.name == schema.name
        assert retrieved.columns == schema.columns
        assert retrieved.primary_key == schema.primary_key
    
    @pytest.mark.asyncio
    async def test_schema_versioning(self, metadata_store):
        """Test schema versioning."""
        # Create initial version
        schema_v1 = SchemaMetadata(
            name="versioned_table",
            columns={"id": {"type": "integer"}},
            primary_key=["id"],
            foreign_keys=[],
            indexes=[],
            constraints=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1
        )
        await metadata_store.update_schema(schema_v1)
        
        # Update to new version
        schema_v2 = SchemaMetadata(
            name="versioned_table",
            columns={
                "id": {"type": "integer"},
                "new_column": {"type": "varchar"}
            },
            primary_key=["id"],
            foreign_keys=[],
            indexes=[],
            constraints=[],
            created_at=schema_v1.created_at,
            updated_at=datetime.utcnow(),
            version=2
        )
        await metadata_store.update_schema(schema_v2)
        
        # Verify latest version
        latest = await metadata_store.get_schema("versioned_table")
        assert latest.version == 2
        assert "new_column" in latest.columns

class TestStatisticsMetadata:
    """Test cases for statistics metadata management."""
    
    @pytest.mark.asyncio
    async def test_statistics_collection(self, metadata_analyzer):
        """Test collecting statistics metadata."""
        with patch('asyncpg.Connection') as mock_conn:
            # Mock basic table statistics
            mock_conn.fetchrow.return_value = {
                'total_bytes': 1000,
                'estimated_rows': 100
            }
            
            # Mock column statistics
            mock_conn.fetch.side_effect = [
                [{'column_name': 'id', 'data_type': 'integer'}],
                [{'index_name': 'test_idx', 'definition': 'CREATE INDEX...'}]
            ]
            
            stats = await metadata_analyzer.analyze_statistics("test_table")
            assert stats.table_name == "test_table"
            assert stats.row_count == 100
            assert stats.size_bytes == 1000
    
    @pytest.mark.asyncio
    async def test_column_statistics(self, metadata_analyzer):
        """Test collecting column-level statistics."""
        with patch('asyncpg.Connection') as mock_conn:
            mock_conn.fetchval.return_value = "integer"
            mock_conn.fetchrow.return_value = {
                'total_count': 100,
                'distinct_count': 90,
                'null_count': 5,
                'min_value': 1,
                'max_value': 100,
                'avg_value': 50.0
            }
            
            stats = await metadata_analyzer._analyze_column(
                mock_conn, "test_table", "id", None)
            
            assert stats['distinct_count'] == 90
            assert stats['null_count'] == 5
            assert stats['avg_value'] == 50.0

class TestQualityMetadata:
    """Test cases for data quality metadata management."""
    
    @pytest.mark.asyncio
    async def test_quality_metrics(self, metadata_analyzer):
        """Test collecting quality metrics."""
        with patch('asyncpg.Connection') as mock_conn:
            # Mock column information
            mock_conn.fetch.side_effect = [
                [{'column_name': 'id', 'data_type': 'integer'}],
                [{'column_name': 'id'}],  # unique columns
                []  # foreign keys
            ]
            
            # Mock null ratio check
            mock_conn.fetchval.return_value = 0.05  # 5% null values
            
            quality = await metadata_analyzer.analyze_quality("test_table")
            assert quality.table_name == "test_table"
            assert len(quality.metrics) > 0
            
            # Verify completeness metric
            completeness_metric = next(
                m for m in quality.metrics 
                if m.metric_name == "completeness_id"
            )
            assert completeness_metric.metric_value == 0.95
            assert completeness_metric.status == "passed"
    
    @pytest.mark.asyncio
    async def test_consistency_checks(self, metadata_analyzer):
        """Test data consistency checks."""
        with patch('asyncpg.Connection') as mock_conn:
            # Mock foreign key information
            mock_conn.fetch.return_value = [{
                'column_name': 'user_id',
                'foreign_table_name': 'users',
                'foreign_column_name': 'id'
            }]
            
            # Mock orphaned record check
            mock_conn.fetchval.side_effect = [0, 100]  # No orphaned records
            
            metrics = await metadata_analyzer._check_consistency(
                mock_conn, "test_table")
            
            assert len(metrics) == 1
            assert metrics[0].metric_name == "referential_integrity_user_id"
            assert metrics[0].metric_value == 1.0
            assert metrics[0].status == "passed"

class TestLineageMetadata:
    """Test cases for data lineage metadata management."""
    
    @pytest.mark.asyncio
    async def test_lineage_tracking(self, metadata_store):
        """Test tracking data lineage."""
        # Create lineage metadata
        source_node = LineageNode(
            id="source_table",
            type="source",
            name="source_table",
            properties={}
        )
        
        target_node = LineageNode(
            id="target_table",
            type="target",
            name="target_table",
            properties={}
        )
        
        edge = LineageEdge(
            source_id="source_table",
            target_id="target_table",
            operation="COPY",
            timestamp=datetime.utcnow(),
            properties={"rows_copied": 1000}
        )
        
        lineage = LineageMetadata(
            nodes=[source_node, target_node],
            edges=[edge],
            last_updated=datetime.utcnow()
        )
        
        # Test create/update
        await metadata_store.update_lineage(lineage)
        
        # Test read
        retrieved = await metadata_store.get_lineage("source_table")
        assert retrieved is not None
        assert len(retrieved.nodes) == 2
        assert len(retrieved.edges) == 1
        assert retrieved.edges[0].operation == "COPY"

@pytest.mark.asyncio
async def test_metadata_integration(metadata_store, metadata_analyzer):
    """Test integration between metadata store and analyzer."""
    with patch('asyncpg.Connection') as mock_conn:
        # Mock schema analysis
        mock_conn.fetch.return_value = [
            {'column_name': 'id', 'data_type': 'integer'}
        ]
        
        # Mock statistics collection
        mock_conn.fetchrow.return_value = {
            'total_bytes': 1000,
            'estimated_rows': 100
        }
        
        # Analyze table
        schema = await metadata_analyzer.analyze_schema("test_table")
        await metadata_store.update_schema(schema)
        
        stats = await metadata_analyzer.analyze_statistics("test_table")
        await metadata_store.update_statistics(stats)
        
        # Verify stored metadata
        stored_schema = await metadata_store.get_schema("test_table")
        assert stored_schema is not None
        assert "id" in stored_schema.columns
        
        stored_stats = await metadata_store.get_statistics("test_table")
        assert stored_stats is not None
        assert stored_stats.row_count == 100 