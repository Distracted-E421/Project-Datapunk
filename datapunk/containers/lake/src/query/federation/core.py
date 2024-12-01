from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union
from ..parser.core import QueryPlan, QueryNode
from ..optimizer.core import QueryOptimizer

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