from typing import Any, Dict, List, Optional, Tuple, Union
from .core import Index, IndexType
from .btree import BTreeIndex
from .hash import HashIndex
from .bitmap import BitmapIndex, CompressionType

class CompositeKey:
    """Represents a composite key for multi-column indexes."""
    
    def __init__(self, values: List[Any]):
        self.values = tuple(values)  # Immutable tuple for hashing
        
    def __eq__(self, other: 'CompositeKey') -> bool:
        return self.values == other.values
        
    def __lt__(self, other: 'CompositeKey') -> bool:
        return self.values < other.values
        
    def __hash__(self) -> int:
        return hash(self.values)
        
    def __str__(self) -> str:
        return f"CompositeKey{self.values}"
        
    def partial_match(self, prefix: List[Any]) -> bool:
        """Check if this key matches a prefix of values."""
        return self.values[:len(prefix)] == tuple(prefix)

class CompositeIndex(Index):
    """Multi-column index implementation supporting various index types."""
    
    def __init__(self, name: str, table_name: str, column_names: List[str],
                 index_type: IndexType = IndexType.BTREE,
                 bitmap_compression: str = CompressionType.NONE):
        super().__init__(name, table_name, column_names, index_type)
        
        # Create appropriate underlying index
        if index_type == IndexType.BTREE:
            self._index = BTreeIndex(name, table_name, column_names)
        elif index_type == IndexType.HASH:
            self._index = HashIndex(name, table_name, column_names)
        elif index_type == IndexType.BITMAP:
            self._index = BitmapIndex(name, table_name, column_names, bitmap_compression)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")
            
        self._column_count = len(column_names)
        self._statistics: Dict[str, Dict[str, Any]] = {
            col: {"distinct_values": 0, "null_count": 0} 
            for col in column_names
        }
        
    def insert(self, values: List[Any], row_id: int) -> None:
        """Insert a new multi-column key into the index."""
        if len(values) != self._column_count:
            raise ValueError(
                f"Expected {self._column_count} values, got {len(values)}")
            
        # Update column statistics
        for i, value in enumerate(values):
            col = self.column_names[i]
            if value is None:
                self._statistics[col]["null_count"] += 1
                
        composite_key = CompositeKey(values)
        self._index.insert(composite_key, row_id)
        
    def delete(self, values: List[Any], row_id: int) -> None:
        """Remove a multi-column key from the index."""
        if len(values) != self._column_count:
            raise ValueError(
                f"Expected {self._column_count} values, got {len(values)}")
            
        # Update column statistics
        for i, value in enumerate(values):
            col = self.column_names[i]
            if value is None:
                self._statistics[col]["null_count"] -= 1
                
        composite_key = CompositeKey(values)
        self._index.delete(composite_key, row_id)
        
    def search(self, values: List[Any]) -> List[int]:
        """Search for row IDs matching the given values.
        
        Supports partial matches where len(values) <= number of columns.
        """
        if len(values) > self._column_count:
            raise ValueError(
                f"Too many values: expected <= {self._column_count}, got {len(values)}")
                
        if isinstance(self._index, BTreeIndex):
            # For B-tree, we can do prefix search
            return self._prefix_search(values)
        else:
            # For other types, we need exact match
            return self._exact_search(values)
            
    def _prefix_search(self, prefix: List[Any]) -> List[int]:
        """Search for entries matching a prefix of values (B-tree only)."""
        if not isinstance(self._index, BTreeIndex):
            raise NotImplementedError("Prefix search only supported for B-tree indexes")
            
        result = []
        for key, row_ids in self._index.range_iterate():
            if isinstance(key, CompositeKey) and key.partial_match(prefix):
                result.extend(row_ids)
        return result
        
    def _exact_search(self, values: List[Any]) -> List[int]:
        """Search for exact matches only."""
        if len(values) != self._column_count:
            return []  # Require exact match for non-B-tree indexes
            
        composite_key = CompositeKey(values)
        return self._index.search(composite_key)
        
    def range_search(self, start_values: List[Any], end_values: List[Any]) -> List[int]:
        """Perform a range search on the composite key."""
        if len(start_values) != len(end_values):
            raise ValueError("Start and end value lists must have same length")
        if len(start_values) > self._column_count:
            raise ValueError(f"Too many values: expected <= {self._column_count}")
            
        # Only B-tree supports true range search
        if not isinstance(self._index, BTreeIndex):
            raise NotImplementedError("Range search only supported for B-tree indexes")
            
        start_key = CompositeKey(start_values)
        end_key = CompositeKey(end_values)
        return self._index.range_search(start_key, end_key)
        
    def rebuild(self) -> None:
        """Rebuild the underlying index."""
        self._index.rebuild()
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the composite index."""
        base_stats = self._index.get_statistics()
        
        # Add composite-specific statistics
        stats = {
            **base_stats,
            "column_count": self._column_count,
            "column_stats": self._statistics,
            "index_type": str(self.index_type),
            "supports_prefix_search": isinstance(self._index, BTreeIndex),
            "supports_range_search": isinstance(self._index, BTreeIndex)
        }
        
        return stats 