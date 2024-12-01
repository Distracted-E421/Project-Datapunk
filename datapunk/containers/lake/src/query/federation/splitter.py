from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from ..parser.core import QueryPlan, QueryNode
from .core import DataSourceStats

@dataclass
class SubQuery:
    """Represents a part of a split query."""
    source_id: str
    query_plan: QueryPlan
    dependencies: Set[str]  # IDs of other subqueries this depends on
    estimated_cost: float
    estimated_rows: int
    push_down_operations: List[str]

class QuerySplitter:
    """Splits complex queries into subqueries for federated execution."""
    
    def __init__(self):
        self.source_capabilities: Dict[str, Set[str]] = {}
        self.source_stats: Dict[str, DataSourceStats] = {}
    
    def update_source_info(self,
                          source_id: str,
                          capabilities: Set[str],
                          stats: DataSourceStats) -> None:
        """Update information about a data source."""
        self.source_capabilities[source_id] = capabilities
        self.source_stats[source_id] = stats
    
    def split_query(self, query: QueryPlan) -> List[SubQuery]:
        """Split a query plan into subqueries for different sources."""
        # Analyze query dependencies
        dependencies = self._analyze_dependencies(query)
        
        # Identify push-down operations
        pushdown_ops = self._identify_pushdown_operations(query)
        
        # Split based on table locations and operations
        subqueries = self._create_subqueries(query, dependencies, pushdown_ops)
        
        # Optimize splits
        optimized = self._optimize_splits(subqueries)
        
        return optimized
    
    def _analyze_dependencies(self, 
                            query: QueryPlan) -> Dict[str, Set[str]]:
        """Analyze data dependencies between query parts."""
        dependencies: Dict[str, Set[str]] = {}
        
        def traverse_node(node: QueryNode, 
                         seen_tables: Set[str]) -> Set[str]:
            """Traverse query node to find dependencies."""
            if node.table_name:
                seen_tables.add(node.table_name)
            
            # Record dependencies for joins
            if node.operation_type.lower() == 'join':
                left_deps = traverse_node(node.left, seen_tables.copy())
                right_deps = traverse_node(node.right, seen_tables.copy())
                dependencies[node.id] = left_deps | right_deps
            
            # Record dependencies for subqueries
            elif node.subquery:
                subq_deps = traverse_node(node.subquery, seen_tables.copy())
                dependencies[node.id] = subq_deps
            
            # Process child nodes
            for child in node.children:
                child_deps = traverse_node(child, seen_tables.copy())
                if node.id in dependencies:
                    dependencies[node.id] |= child_deps
                else:
                    dependencies[node.id] = child_deps
            
            return seen_tables
        
        traverse_node(query.root, set())
        return dependencies
    
    def _identify_pushdown_operations(self, 
                                    query: QueryPlan) -> Dict[str, List[str]]:
        """Identify operations that can be pushed down to sources."""
        pushdown_ops: Dict[str, List[str]] = {}
        
        def analyze_node(node: QueryNode) -> None:
            """Analyze node for pushdown potential."""
            if node.table_name:
                source_id = self._get_source_for_table(node.table_name)
                if source_id:
                    capabilities = self.source_capabilities.get(source_id, set())
                    
                    # Check if operation can be pushed down
                    if node.operation_type.lower() in capabilities:
                        if source_id in pushdown_ops:
                            pushdown_ops[source_id].append(node.operation_type)
                        else:
                            pushdown_ops[source_id] = [node.operation_type]
            
            # Process child nodes
            if node.left:
                analyze_node(node.left)
            if node.right:
                analyze_node(node.right)
            for child in node.children:
                analyze_node(child)
        
        analyze_node(query.root)
        return pushdown_ops
    
    def _create_subqueries(self,
                          query: QueryPlan,
                          dependencies: Dict[str, Set[str]],
                          pushdown_ops: Dict[str, List[str]]) -> List[SubQuery]:
        """Create subqueries based on analysis."""
        subqueries: List[SubQuery] = []
        
        def split_node(node: QueryNode,
                      parent_source: Optional[str] = None) -> str:
            """Split a node into subqueries."""
            # Determine source for this node
            current_source = None
            if node.table_name:
                current_source = self._get_source_for_table(node.table_name)
            elif parent_source:
                current_source = parent_source
            
            # Create subquery if source changes
            if current_source and current_source != parent_source:
                subq = self._create_subquery_for_node(
                    node, current_source, dependencies, pushdown_ops
                )
                subqueries.append(subq)
                return current_source
            
            # Process child nodes
            if node.left:
                split_node(node.left, current_source)
            if node.right:
                split_node(node.right, current_source)
            for child in node.children:
                split_node(child, current_source)
            
            return current_source or parent_source or ''
        
        split_node(query.root)
        return subqueries
    
    def _optimize_splits(self, subqueries: List[SubQuery]) -> List[SubQuery]:
        """Optimize subquery splits for better performance."""
        # Merge small subqueries if beneficial
        merged = self._merge_small_subqueries(subqueries)
        
        # Reorder based on dependencies
        ordered = self._order_subqueries(merged)
        
        # Balance load across sources
        balanced = self._balance_load(ordered)
        
        return balanced
    
    def _merge_small_subqueries(self, 
                               subqueries: List[SubQuery]) -> List[SubQuery]:
        """Merge small subqueries to reduce overhead."""
        result = subqueries.copy()
        merged_any = True
        
        while merged_any:
            merged_any = False
            i = 0
            while i < len(result) - 1:
                if self._should_merge(result[i], result[i + 1]):
                    merged = self._merge_subqueries(result[i], result[i + 1])
                    result[i:i + 2] = [merged]
                    merged_any = True
                else:
                    i += 1
        
        return result
    
    def _order_subqueries(self, subqueries: List[SubQuery]) -> List[SubQuery]:
        """Order subqueries based on dependencies."""
        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        for subq in subqueries:
            graph[subq.query_plan.id] = subq.dependencies
        
        # Topological sort
        ordered: List[SubQuery] = []
        visited: Set[str] = set()
        
        def visit(subq: SubQuery) -> None:
            """Visit node in dependency graph."""
            if subq.query_plan.id in visited:
                return
            
            visited.add(subq.query_plan.id)
            for dep in subq.dependencies:
                dep_subq = next(
                    (sq for sq in subqueries if sq.query_plan.id == dep),
                    None
                )
                if dep_subq:
                    visit(dep_subq)
            
            ordered.append(subq)
        
        for subq in subqueries:
            visit(subq)
        
        return ordered
    
    def _balance_load(self, subqueries: List[SubQuery]) -> List[SubQuery]:
        """Balance load across data sources."""
        # Group by source
        by_source: Dict[str, List[SubQuery]] = {}
        for subq in subqueries:
            if subq.source_id in by_source:
                by_source[subq.source_id].append(subq)
            else:
                by_source[subq.source_id] = [subq]
        
        # Calculate load per source
        source_load: Dict[str, float] = {}
        for source_id, queries in by_source.items():
            source_load[source_id] = sum(sq.estimated_cost for sq in queries)
        
        # Rebalance if needed
        balanced = subqueries.copy()
        while self._needs_rebalancing(source_load):
            source_from = max(source_load.items(), key=lambda x: x[1])[0]
            source_to = min(source_load.items(), key=lambda x: x[1])[0]
            
            # Find query to move
            moveable = self._find_moveable_query(
                by_source[source_from],
                source_to
            )
            
            if moveable:
                self._move_query(
                    moveable,
                    source_from,
                    source_to,
                    by_source,
                    source_load
                )
        
        return balanced
    
    def _should_merge(self, sq1: SubQuery, sq2: SubQuery) -> bool:
        """Determine if two subqueries should be merged."""
        # Check if same source
        if sq1.source_id != sq2.source_id:
            return False
        
        # Check combined cost
        combined_cost = sq1.estimated_cost + sq2.estimated_cost
        if combined_cost > 1000:  # Threshold
            return False
        
        # Check dependencies
        if sq1.query_plan.id in sq2.dependencies or \
           sq2.query_plan.id in sq1.dependencies:
            return True
        
        return False
    
    def _merge_subqueries(self, sq1: SubQuery, sq2: SubQuery) -> SubQuery:
        """Merge two subqueries into one."""
        # Combine query plans
        merged_plan = self._merge_plans(sq1.query_plan, sq2.query_plan)
        
        # Combine dependencies
        merged_deps = sq1.dependencies | sq2.dependencies
        merged_deps.discard(sq1.query_plan.id)
        merged_deps.discard(sq2.query_plan.id)
        
        # Combine push-down operations
        merged_ops = list(set(sq1.push_down_operations + sq2.push_down_operations))
        
        return SubQuery(
            source_id=sq1.source_id,
            query_plan=merged_plan,
            dependencies=merged_deps,
            estimated_cost=sq1.estimated_cost + sq2.estimated_cost,
            estimated_rows=max(sq1.estimated_rows, sq2.estimated_rows),
            push_down_operations=merged_ops
        )
    
    def _merge_plans(self, plan1: QueryPlan, plan2: QueryPlan) -> QueryPlan:
        """Merge two query plans into one."""
        # Implementation depends on query plan structure
        pass
    
    def _needs_rebalancing(self, source_load: Dict[str, float]) -> bool:
        """Check if load needs rebalancing."""
        if not source_load:
            return False
        
        avg_load = sum(source_load.values()) / len(source_load)
        max_load = max(source_load.values())
        min_load = min(source_load.values())
        
        # Rebalance if max load is significantly higher than average
        return max_load > avg_load * 1.5 and max_load - min_load > 500
    
    def _find_moveable_query(self,
                           queries: List[SubQuery],
                           target_source: str) -> Optional[SubQuery]:
        """Find a query that can be moved to another source."""
        # Sort by cost ascending to prefer moving smaller queries
        sorted_queries = sorted(queries, key=lambda q: q.estimated_cost)
        
        for query in sorted_queries:
            if self._can_move_query(query, target_source):
                return query
        
        return None
    
    def _can_move_query(self, query: SubQuery, target_source: str) -> bool:
        """Check if a query can be moved to another source."""
        # Check if target source has required capabilities
        target_caps = self.source_capabilities.get(target_source, set())
        required_ops = set(query.push_down_operations)
        
        return required_ops.issubset(target_caps)
    
    def _move_query(self,
                   query: SubQuery,
                   source_from: str,
                   source_to: str,
                   by_source: Dict[str, List[SubQuery]],
                   source_load: Dict[str, float]) -> None:
        """Move a query from one source to another."""
        # Update source assignments
        by_source[source_from].remove(query)
        if source_to in by_source:
            by_source[source_to].append(query)
        else:
            by_source[source_to] = [query]
        
        # Update load calculations
        source_load[source_from] -= query.estimated_cost
        source_load[source_to] = source_load.get(source_to, 0) + query.estimated_cost
        
        # Update query source
        query.source_id = source_to
    
    def _get_source_for_table(self, table_name: str) -> Optional[str]:
        """Get the source ID for a table."""
        # Implementation depends on metadata storage
        pass