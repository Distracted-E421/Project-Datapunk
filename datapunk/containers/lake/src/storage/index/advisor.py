from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import logging
from .core import Index, IndexType
from .composite import CompositeIndex
from .bitmap import CompressionType

class QueryPattern:
    """Represents a query access pattern for index selection."""
    
    def __init__(self, table_name: str, columns: List[str], 
                 is_equality: bool = True, is_range: bool = False,
                 frequency: int = 1):
        self.table_name = table_name
        self.columns = columns
        self.is_equality = is_equality
        self.is_range = is_range
        self.frequency = frequency
        
    def __hash__(self) -> int:
        return hash((self.table_name, tuple(self.columns), 
                    self.is_equality, self.is_range))
                    
    def __eq__(self, other: 'QueryPattern') -> bool:
        return (self.table_name == other.table_name and
                self.columns == other.columns and
                self.is_equality == other.is_equality and
                self.is_range == other.is_range)

class ColumnStats:
    """Statistics about a column for index selection."""
    
    def __init__(self, distinct_values: int, null_count: int, total_rows: int):
        self.distinct_values = distinct_values
        self.null_count = null_count
        self.total_rows = total_rows
        self.cardinality = distinct_values / total_rows if total_rows > 0 else 1.0

class IndexAdvisor:
    """Recommends optimal indexes based on query patterns and statistics."""
    
    def __init__(self):
        self._query_patterns: Dict[str, List[QueryPattern]] = defaultdict(list)
        self._column_stats: Dict[str, Dict[str, ColumnStats]] = defaultdict(dict)
        self._existing_indexes: Dict[str, List[Index]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        
    def add_query_pattern(self, pattern: QueryPattern) -> None:
        """Register a query access pattern."""
        self._query_patterns[pattern.table_name].append(pattern)
        
    def add_column_stats(self, table_name: str, column_name: str, 
                        stats: ColumnStats) -> None:
        """Add statistics for a column."""
        self._column_stats[table_name][column_name] = stats
        
    def register_existing_index(self, index: Index) -> None:
        """Register an existing index."""
        self._existing_indexes[index.table_name].append(index)
        
    def recommend_indexes(self, table_name: str, 
                        max_indexes: int = 5) -> List[Tuple[List[str], IndexType]]:
        """Recommend optimal indexes for a table."""
        if table_name not in self._query_patterns:
            return []
            
        recommendations = []
        covered_patterns = set()
        
        # Sort patterns by frequency
        patterns = sorted(self._query_patterns[table_name],
                        key=lambda p: p.frequency, reverse=True)
                        
        # Check if existing indexes cover patterns
        for pattern in patterns:
            if self._is_pattern_covered(pattern):
                covered_patterns.add(pattern)
                
        # Recommend new indexes
        for pattern in patterns:
            if len(recommendations) >= max_indexes:
                break
            if pattern in covered_patterns:
                continue
                
            index_type = self._select_index_type(pattern)
            if index_type:
                recommendations.append((pattern.columns, index_type))
                covered_patterns.add(pattern)
                
        return recommendations
        
    def _is_pattern_covered(self, pattern: QueryPattern) -> bool:
        """Check if a pattern is covered by existing indexes."""
        for index in self._existing_indexes[pattern.table_name]:
            if self._covers_pattern(index, pattern):
                return True
        return False
        
    def _covers_pattern(self, index: Index, pattern: QueryPattern) -> bool:
        """Check if an index covers a query pattern."""
        # For composite indexes, check prefix matching
        if isinstance(index, CompositeIndex):
            if len(index.column_names) < len(pattern.columns):
                return False
            return all(a == b for a, b in zip(index.column_names, pattern.columns))
            
        # For single-column indexes
        return (index.column_names == pattern.columns and
                (not pattern.is_range or index.index_type == IndexType.BTREE))
                
    def _select_index_type(self, pattern: QueryPattern) -> Optional[IndexType]:
        """Select the most appropriate index type for a pattern."""
        if not pattern.columns:
            return None
            
        # Get statistics for the first column
        col_stats = self._column_stats.get(pattern.table_name, {}).get(pattern.columns[0])
        if not col_stats:
            self.logger.warning(f"No statistics available for {pattern.table_name}.{pattern.columns[0]}")
            return IndexType.BTREE  # Default to B-tree
            
        if pattern.is_range:
            return IndexType.BTREE  # Always use B-tree for range queries
            
        if col_stats.cardinality < 0.01:  # Very low cardinality
            return IndexType.BITMAP
        elif pattern.is_equality:
            return IndexType.HASH
        else:
            return IndexType.BTREE
            
    def analyze_workload(self) -> Dict[str, List[str]]:
        """Analyze the current workload and provide recommendations."""
        recommendations = defaultdict(list)
        
        for table_name in self._query_patterns:
            index_recs = self.recommend_indexes(table_name)
            
            for columns, index_type in index_recs:
                rec = f"Create {index_type.name} index on ({', '.join(columns)})"
                if (index_type == IndexType.BITMAP and
                    self._should_use_compression(table_name, columns[0])):
                    rec += " with compression"
                recommendations[table_name].append(rec)
                
        return dict(recommendations)
        
    def _should_use_compression(self, table_name: str, column_name: str) -> bool:
        """Determine if bitmap compression would be beneficial."""
        stats = self._column_stats.get(table_name, {}).get(column_name)
        if not stats:
            return False
            
        # Recommend compression for very low cardinality columns with many rows
        return stats.cardinality < 0.001 and stats.total_rows > 100000 