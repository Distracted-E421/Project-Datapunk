from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union
from ..parser.query_parser_core import QueryPlan, QueryNode
from ..optimizer.optimizer_core import QueryOptimizer, OptimizationRule
from datetime import datetime
import asyncio
import logging

@dataclass
class DataSourceInfo:
    """Information about a data source."""
    name: str
    type: str  # e.g., 'sql', 'nosql', 'file'
    capabilities: Set[str]  # supported operations
    cost_factors: Dict[str, float]  # operation costs
    statistics: Dict[str, Any]  # source statistics

@dataclass
class FederatedQueryPlan:
    """Represents a distributed query plan across multiple sources."""
    subplans: Dict[str, QueryPlan]  # source -> plan mapping
    dependencies: Dict[str, List[str]]  # source -> dependencies
    merge_plan: Optional[QueryPlan] = None  # plan to merge results

@dataclass
class DataSourceStats:
    """Statistics about a federated data source."""
    total_rows: int
    total_size_bytes: int
    avg_query_time_ms: float
    error_rate: float
    last_updated: datetime
    capabilities: List[str]

@dataclass
class FederationCost:
    """Cost estimate for a federated query plan."""
    cpu_cost: float
    io_cost: float
    network_cost: float
    memory_cost: float
    parallelism_benefit: float
    total_cost: float

class DataSourceAdapter(ABC):
    """Base adapter for connecting to different data sources."""
    
    @abstractmethod
    def get_capabilities(self) -> Set[str]:
        """Get the supported operations of this source."""
        pass
        
    @abstractmethod
    def estimate_cost(self, plan: QueryPlan) -> float:
        """Estimate the cost of executing a plan on this source."""
        pass
        
    @abstractmethod
    def translate_plan(self, plan: QueryPlan) -> Any:
        """Translate a query plan to source-specific format."""
        pass
        
    @abstractmethod
    def execute_plan(self, plan: QueryPlan) -> Any:
        """Execute a query plan on this source."""
        pass

class FederatedQueryOptimizer(QueryOptimizer):
    """Query optimizer for federated queries."""
    
    def __init__(self, rules: Optional[List[OptimizationRule]] = None):
        super().__init__(rules)
        self.source_stats: Dict[str, DataSourceStats] = {}
        self.network_latency: Dict[str, float] = {}
    
    def add_source_stats(self, source_id: str, stats: DataSourceStats) -> None:
        """Add or update statistics for a data source."""
        self.source_stats[source_id] = stats
    
    def update_network_latency(self, source_id: str, latency_ms: float) -> None:
        """Update network latency measurement for a source."""
        self.network_latency[source_id] = latency_ms
    
    def estimate_cost(self, plan: QueryPlan, source_id: str) -> FederationCost:
        """Estimate cost of executing a query plan on a data source."""
        stats = self.source_stats.get(source_id)
        if not stats:
            return FederationCost(
                cpu_cost=float('inf'),
                io_cost=float('inf'),
                network_cost=float('inf'),
                memory_cost=float('inf'),
                parallelism_benefit=0.0,
                total_cost=float('inf')
            )
        
        # Estimate CPU cost based on rows and operations
        cpu_cost = self._estimate_cpu_cost(plan, stats)
        
        # Estimate I/O cost based on data size and access patterns
        io_cost = self._estimate_io_cost(plan, stats)
        
        # Estimate network cost based on result size and latency
        network_cost = self._estimate_network_cost(plan, stats, source_id)
        
        # Estimate memory requirements
        memory_cost = self._estimate_memory_cost(plan, stats)
        
        # Calculate potential benefit from parallelism
        parallelism_benefit = self._estimate_parallelism_benefit(plan, stats)
        
        # Combine costs with weights
        total_cost = (
            0.3 * cpu_cost +
            0.3 * io_cost +
            0.2 * network_cost +
            0.1 * memory_cost -
            0.1 * parallelism_benefit
        )
        
        return FederationCost(
            cpu_cost=cpu_cost,
            io_cost=io_cost,
            network_cost=network_cost,
            memory_cost=memory_cost,
            parallelism_benefit=parallelism_benefit,
            total_cost=total_cost
        )
    
    def _estimate_cpu_cost(self, plan: QueryPlan, stats: DataSourceStats) -> float:
        """Estimate CPU cost based on operations and data size."""
        base_cost = stats.avg_query_time_ms * 0.5  # 50% of avg query time
        
        # Add costs for specific operations
        operation_costs = {
            'join': 100,
            'filter': 10,
            'aggregate': 50,
            'sort': 80,
            'window': 120
        }
        
        total_cost = base_cost
        for node in plan.nodes:
            op_type = node.operation_type.lower()
            if op_type in operation_costs:
                total_cost += operation_costs[op_type]
        
        return total_cost
    
    def _estimate_io_cost(self, plan: QueryPlan, stats: DataSourceStats) -> float:
        """Estimate I/O cost based on data access patterns."""
        # Base cost from data size
        base_cost = stats.total_size_bytes / (1024 * 1024)  # Convert to MB
        
        # Adjust for sequential vs random access
        access_pattern_multiplier = 1.0
        if self._has_random_access(plan):
            access_pattern_multiplier = 2.0
        
        return base_cost * access_pattern_multiplier
    
    def _estimate_network_cost(self, 
                             plan: QueryPlan, 
                             stats: DataSourceStats,
                             source_id: str) -> float:
        """Estimate network transfer cost."""
        # Base cost from result size estimate
        estimated_result_size = self._estimate_result_size(plan, stats)
        
        # Factor in network latency
        latency = self.network_latency.get(source_id, 100.0)  # Default 100ms
        
        return (estimated_result_size / (1024 * 1024)) * (latency / 100)
    
    def _estimate_memory_cost(self, plan: QueryPlan, stats: DataSourceStats) -> float:
        """Estimate memory requirements."""
        # Base memory for query execution
        base_memory = 100  # MB
        
        # Additional memory for operations
        operation_memory = {
            'join': 200,
            'sort': 150,
            'aggregate': 100,
            'window': 180
        }
        
        total_memory = base_memory
        for node in plan.nodes:
            op_type = node.operation_type.lower()
            if op_type in operation_memory:
                total_memory += operation_memory[op_type]
        
        return total_memory
    
    def _estimate_parallelism_benefit(self, 
                                    plan: QueryPlan, 
                                    stats: DataSourceStats) -> float:
        """Estimate benefit from parallel execution."""
        if 'parallel_execution' not in stats.capabilities:
            return 0.0
        
        # Calculate potential speedup from parallelism
        parallelizable_ops = ['join', 'aggregate', 'sort', 'scan']
        parallel_ops = sum(
            1 for node in plan.nodes
            if node.operation_type.lower() in parallelizable_ops
        )
        
        return min(parallel_ops * 50, 200)  # Cap benefit at 200
    
    def _has_random_access(self, plan: QueryPlan) -> bool:
        """Check if plan involves random access patterns."""
        random_access_ops = {'index_lookup', 'nested_loop_join'}
        return any(
            node.operation_type.lower() in random_access_ops
            for node in plan.nodes
        )
    
    def _estimate_result_size(self, plan: QueryPlan, stats: DataSourceStats) -> float:
        """Estimate size of query results in bytes."""
        # Start with table size
        size_estimate = stats.total_size_bytes
        
        # Adjust based on operations
        for node in plan.nodes:
            op_type = node.operation_type.lower()
            if op_type == 'filter':
                size_estimate *= 0.1  # Assume 10% selectivity
            elif op_type == 'join':
                size_estimate *= 1.5  # Assume 50% size increase
            elif op_type == 'aggregate':
                size_estimate *= 0.01  # Assume 1% of original size
        
        return max(size_estimate, 1024)  # Minimum 1KB

class QueryFederator:
    """Manages query federation across data sources."""
    
    def __init__(self):
        self.optimizer = FederatedQueryOptimizer()
        self.sources: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    async def add_source(self, 
                        source_id: str,
                        connection_info: Dict[str, Any],
                        capabilities: List[str]) -> None:
        """Add a new data source to the federation."""
        try:
            # Initialize source connection
            source = await self._initialize_source(source_id, connection_info)
            self.sources[source_id] = source
            
            # Collect initial statistics
            stats = await self._collect_source_stats(source)
            stats.capabilities = capabilities
            self.optimizer.add_source_stats(source_id, stats)
            
            # Measure initial network latency
            latency = await self._measure_network_latency(source)
            self.optimizer.update_network_latency(source_id, latency)
            
            self.logger.info(f"Added source {source_id} to federation")
        except Exception as e:
            self.logger.error(f"Error adding source {source_id}: {e}")
            raise
    
    async def remove_source(self, source_id: str) -> None:
        """Remove a data source from the federation."""
        if source_id in self.sources:
            try:
                await self._cleanup_source(self.sources[source_id])
                del self.sources[source_id]
                self.logger.info(f"Removed source {source_id} from federation")
            except Exception as e:
                self.logger.error(f"Error removing source {source_id}: {e}")
                raise
    
    async def execute_federated_query(self, 
                                    query: QueryPlan,
                                    timeout_ms: Optional[int] = None) -> Any:
        """Execute a query across federated sources."""
        try:
            # Find best execution plan
            execution_plan = await self._create_execution_plan(query)
            
            # Set up execution context
            context = await self._setup_execution_context(execution_plan, timeout_ms)
            
            # Execute the plan
            results = await self._execute_plan(execution_plan, context)
            
            # Merge results if needed
            if len(execution_plan) > 1:
                results = await self._merge_results(results, query)
            
            return results
        except Exception as e:
            self.logger.error(f"Error executing federated query: {e}")
            raise
    
    async def _initialize_source(self, 
                               source_id: str,
                               connection_info: Dict[str, Any]) -> Any:
        """Initialize connection to a data source."""
        # Implementation depends on source type
        pass
    
    async def _cleanup_source(self, source: Any) -> None:
        """Clean up source connection and resources."""
        # Implementation depends on source type
        pass
    
    async def _collect_source_stats(self, source: Any) -> DataSourceStats:
        """Collect statistics about a data source."""
        # Implementation depends on source type
        pass
    
    async def _measure_network_latency(self, source: Any) -> float:
        """Measure network latency to a data source."""
        # Implementation depends on source type
        pass
    
    async def _create_execution_plan(self, query: QueryPlan) -> List[Dict[str, Any]]:
        """Create optimal execution plan for federated query."""
        # Implementation depends on query type
        pass
    
    async def _setup_execution_context(self,
                                     plan: List[Dict[str, Any]],
                                     timeout_ms: Optional[int]) -> Dict[str, Any]:
        """Set up context for query execution."""
        # Implementation depends on execution requirements
        pass
    
    async def _execute_plan(self,
                          plan: List[Dict[str, Any]],
                          context: Dict[str, Any]) -> List[Any]:
        """Execute a federated query plan."""
        # Implementation depends on plan type
        pass
    
    async def _merge_results(self,
                           results: List[Any],
                           original_query: QueryPlan) -> Any:
        """Merge results from multiple sources."""
        # Implementation depends on result types
        pass

class FederationManager:
    """Manages query federation across multiple data sources."""
    
    def __init__(self):
        self.sources: Dict[str, DataSourceAdapter] = {}
        self.optimizer = QueryOptimizer()
        
    def register_source(self, name: str, adapter: DataSourceAdapter) -> None:
        """Register a new data source."""
        self.sources[name] = adapter
        
    def remove_source(self, name: str) -> None:
        """Remove a registered data source."""
        if name in self.sources:
            del self.sources[name]
            
    def get_source_info(self, name: str) -> DataSourceInfo:
        """Get information about a registered source."""
        if name not in self.sources:
            raise KeyError(f"Source {name} not registered")
            
        adapter = self.sources[name]
        return DataSourceInfo(
            name=name,
            type=adapter.__class__.__name__,
            capabilities=adapter.get_capabilities(),
            cost_factors={},  # To be populated
            statistics={}  # To be populated
        )
        
    def federate_query(self, query_plan: QueryPlan) -> FederatedQueryPlan:
        """Split a query plan into subplans for different sources."""
        # Analyze query requirements
        required_capabilities = self._analyze_requirements(query_plan)
        
        # Find capable sources
        capable_sources = self._find_capable_sources(required_capabilities)
        
        # Split query into subplans
        subplans = self._split_query(query_plan, capable_sources)
        
        # Optimize subplans
        optimized_subplans = self._optimize_subplans(subplans)
        
        # Create merge plan
        merge_plan = self._create_merge_plan(optimized_subplans)
        
        # Build dependencies
        dependencies = self._build_dependencies(optimized_subplans)
        
        return FederatedQueryPlan(
            subplans=optimized_subplans,
            dependencies=dependencies,
            merge_plan=merge_plan
        )
        
    def execute_federated_query(self, fed_plan: FederatedQueryPlan) -> Any:
        """Execute a federated query plan."""
        # Execute subplans in dependency order
        results = {}
        executed = set()
        
        while len(executed) < len(fed_plan.subplans):
            for source, plan in fed_plan.subplans.items():
                if source in executed:
                    continue
                    
                # Check if dependencies are satisfied
                deps = fed_plan.dependencies.get(source, [])
                if not all(dep in executed for dep in deps):
                    continue
                    
                # Execute subplan
                adapter = self.sources[source]
                results[source] = adapter.execute_plan(plan)
                executed.add(source)
                
        # Execute merge plan if present
        if fed_plan.merge_plan:
            return self._execute_merge(fed_plan.merge_plan, results)
            
        return results
        
    def _analyze_requirements(self, plan: QueryPlan) -> Set[str]:
        """Analyze the capabilities required by a query plan."""
        required = set()
        
        def analyze_node(node: QueryNode):
            required.add(node.operation)
            for child in node.children:
                analyze_node(child)
                
        analyze_node(plan.root)
        return required
        
    def _find_capable_sources(self, requirements: Set[str]) -> Dict[str, Set[str]]:
        """Find sources capable of handling given requirements."""
        capable_sources = {}
        
        for name, adapter in self.sources.items():
            capabilities = adapter.get_capabilities()
            supported = requirements & capabilities
            if supported:
                capable_sources[name] = supported
                
        return capable_sources
        
    def _split_query(
        self, 
        plan: QueryPlan, 
        capable_sources: Dict[str, Set[str]]
    ) -> Dict[str, QueryPlan]:
        """Split a query plan among capable sources."""
        # Simple initial implementation - assign whole plan to most capable source
        best_source = max(
            capable_sources.items(),
            key=lambda x: len(x[1])
        )[0]
        
        return {best_source: plan}
        
    def _optimize_subplans(
        self, 
        subplans: Dict[str, QueryPlan]
    ) -> Dict[str, QueryPlan]:
        """Optimize subplans for each source."""
        optimized = {}
        
        for source, plan in subplans.items():
            optimized[source] = self.optimizer.optimize(plan)
            
        return optimized
        
    def _create_merge_plan(
        self, 
        subplans: Dict[str, QueryPlan]
    ) -> Optional[QueryPlan]:
        """Create a plan to merge results from subplans."""
        if len(subplans) <= 1:
            return None
            
        # Create a simple union plan
        merge_node = QueryNode(
            operation='union',
            children=[]  # Placeholder for result references
        )
        
        return QueryPlan(merge_node)
        
    def _build_dependencies(
        self, 
        subplans: Dict[str, QueryPlan]
    ) -> Dict[str, List[str]]:
        """Build execution dependencies between subplans."""
        # Simple implementation - no dependencies
        return {source: [] for source in subplans}
        
    def _execute_merge(self, merge_plan: QueryPlan, results: Dict[str, Any]) -> Any:
        """Execute the merge plan on subplan results."""
        # Simple implementation - union all results
        merged = []
        for result in results.values():
            if isinstance(result, list):
                merged.extend(result)
            else:
                merged.append(result)
        return merged 