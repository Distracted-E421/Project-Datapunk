from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from ..parser.query_parser_core import QueryNode, QueryType
from ...storage.index.core import Index, IndexType
from ...storage.index.maintenance import IndexMaintenanceManager

@dataclass
class IndexAccessPath:
    """Represents a possible index access path for query execution."""
    index: Index
    cost: float
    columns_covered: List[str]
    supports_ordering: bool
    is_range_scan: bool
    estimated_rows: int

class IndexAwareOptimizer:
    """Query optimizer that leverages available indexes."""
    
    def __init__(self, maintenance_manager: IndexMaintenanceManager):
        self.maintenance_manager = maintenance_manager
        self.table_indexes: Dict[str, List[Index]] = {}
        
    def register_table_indexes(self, table_name: str, indexes: List[Index]) -> None:
        """Register available indexes for a table."""
        self.table_indexes[table_name] = indexes
        
    def optimize_query(self, query_node: QueryNode) -> QueryNode:
        """Optimize a query using available indexes."""
        if query_node.query_type == QueryType.SELECT:
            return self._optimize_select(query_node)
        return query_node
        
    def _optimize_select(self, select_node: QueryNode) -> QueryNode:
        """Optimize a SELECT query."""
        # Find best indexes for each table
        table_access_paths = {}
        for table in select_node.tables:
            access_path = self._find_best_access_path(
                table,
                select_node.conditions,
                select_node.order_by
            )
            if access_path:
                table_access_paths[table] = access_path
                
        # Modify query plan based on chosen access paths
        optimized_node = self._apply_access_paths(select_node, table_access_paths)
        
        # Record index usage patterns
        self._record_index_usage(table_access_paths)
        
        return optimized_node
        
    def _find_best_access_path(self, table_name: str, 
                              conditions: List[Any],
                              order_by: Optional[List[str]] = None) -> Optional[IndexAccessPath]:
        """Find the best index access path for a table."""
        if table_name not in self.table_indexes:
            return None
            
        candidate_paths = []
        for index in self.table_indexes[table_name]:
            path = self._evaluate_index(index, conditions, order_by)
            if path:
                candidate_paths.append(path)
                
        if not candidate_paths:
            return None
            
        # Choose the lowest cost path
        return min(candidate_paths, key=lambda p: p.cost)
        
    def _evaluate_index(self, index: Index, conditions: List[Any],
                       order_by: Optional[List[str]] = None) -> Optional[IndexAccessPath]:
        """Evaluate an index for query conditions."""
        covered_columns = []
        is_range_scan = False
        
        # Check which conditions can use this index
        for condition in conditions:
            if self._can_use_index(index, condition):
                covered_columns.extend(self._get_condition_columns(condition))
                if self._is_range_condition(condition):
                    is_range_scan = True
                    
        if not covered_columns:
            return None
            
        # Calculate cost based on index statistics
        stats = self.maintenance_manager.get_index_statistics().get(index.name, {})
        avg_lookup_time = stats.get("avg_lookup_time_ms", 1.0)
        estimated_rows = self._estimate_rows(index, conditions)
        
        # Adjust cost based on various factors
        cost = avg_lookup_time
        if is_range_scan:
            cost *= (estimated_rows / 100)  # Penalize range scans
        if stats.get("fragmentation", 0) > 20:
            cost *= 1.2  # Penalize fragmented indexes
            
        # Check if index supports required ordering
        supports_ordering = False
        if order_by and set(order_by).issubset(set(index.column_names)):
            supports_ordering = True
            cost *= 0.8  # Reward indexes that support ordering
            
        return IndexAccessPath(
            index=index,
            cost=cost,
            columns_covered=covered_columns,
            supports_ordering=supports_ordering,
            is_range_scan=is_range_scan,
            estimated_rows=estimated_rows
        )
        
    def _can_use_index(self, index: Index, condition: Any) -> bool:
        """Check if an index can be used for a condition."""
        columns = self._get_condition_columns(condition)
        if not columns:
            return False
            
        # For composite indexes, check prefix matching
        index_columns = index.column_names
        return all(col in index_columns for col in columns)
        
    def _get_condition_columns(self, condition: Any) -> List[str]:
        """Extract column names from a condition."""
        # This is a placeholder - actual implementation would depend on
        # how conditions are represented in your query nodes
        return []
        
    def _is_range_condition(self, condition: Any) -> bool:
        """Check if a condition involves a range comparison."""
        # This is a placeholder - actual implementation would depend on
        # how conditions are represented in your query nodes
        return False
        
    def _estimate_rows(self, index: Index, conditions: List[Any]) -> int:
        """Estimate number of rows that will be returned."""
        # This is a placeholder - actual implementation would use
        # index statistics and condition selectivity estimation
        return 1000
        
    def _apply_access_paths(self, select_node: QueryNode,
                          access_paths: Dict[str, IndexAccessPath]) -> QueryNode:
        """Modify query plan to use chosen access paths."""
        # This is a placeholder - actual implementation would modify
        # the query plan based on chosen access paths
        return select_node
        
    def _record_index_usage(self, access_paths: Dict[str, IndexAccessPath]) -> None:
        """Record index usage patterns for future optimization."""
        for table_name, path in access_paths.items():
            self.maintenance_manager.collect_query_patterns(
                path.index.name,
                path.columns_covered,
                path.is_range_scan
            ) 