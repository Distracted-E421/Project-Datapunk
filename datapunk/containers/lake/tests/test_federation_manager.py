import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict, Any

from ..src.query.federation.manager import FederationManager, FederationMetrics
from ..src.query.optimizer.executor_bridge import OptimizerExecutorBridge, OptimizedPlan, ExecutionStrategy

@pytest.fixture
def mock_optimizer_executor():
    executor = Mock(spec=OptimizerExecutorBridge)
    executor.create_execution_plan.return_value = OptimizedPlan(
        strategy=ExecutionStrategy.PARALLEL,
        cost_estimate=100.0,
        parallelism_degree=4,
        cache_policy=None,
        streaming_config=None,
        monitoring_hooks=["performance"]
    )
    executor.execute_plan.return_value = {"data": "test_result"}
    return executor

@pytest.fixture
def mock_adapter():
    adapter = Mock()
    adapter.get_capabilities.return_value = {
        "supports_aggregation": True,
        "supports_joins": True,
        "max_concurrent_queries": 10
    }
    adapter.get_metadata.return_value = {
        "name": "Test Source",
        "type": "SQL",
        "version": "1.0"
    }
    adapter.transform_query.return_value = {"transformed": "query"}
    adapter.transform_result.return_value = {"transformed": "result"}
    adapter.get_status.return_value = {"status": "healthy"}
    return adapter

@pytest.fixture
def federation_manager(mock_optimizer_executor):
    return FederationManager(
        optimizer_executor=mock_optimizer_executor,
        alert_threshold=0.8
    )

class TestFederationManager:
    def test_register_data_source(self, federation_manager, mock_adapter):
        federation_manager.register_data_source("test_source", mock_adapter)
        
        assert "test_source" in federation_manager.adapters
        mock_adapter.get_capabilities.assert_called_once()
        mock_adapter.get_metadata.assert_called_once()

    def test_execute_federated_query_success(self, federation_manager, mock_adapter, mock_optimizer_executor):
        # Register a test source
        federation_manager.register_data_source("test_source", mock_adapter)
        
        # Execute query
        query = {"select": "*", "from": "test_table"}
        result = federation_manager.execute_federated_query(
            query=query,
            visualization_required=True,
            alert_on_threshold=True
        )
        
        # Verify result structure
        assert "result" in result
        assert "metrics" in result
        assert "visualization" in result
        assert result["errors"] is None
        
        # Verify metrics
        metrics = result["metrics"]
        assert "duration" in metrics
        assert "data_volume" in metrics
        assert "source_count" in metrics
        assert "error_count" in metrics
        
        # Verify interactions
        mock_adapter.transform_query.assert_called_once()
        mock_adapter.transform_result.assert_called_once()
        mock_optimizer_executor.create_execution_plan.assert_called_once()
        mock_optimizer_executor.execute_plan.assert_called_once()

    def test_execute_federated_query_with_errors(self, federation_manager, mock_adapter, mock_optimizer_executor):
        # Register test sources
        federation_manager.register_data_source("source1", mock_adapter)
        
        # Make one source fail
        mock_optimizer_executor.execute_plan.side_effect = Exception("Test error")
        
        # Execute query
        query = {"select": "*", "from": "test_table"}
        result = federation_manager.execute_federated_query(
            query=query,
            visualization_required=True,
            alert_on_threshold=True
        )
        
        # Verify error handling
        assert result["errors"] is not None
        assert len(result["errors"]) == 1
        assert result["errors"][0]["source_id"] == "source1"
        assert "Test error" in result["errors"][0]["error"]

    def test_federation_metrics_calculation(self, federation_manager, mock_adapter):
        federation_manager.register_data_source("source1", mock_adapter)
        federation_manager.register_data_source("source2", mock_adapter)
        
        query = {"select": "*", "from": "test_table"}
        result = federation_manager.execute_federated_query(query)
        
        metrics = result["metrics"]
        assert metrics["source_count"] == 2
        assert metrics["error_count"] == 0
        assert isinstance(metrics["duration"], float)
        assert isinstance(metrics["data_volume"], int)

    def test_alert_generation(self, federation_manager, mock_adapter):
        federation_manager.register_data_source("source1", mock_adapter)
        
        # Simulate a long-running query
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.side_effect = [
                datetime(2023, 1, 1, 12, 0, 0),  # Start time
                datetime(2023, 1, 1, 12, 0, 35)  # End time (35 seconds later)
            ]
            
            result = federation_manager.execute_federated_query(
                query={"select": "*", "from": "test_table"},
                alert_on_threshold=True
            )
        
        # Verify that alerts were generated
        assert result["metrics"]["duration"] > 30  # Should trigger duration alert

    def test_visualization_generation(self, federation_manager, mock_adapter):
        federation_manager.register_data_source("source1", mock_adapter)
        
        result = federation_manager.execute_federated_query(
            query={"select": "*", "from": "test_table"},
            visualization_required=True
        )
        
        assert result["visualization"] is not None

    def test_get_federation_status(self, federation_manager, mock_adapter):
        federation_manager.register_data_source("source1", mock_adapter)
        federation_manager.register_data_source("source2", mock_adapter)
        
        status = federation_manager.get_federation_status()
        
        assert "sources" in status
        assert len(status["sources"]) == 2
        assert "metrics" in status
        assert "alerts" in status
        assert "visualization" in status

    def test_get_source_statistics(self, federation_manager, mock_adapter):
        source_id = "test_source"
        federation_manager.register_data_source(source_id, mock_adapter)
        
        stats = federation_manager.get_source_statistics(source_id)
        
        assert "metadata" in stats
        assert "capabilities" in stats
        assert "metrics" in stats
        assert "alerts" in stats
        assert "visualization" in stats
        
        with pytest.raises(ValueError):
            federation_manager.get_source_statistics("nonexistent_source")

    def test_error_rate_alerting(self, federation_manager, mock_adapter, mock_optimizer_executor):
        # Register multiple sources
        for i in range(5):
            federation_manager.register_data_source(f"source{i}", mock_adapter)
        
        # Make most executions fail to trigger error rate alert
        mock_optimizer_executor.execute_plan.side_effect = Exception("Test error")
        
        result = federation_manager.execute_federated_query(
            query={"select": "*", "from": "test_table"},
            alert_on_threshold=True
        )
        
        assert result["metrics"]["error_count"] == 5
        assert result["metrics"]["source_count"] == 5
        assert len(result["errors"]) == 5

    def test_data_volume_alerting(self, federation_manager, mock_adapter):
        federation_manager.register_data_source("source1", mock_adapter)
        
        # Create a large result to trigger data volume alert
        large_result = "x" * (150 * 1024 * 1024)  # 150MB
        mock_adapter.transform_result.return_value = large_result
        
        result = federation_manager.execute_federated_query(
            query={"select": "*", "from": "test_table"},
            alert_on_threshold=True
        )
        
        assert result["metrics"]["data_volume"] > 100 * 1024 * 1024  # > 100MB 