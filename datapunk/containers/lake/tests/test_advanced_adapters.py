import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

from ..src.query.federation.adapters.timescale_advanced import (
    TimescaleDBAdvancedAdapter,
    ContinuousAggregateConfig,
    RetentionPolicy,
    CompressionPolicy
)
from ..src.query.federation.adapters.pgvector_advanced import (
    PgVectorAdvancedAdapter,
    VectorIndexConfig,
    HybridSearchConfig,
    VectorSimilarityMetric
)

@pytest.fixture
def timescale_adapter():
    """Create TimescaleDB advanced adapter instance."""
    return TimescaleDBAdvancedAdapter(
        connection_config={
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
    )

@pytest.fixture
def pgvector_adapter():
    """Create pgvector advanced adapter instance."""
    return PgVectorAdvancedAdapter(
        connection_config={
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
    )

class TestTimescaleDBAdvancedAdapter:
    """Test cases for TimescaleDB advanced features."""
    
    def test_continuous_aggregate_creation(self, timescale_adapter):
        """Test creating continuous aggregates."""
        config = ContinuousAggregateConfig(
            view_name="daily_metrics",
            source_table="raw_metrics",
            time_column="timestamp",
            aggregates=[
                {"column": "value", "func": "avg", "alias": "daily_avg"},
                {"column": "value", "func": "max", "alias": "daily_max"}
            ],
            bucket_interval="1 day",
            materialization_interval="1 hour"
        )
        
        with patch.object(timescale_adapter, '_execute_query') as mock_execute:
            timescale_adapter.create_continuous_aggregate(config)
            
            # Verify correct SQL was generated
            call_args = mock_execute.call_args[0][0]
            assert "CREATE MATERIALIZED VIEW" in call_args
            assert "daily_metrics" in call_args
            assert "time_bucket" in call_args
            assert "WITH (timescaledb.continuous)" in call_args
    
    def test_retention_policy_management(self, timescale_adapter):
        """Test retention policy management."""
        policy = RetentionPolicy(
            table_name="metrics",
            retention_interval="30 days",
            cascade=True
        )
        
        with patch.object(timescale_adapter, '_execute_query') as mock_execute:
            # Test adding policy
            timescale_adapter.add_retention_policy(policy)
            add_call = mock_execute.call_args_list[0][0][0]
            assert "ADD RETENTION POLICY" in add_call
            assert "DROP AFTER" in add_call
            
            # Test removing policy
            timescale_adapter.remove_retention_policy(policy.table_name)
            remove_call = mock_execute.call_args_list[1][0][0]
            assert "REMOVE RETENTION POLICY" in remove_call
    
    def test_compression_policy_management(self, timescale_adapter):
        """Test compression policy management."""
        policy = CompressionPolicy(
            table_name="metrics",
            compress_after="7 days",
            segment_by=["device_id"],
            order_by=["timestamp DESC"]
        )
        
        with patch.object(timescale_adapter, '_execute_query') as mock_execute:
            timescale_adapter.add_compression_policy(policy)
            
            call_args = mock_execute.call_args[0][0]
            assert "ALTER TABLE metrics SET" in call_args
            assert "timescaledb.compress" in call_args
            assert "timescaledb.compress_segmentby" in call_args
            assert "timescaledb.compress_orderby" in call_args
    
    def test_refresh_continuous_aggregate(self, timescale_adapter):
        """Test refreshing continuous aggregates."""
        view_name = "daily_metrics"
        window = {
            "start": datetime.now() - timedelta(days=7),
            "end": datetime.now()
        }
        
        with patch.object(timescale_adapter, '_execute_query') as mock_execute:
            timescale_adapter.refresh_continuous_aggregate(view_name, window)
            
            call_args = mock_execute.call_args[0][0]
            assert "CALL refresh_continuous_aggregate" in call_args
            assert view_name in call_args
    
    def test_error_handling_continuous_aggregate(self, timescale_adapter):
        """Test error handling in continuous aggregate creation."""
        config = ContinuousAggregateConfig(
            view_name="invalid_view",
            source_table="nonexistent_table",
            time_column="timestamp",
            aggregates=[{"column": "value", "func": "avg"}],
            bucket_interval="1 day"
        )
        
        with patch.object(timescale_adapter, '_execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Table does not exist")
            
            with pytest.raises(Exception) as exc_info:
                timescale_adapter.create_continuous_aggregate(config)
            assert "Table does not exist" in str(exc_info.value)
    
    def test_materialization_policy(self, timescale_adapter):
        """Test materialization policy management."""
        view_name = "hourly_metrics"
        policy = {
            "start_offset": "1 month",
            "end_offset": "1 hour",
            "schedule_interval": "1 hour"
        }
        
        with patch.object(timescale_adapter, '_execute_query') as mock_execute:
            timescale_adapter.set_materialization_policy(view_name, policy)
            
            call_args = mock_execute.call_args[0][0]
            assert "ALTER MATERIALIZED VIEW" in call_args
            assert "SET (timescaledb.materialization_schedule_interval" in call_args
    
    def test_hypertable_management(self, timescale_adapter):
        """Test hypertable management operations."""
        table_name = "sensor_data"
        
        with patch.object(timescale_adapter, '_execute_query') as mock_execute:
            # Test hypertable creation
            timescale_adapter.create_hypertable(
                table_name=table_name,
                time_column="timestamp",
                partitioning_column="sensor_id",
                number_partitions=4
            )
            
            create_call = mock_execute.call_args[0][0]
            assert "SELECT create_hypertable" in create_call
            assert "number_partitions => 4" in create_call
            
            # Test adding space dimension
            timescale_adapter.add_space_dimension(
                table_name=table_name,
                column_name="location_id",
                number_partitions=2
            )
            
            space_call = mock_execute.call_args_list[1][0][0]
            assert "SELECT add_dimension" in space_call
            assert "number_partitions => 2" in space_call

class TestPgVectorAdvancedAdapter:
    """Test cases for pgvector advanced features."""
    
    def test_vector_index_creation(self, pgvector_adapter):
        """Test creating vector indexes."""
        config = VectorIndexConfig(
            table_name="embeddings",
            vector_column="embedding",
            index_type="ivfflat",
            index_params={
                "lists": 100,
                "probes": 10
            }
        )
        
        with patch.object(pgvector_adapter, '_execute_query') as mock_execute:
            pgvector_adapter.create_vector_index(config)
            
            call_args = mock_execute.call_args[0][0]
            assert "CREATE INDEX" in call_args
            assert "USING ivfflat" in call_args
            assert "embeddings" in call_args
            assert "embedding" in call_args
    
    def test_hybrid_search(self, pgvector_adapter):
        """Test hybrid search functionality."""
        config = HybridSearchConfig(
            vector_column="embedding",
            metadata_columns=["title", "description"],
            vector_weight=0.7,
            text_weight=0.3,
            max_results=10
        )
        
        query_vector = np.random.rand(384).astype(np.float32)
        text_query = "machine learning"
        
        with patch.object(pgvector_adapter, '_execute_query') as mock_execute:
            mock_execute.return_value = [
                {"id": 1, "score": 0.9},
                {"id": 2, "score": 0.8}
            ]
            
            results = pgvector_adapter.hybrid_search(
                table_name="documents",
                query_vector=query_vector,
                text_query=text_query,
                config=config
            )
            
            call_args = mock_execute.call_args[0][0]
            assert "SELECT" in call_args
            assert "<->" in call_args  # Vector similarity operator
            assert "ts_rank" in call_args  # Text search ranking
            assert len(results) == 2
    
    def test_vector_similarity_search(self, pgvector_adapter):
        """Test vector similarity search with different metrics."""
        query_vector = np.random.rand(384).astype(np.float32)
        
        with patch.object(pgvector_adapter, '_execute_query') as mock_execute:
            mock_execute.return_value = [
                {"id": 1, "distance": 0.1},
                {"id": 2, "distance": 0.2}
            ]
            
            # Test L2 distance
            results = pgvector_adapter.similarity_search(
                table_name="embeddings",
                query_vector=query_vector,
                metric=VectorSimilarityMetric.L2,
                limit=10
            )
            l2_call = mock_execute.call_args_list[0][0][0]
            assert "<->" in l2_call
            
            # Test cosine distance
            results = pgvector_adapter.similarity_search(
                table_name="embeddings",
                query_vector=query_vector,
                metric=VectorSimilarityMetric.COSINE,
                limit=10
            )
            cosine_call = mock_execute.call_args_list[1][0][0]
            assert "<=>" in cosine_call
    
    def test_batch_vector_operations(self, pgvector_adapter):
        """Test batch vector operations."""
        vectors = [np.random.rand(384).astype(np.float32) for _ in range(5)]
        metadata = [{"text": f"doc_{i}"} for i in range(5)]
        
        with patch.object(pgvector_adapter, '_execute_query') as mock_execute:
            # Test batch insert
            pgvector_adapter.batch_insert_vectors(
                table_name="embeddings",
                vectors=vectors,
                metadata=metadata
            )
            
            insert_call = mock_execute.call_args[0][0]
            assert "INSERT INTO embeddings" in insert_call
            assert "vector" in insert_call
            
            # Test batch similarity search
            results = pgvector_adapter.batch_similarity_search(
                table_name="embeddings",
                query_vectors=vectors[:2],
                limit=5
            )
            
            search_call = mock_execute.call_args[0][0]
            assert "SELECT" in search_call
            assert "UNNEST" in search_call  # For batch processing
    
    def test_error_handling_vector_operations(self, pgvector_adapter):
        """Test error handling in vector operations."""
        invalid_vector = np.random.rand(100).astype(np.float32)  # Wrong dimension
        
        with patch.object(pgvector_adapter, '_execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Vector dimension mismatch")
            
            with pytest.raises(Exception) as exc_info:
                pgvector_adapter.similarity_search(
                    table_name="embeddings",
                    query_vector=invalid_vector,
                    metric=VectorSimilarityMetric.L2
                )
            assert "Vector dimension mismatch" in str(exc_info.value)
    
    def test_advanced_index_operations(self, pgvector_adapter):
        """Test advanced vector index operations."""
        with patch.object(pgvector_adapter, '_execute_query') as mock_execute:
            # Test index rebuild
            pgvector_adapter.rebuild_vector_index(
                table_name="embeddings",
                index_name="embedding_idx"
            )
            rebuild_call = mock_execute.call_args[0][0]
            assert "REINDEX INDEX" in rebuild_call
            
            # Test index statistics
            mock_execute.return_value = [{"index_size": "1 GB", "row_count": 1000000}]
            stats = pgvector_adapter.get_index_statistics("embedding_idx")
            assert stats["index_size"] == "1 GB"
            assert stats["row_count"] == 1000000
    
    def test_approximate_nearest_neighbors(self, pgvector_adapter):
        """Test approximate nearest neighbors search."""
        query_vector = np.random.rand(384).astype(np.float32)
        
        with patch.object(pgvector_adapter, '_execute_query') as mock_execute:
            mock_execute.return_value = [
                {"id": i, "distance": 0.1 * i} for i in range(5)
            ]
            
            # Test with different index types
            for index_type in ["ivfflat", "hnsw"]:
                results = pgvector_adapter.ann_search(
                    table_name="embeddings",
                    query_vector=query_vector,
                    index_type=index_type,
                    num_lists=100,
                    num_probes=10,
                    ef_search=40
                )
                
                call_args = mock_execute.call_args[0][0]
                if index_type == "ivfflat":
                    assert "SET ivfflat.probes" in call_args
                else:
                    assert "SET hnsw.ef_search" in call_args
                assert len(results) == 5
    
    def test_vector_operations_validation(self, pgvector_adapter):
        """Test input validation for vector operations."""
        with pytest.raises(ValueError):
            # Test invalid vector dimension
            pgvector_adapter.create_vector_index(
                VectorIndexConfig(
                    table_name="embeddings",
                    vector_column="embedding",
                    index_type="invalid_type"
                )
            )
        
        with pytest.raises(ValueError):
            # Test invalid similarity metric
            pgvector_adapter.similarity_search(
                table_name="embeddings",
                query_vector=np.random.rand(384),
                metric="invalid_metric"
            )
    
    def test_bulk_vector_operations(self, pgvector_adapter):
        """Test bulk vector operations with batching."""
        # Generate large test data
        num_vectors = 1000
        vectors = [np.random.rand(384).astype(np.float32) for _ in range(num_vectors)]
        metadata = [{"text": f"doc_{i}"} for i in range(num_vectors)]
        
        with patch.object(pgvector_adapter, '_execute_query') as mock_execute:
            # Test bulk insert with batching
            pgvector_adapter.bulk_insert_vectors(
                table_name="embeddings",
                vectors=vectors,
                metadata=metadata,
                batch_size=100
            )
            
            # Verify number of batch inserts
            assert mock_execute.call_count == (num_vectors + 99) // 100
            
            # Verify batch insert SQL
            first_batch_call = mock_execute.call_args_list[0][0][0]
            assert "INSERT INTO embeddings" in first_batch_call
            assert "UNNEST" in first_batch_call 