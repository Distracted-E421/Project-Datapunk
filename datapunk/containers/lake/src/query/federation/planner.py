from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from ..parser.core import QueryNode, QueryType
from ..optimizer.index_aware import IndexAwareOptimizer

class DataSourceType(Enum):
    """Types of data sources supported by federation."""
    RELATIONAL = "relational"
    DOCUMENT = "document"
    GRAPH = "graph"
    OBJECT_STORE = "object_store"
    TIME_SERIES = "time_series"

@dataclass
class DataSource:
    """Represents a federated data source."""
    name: str
    type: DataSourceType
    capabilities: Set[str]  # Supported operations
    cost_factors: Dict[str, float]  # Operation costs
    statistics: Dict[str, Any]  # Source statistics

@dataclass
class SubQuery:
    """Represents a portion of query to be executed on a data source."""
    source: DataSource
    query: QueryNode
    estimated_cost: float
    dependencies: List['SubQuery']
    result_size: int

class DistributedQueryPlanner:
    """Plans and optimizes federated query execution."""
    
    def __init__(self):
        self.data_sources: Dict[str, DataSource] = {}
        self.optimizers: Dict[str, IndexAwareOptimizer] = {}
        
    def register_data_source(self, source: DataSource,
                           optimizer: Optional[IndexAwareOptimizer] = None) -> None:
        """Register a data source and its optimizer."""
        self.data_sources[source.name] = source
        if optimizer:
            self.optimizers[source.name] = optimizer
            
    def plan_query(self, query: QueryNode) -> List[SubQuery]:
        """Create an optimized distributed query plan."""
        # Analyze query requirements
        required_capabilities = self._analyze_requirements(query)
        
        # Find capable data sources
        candidate_sources = self._find_capable_sources(required_capabilities)
        
        # Split query into sub-queries
        sub_queries = self._split_query(query, candidate_sources)
        
        # Optimize sub-queries
        optimized_queries = self._optimize_sub_queries(sub_queries)
        
        # Create execution plan
        return self._create_execution_plan(optimized_queries)
        
    def _analyze_requirements(self, query: QueryNode) -> Set[str]:
        """Analyze query to determine required capabilities."""
        requirements = set()
        
        if query.query_type == QueryType.SELECT:
            requirements.add("select")
            if query.joins:
                requirements.add("join")
            if query.group_by:
                requirements.add("group")
            if query.order_by:
                requirements.add("order")
            if query.having:
                requirements.add("having")
                
        # Add specific operation requirements
        for condition in query.conditions:
            op_type = condition.get("op", "").lower()
            if op_type in ("like", "regex"):
                requirements.add("text_search")
            elif op_type in ("geo_within", "geo_intersects"):
                requirements.add("geospatial")
                
        return requirements
        
    def _find_capable_sources(self, requirements: Set[str]) -> List[DataSource]:
        """Find data sources capable of handling requirements."""
        capable_sources = []
        
        for source in self.data_sources.values():
            if requirements.issubset(source.capabilities):
                capable_sources.append(source)
                
        return capable_sources
        
    def _split_query(self, query: QueryNode, 
                    sources: List[DataSource]) -> List[SubQuery]:
        """Split query into sub-queries for different data sources."""
        sub_queries = []
        
        # Handle different query types
        if query.query_type == QueryType.SELECT:
            # Split based on table locations
            table_groups = self._group_tables_by_source(query.tables)
            
            for source, tables in table_groups.items():
                sub_query = self._create_sub_query(query, tables, source)
                if sub_query:
                    sub_queries.append(sub_query)
                    
        return sub_queries
        
    def _optimize_sub_queries(self, sub_queries: List[SubQuery]) -> List[SubQuery]:
        """Optimize individual sub-queries."""
        optimized = []
        
        for sub_query in sub_queries:
            # Use source-specific optimizer if available
            optimizer = self.optimizers.get(sub_query.source.name)
            if optimizer:
                optimized_query = optimizer.optimize_query(sub_query.query)
                sub_query.query = optimized_query
                
            # Update cost estimation
            sub_query.estimated_cost = self._estimate_cost(sub_query)
            optimized.append(sub_query)
            
        return optimized
        
    def _create_execution_plan(self, sub_queries: List[SubQuery]) -> List[SubQuery]:
        """Create optimal execution plan for sub-queries."""
        # Sort by dependencies and cost
        sorted_queries = self._topological_sort(sub_queries)
        
        # Look for optimization opportunities
        optimized_plan = self._optimize_plan(sorted_queries)
        
        return optimized_plan
        
    def _group_tables_by_source(self, tables: List[str]) -> Dict[DataSource, List[str]]:
        """Group tables by their data sources."""
        groups: Dict[DataSource, List[str]] = {}
        
        for table in tables:
            source = self._find_table_source(table)
            if source:
                if source not in groups:
                    groups[source] = []
                groups[source].append(table)
                
        return groups
        
    def _find_table_source(self, table: str) -> Optional[DataSource]:
        """Find the data source containing a table."""
        # This is a placeholder - actual implementation would use
        # metadata catalog to locate tables
        return next(iter(self.data_sources.values()), None)
        
    def _create_sub_query(self, query: QueryNode, tables: List[str],
                         source: DataSource) -> Optional[SubQuery]:
        """Create a sub-query for specific tables on a source."""
        # Extract relevant parts of the query for these tables
        filtered_query = self._filter_query_for_tables(query, tables)
        if not filtered_query:
            return None
            
        return SubQuery(
            source=source,
            query=filtered_query,
            estimated_cost=0.0,  # Will be updated during optimization
            dependencies=[],     # Will be updated during plan creation
            result_size=0       # Will be updated during optimization
        )
        
    def _filter_query_for_tables(self, query: QueryNode,
                               tables: List[str]) -> Optional[QueryNode]:
        """Filter query to only include specified tables."""
        # This is a placeholder - actual implementation would create
        # a new query node with only the relevant parts
        return query
        
    def _estimate_cost(self, sub_query: SubQuery) -> float:
        """Estimate cost of executing a sub-query."""
        source = sub_query.source
        cost = 0.0
        
        # Factor in operation costs
        for capability in source.capabilities:
            if capability in source.cost_factors:
                cost += source.cost_factors[capability]
                
        # Factor in data size
        data_size = source.statistics.get("data_size", 0)
        cost *= (1 + (data_size / 1_000_000))  # Adjust cost based on data size
        
        return cost
        
    def _topological_sort(self, sub_queries: List[SubQuery]) -> List[SubQuery]:
        """Sort sub-queries based on dependencies."""
        # Implementation would use topological sorting algorithm
        return sorted(sub_queries, key=lambda q: len(q.dependencies))
        
    def _optimize_plan(self, sorted_queries: List[SubQuery]) -> List[SubQuery]:
        """Look for plan optimization opportunities."""
        # This would implement various optimization strategies:
        # - Parallel execution opportunities
        # - Push down optimizations
        # - Common sub-expression elimination
        # - Data locality optimizations
        return sorted_queries 