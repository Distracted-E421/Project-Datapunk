import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from ..src.query.optimizer.executor_bridge import (
    OptimizerExecutorBridge,
    ExecutionStrategy,
    OptimizedPlan
)

@pytest.fixture
def mock_optimizer():
    optimizer = Mock()
    # Set up common optimizer method returns
    optimizer.optimize.return_value = {"type": "select", "table": "test"}
    optimizer.estimate_cost.return_value = 100.0
    optimizer.estimate_data_size.return_value = 1000000
    optimizer.estimate_complexity.return_value = 0.5
    optimizer.estimate_memory_requirements.return_value = 1024 * 1024  # 1MB
    optimizer.is_cacheable.return_value = True
    optimizer.is_streamable.return_value = True
    return optimizer

@pytest.fixture
def mock_executor():
    executor = Mock()
    executor.execute.return_value = {"result": "test_data"}
    return executor

@pytest.fixture
def bridge(mock_optimizer, mock_executor):
    return OptimizerExecutorBridge(
        optimizer=mock_optimizer,
        executor=mock_executor,
        enable_adaptive=True,
        enable_caching=True
    )

class TestOptimizerExecutorBridge:
    def test_create_execution_plan_basic(self, bridge):
        query = {"select": "*", "from": "test_table"}
        plan = bridge.create_execution_plan(query)
        
        assert isinstance(plan, OptimizedPlan)
        assert isinstance(plan.strategy, ExecutionStrategy)
        assert isinstance(plan.cost_estimate, float)
        assert isinstance(plan.parallelism_degree, int)
        assert isinstance(plan.monitoring_hooks, list)

    def test_execution_strategy_selection(self, bridge, mock_optimizer):
        # Test CACHED strategy
        mock_optimizer.is_cacheable.return_value = True
        plan = bridge.create_execution_plan({"query": "test"})
        assert plan.strategy == ExecutionStrategy.CACHED

        # Test STREAMING strategy
        mock_optimizer.is_cacheable.return_value = False
        mock_optimizer.is_streamable.return_value = True
        mock_optimizer.estimate_data_size.return_value = 2 * 10**9  # 2GB
        plan = bridge.create_execution_plan({"query": "test"})
        assert plan.strategy == ExecutionStrategy.STREAMING

        # Test PARALLEL strategy
        mock_optimizer.estimate_complexity.return_value = 0.8
        mock_optimizer.estimate_data_size.return_value = 100000
        plan = bridge.create_execution_plan({"query": "test"})
        assert plan.strategy == ExecutionStrategy.PARALLEL

    def test_parallelism_computation(self, bridge, mock_optimizer):
        # Test high complexity
        mock_optimizer.estimate_complexity.return_value = 0.9
        plan = bridge.create_execution_plan({"query": "test"})
        assert plan.parallelism_degree == 8

        # Test medium complexity
        mock_optimizer.estimate_complexity.return_value = 0.6
        plan = bridge.create_execution_plan({"query": "test"})
        assert plan.parallelism_degree == 4

        # Test low complexity
        mock_optimizer.estimate_complexity.return_value = 0.3
        plan = bridge.create_execution_plan({"query": "test"})
        assert plan.parallelism_degree == 2

    def test_cache_policy_configuration(self, bridge, mock_optimizer):
        # Test complex query cache policy
        mock_optimizer.estimate_complexity.return_value = 0.9
        mock_optimizer.is_cacheable.return_value = True
        plan = bridge.create_execution_plan({"query": "test"})
        
        assert plan.cache_policy is not None
        assert plan.cache_policy["ttl"] == 3600  # 1 hour
        assert plan.cache_policy["max_size"] > 0

        # Test simple query cache policy
        mock_optimizer.estimate_complexity.return_value = 0.3
        plan = bridge.create_execution_plan({"query": "test"})
        
        assert plan.cache_policy is not None
        assert plan.cache_policy["ttl"] == 1800  # 30 minutes

    def test_streaming_configuration(self, bridge, mock_optimizer):
        mock_optimizer.is_cacheable.return_value = False
        mock_optimizer.is_streamable.return_value = True
        mock_optimizer.estimate_data_size.return_value = 2 * 10**9  # 2GB
        
        plan = bridge.create_execution_plan({"query": "test"})
        
        assert plan.streaming_config is not None
        assert "batch_size" in plan.streaming_config
        assert "buffer_size" in plan.streaming_config
        assert "timeout" in plan.streaming_config
        assert plan.streaming_config["timeout"] == 30

    def test_monitoring_hooks_setup(self, bridge):
        # Test parallel execution monitoring
        plan = bridge.create_execution_plan({"query": "test"})
        assert "performance" in plan.monitoring_hooks
        assert "resource_usage" in plan.monitoring_hooks
        
        if plan.strategy == ExecutionStrategy.PARALLEL:
            assert "parallelism_efficiency" in plan.monitoring_hooks
            assert "thread_usage" in plan.monitoring_hooks
        elif plan.strategy == ExecutionStrategy.STREAMING:
            assert "throughput" in plan.monitoring_hooks
            assert "backpressure" in plan.monitoring_hooks
        elif plan.strategy == ExecutionStrategy.ADAPTIVE:
            assert "adaptation_events" in plan.monitoring_hooks
            assert "optimization_decisions" in plan.monitoring_hooks

    @pytest.mark.parametrize("strategy", [
        ExecutionStrategy.PARALLEL,
        ExecutionStrategy.STREAMING,
        ExecutionStrategy.ADAPTIVE,
        ExecutionStrategy.CACHED
    ])
    def test_execute_plan_with_different_strategies(self, bridge, strategy):
        plan = OptimizedPlan(
            strategy=strategy,
            cost_estimate=100.0,
            parallelism_degree=4,
            cache_policy={"ttl": 3600, "max_size": 1024*1024} if strategy == ExecutionStrategy.CACHED else None,
            streaming_config={"batch_size": 1000, "buffer_size": 5000, "timeout": 30} if strategy == ExecutionStrategy.STREAMING else None,
            monitoring_hooks=["performance", "resource_usage"]
        )
        
        result = bridge.execute_plan({"query": "test"}, plan)
        assert result == {"result": "test_data"}

    def test_error_handling(self, bridge, mock_executor):
        mock_executor.execute.side_effect = Exception("Test error")
        
        plan = OptimizedPlan(
            strategy=ExecutionStrategy.PARALLEL,
            cost_estimate=100.0,
            parallelism_degree=4,
            cache_policy=None,
            streaming_config=None,
            monitoring_hooks=["performance"]
        )
        
        with pytest.raises(Exception) as exc_info:
            bridge.execute_plan({"query": "test"}, plan)
        assert str(exc_info.value) == "Test error"

    def test_cost_estimation(self, bridge, mock_optimizer):
        # Test cost estimates for different strategies
        query = {"query": "test"}
        base_cost = 100.0
        mock_optimizer.estimate_cost.return_value = base_cost
        
        # PARALLEL strategy
        plan = bridge.create_execution_plan(query)
        if plan.strategy == ExecutionStrategy.PARALLEL:
            assert plan.cost_estimate == base_cost * 0.8
        elif plan.strategy == ExecutionStrategy.STREAMING:
            assert plan.cost_estimate == base_cost * 0.9
        elif plan.strategy == ExecutionStrategy.ADAPTIVE:
            assert plan.cost_estimate == base_cost * 0.85
        elif plan.strategy == ExecutionStrategy.CACHED:
            assert plan.cost_estimate == base_cost * 0.1 