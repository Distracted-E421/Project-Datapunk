from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

from .core import QueryOptimizer
from .rules import OptimizationRules
from .index_aware import IndexAwareOptimizer
from ..executor import (
    core as executor_core,
    parallel,
    adaptive,
    caching,
    streaming,
    monitoring
)

class ExecutionStrategy(Enum):
    PARALLEL = "parallel"
    STREAMING = "streaming"
    ADAPTIVE = "adaptive"
    CACHED = "cached"

@dataclass
class OptimizedPlan:
    strategy: ExecutionStrategy
    cost_estimate: float
    parallelism_degree: int
    cache_policy: Optional[Dict[str, Any]]
    streaming_config: Optional[Dict[str, Any]]
    monitoring_hooks: List[str]

class OptimizerExecutorBridge:
    def __init__(
        self,
        optimizer: QueryOptimizer,
        executor: executor_core.QueryExecutor,
        enable_adaptive: bool = True,
        enable_caching: bool = True
    ):
        self.optimizer = optimizer
        self.executor = executor
        self.enable_adaptive = enable_adaptive
        self.enable_caching = enable_caching
        
        # Initialize specialized executors
        self.parallel_executor = parallel.ParallelExecutor()
        self.adaptive_executor = adaptive.AdaptiveExecutor()
        self.cache_manager = caching.CacheManager()
        self.stream_executor = streaming.StreamingExecutor()
        self.monitor = monitoring.ExecutionMonitor()

    def create_execution_plan(self, query: Any) -> OptimizedPlan:
        """Creates an optimized execution plan based on query characteristics"""
        # Get initial optimization from query optimizer
        optimized_query = self.optimizer.optimize(query)
        
        # Analyze query characteristics
        characteristics = self._analyze_query_characteristics(optimized_query)
        
        # Choose execution strategy
        strategy = self._select_execution_strategy(characteristics)
        
        # Build execution plan
        plan = OptimizedPlan(
            strategy=strategy,
            cost_estimate=self._estimate_cost(optimized_query, strategy),
            parallelism_degree=self._compute_parallelism(characteristics),
            cache_policy=self._determine_cache_policy(characteristics) if self.enable_caching else None,
            streaming_config=self._configure_streaming(characteristics) if strategy == ExecutionStrategy.STREAMING else None,
            monitoring_hooks=self._setup_monitoring_hooks(strategy)
        )
        
        return plan

    def execute_plan(self, query: Any, plan: OptimizedPlan):
        """Executes the optimized plan using appropriate executor"""
        # Set up monitoring
        self.monitor.attach_hooks(plan.monitoring_hooks)
        
        # Configure execution based on strategy
        if plan.strategy == ExecutionStrategy.PARALLEL:
            executor = self.parallel_executor
            executor.set_parallelism(plan.parallelism_degree)
        elif plan.strategy == ExecutionStrategy.STREAMING:
            executor = self.stream_executor
            executor.configure(plan.streaming_config)
        elif plan.strategy == ExecutionStrategy.ADAPTIVE:
            executor = self.adaptive_executor
        else:  # CACHED
            if self.cache_manager.has_cached_result(query):
                return self.cache_manager.get_cached_result(query)
            executor = self.executor

        # Execute with monitoring
        with self.monitor.track_execution():
            result = executor.execute(query)
            
        # Cache result if appropriate
        if plan.cache_policy and self.enable_caching:
            self.cache_manager.cache_result(query, result, plan.cache_policy)
            
        return result

    def _analyze_query_characteristics(self, query: Any) -> Dict[str, Any]:
        """Analyzes query characteristics to determine optimal execution strategy"""
        return {
            "estimated_data_size": self._estimate_data_size(query),
            "complexity": self._estimate_complexity(query),
            "memory_requirements": self._estimate_memory_requirements(query),
            "cacheable": self._is_cacheable(query),
            "streamable": self._is_streamable(query)
        }

    def _select_execution_strategy(self, characteristics: Dict[str, Any]) -> ExecutionStrategy:
        """Selects the best execution strategy based on query characteristics"""
        if characteristics["cacheable"] and self.enable_caching:
            return ExecutionStrategy.CACHED
        elif characteristics["streamable"] and characteristics["estimated_data_size"] > 1e9:  # 1GB
            return ExecutionStrategy.STREAMING
        elif characteristics["complexity"] > 0.7:  # High complexity
            return ExecutionStrategy.PARALLEL
        elif self.enable_adaptive:
            return ExecutionStrategy.ADAPTIVE
        return ExecutionStrategy.PARALLEL

    # Helper methods for various computations
    def _estimate_cost(self, query: Any, strategy: ExecutionStrategy) -> float:
        """Estimates the cost of executing the query with given strategy"""
        base_cost = self.optimizer.estimate_cost(query)
        strategy_multiplier = {
            ExecutionStrategy.PARALLEL: 0.8,  # 20% reduction due to parallelism
            ExecutionStrategy.STREAMING: 0.9,  # 10% reduction due to streaming
            ExecutionStrategy.ADAPTIVE: 0.85,  # 15% reduction due to adaptation
            ExecutionStrategy.CACHED: 0.1,  # 90% reduction due to caching
        }
        return base_cost * strategy_multiplier[strategy]

    def _compute_parallelism(self, characteristics: Dict[str, Any]) -> int:
        """Computes optimal parallelism degree based on query characteristics"""
        if characteristics["complexity"] > 0.8:
            return 8
        elif characteristics["complexity"] > 0.5:
            return 4
        return 2

    def _determine_cache_policy(self, characteristics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determines caching policy based on query characteristics"""
        if not characteristics["cacheable"]:
            return None
        return {
            "ttl": self._compute_cache_ttl(characteristics),
            "max_size": self._compute_cache_size(characteristics)
        }

    def _configure_streaming(self, characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Configures streaming parameters based on query characteristics"""
        return {
            "batch_size": self._compute_batch_size(characteristics),
            "buffer_size": self._compute_buffer_size(characteristics),
            "timeout": 30  # seconds
        }

    def _setup_monitoring_hooks(self, strategy: ExecutionStrategy) -> List[str]:
        """Sets up monitoring hooks based on execution strategy"""
        hooks = ["performance", "resource_usage"]
        if strategy == ExecutionStrategy.PARALLEL:
            hooks.extend(["parallelism_efficiency", "thread_usage"])
        elif strategy == ExecutionStrategy.STREAMING:
            hooks.extend(["throughput", "backpressure"])
        elif strategy == ExecutionStrategy.ADAPTIVE:
            hooks.extend(["adaptation_events", "optimization_decisions"])
        return hooks

    # Additional helper methods for internal calculations
    def _estimate_data_size(self, query: Any) -> int:
        return self.optimizer.estimate_data_size(query)

    def _estimate_complexity(self, query: Any) -> float:
        return self.optimizer.estimate_complexity(query)

    def _estimate_memory_requirements(self, query: Any) -> int:
        return self.optimizer.estimate_memory_requirements(query)

    def _is_cacheable(self, query: Any) -> bool:
        return self.optimizer.is_cacheable(query)

    def _is_streamable(self, query: Any) -> bool:
        return self.optimizer.is_streamable(query)

    def _compute_cache_ttl(self, characteristics: Dict[str, Any]) -> int:
        """Computes cache TTL in seconds based on characteristics"""
        if characteristics["complexity"] > 0.8:
            return 3600  # 1 hour for complex queries
        return 1800  # 30 minutes for simpler queries

    def _compute_cache_size(self, characteristics: Dict[str, Any]) -> int:
        """Computes maximum cache size in bytes"""
        return min(characteristics["memory_requirements"] * 2, 1024 * 1024 * 1024)  # Max 1GB

    def _compute_batch_size(self, characteristics: Dict[str, Any]) -> int:
        """Computes optimal batch size for streaming"""
        return min(1000, max(100, characteristics["estimated_data_size"] // 1000000))

    def _compute_buffer_size(self, characteristics: Dict[str, Any]) -> int:
        """Computes optimal buffer size for streaming"""
        return min(10000, max(1000, characteristics["estimated_data_size"] // 100000)) 