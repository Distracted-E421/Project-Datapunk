from typing import List, Tuple, Optional, Any, Dict, Generic, TypeVar, Protocol, runtime_checkable
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from abc import ABC, abstractmethod

from .core import Index, IndexType, IndexStats

K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type

@runtime_checkable
class GiSTPredicateStrategy(Protocol[K]):
    """Protocol defining the strategy for predicate operations."""
    
    def consistent(self, entry: K, query: Any) -> bool:
        """Check if entry is consistent with query."""
        ...
        
    def union(self, entries: List[K]) -> K:
        """Create union predicate for a list of entries."""
        ...
        
    def compress(self, entry: K) -> K:
        """Compress an entry, possibly losing information but maintaining consistency."""
        ...
        
    def decompress(self, entry: K) -> K:
        """Decompress an entry if it was previously compressed."""
        ...
        
    def penalty(self, entry1: K, entry2: K) -> float:
        """Calculate penalty for inserting entry2 into subtree rooted at entry1."""
        ...
        
    def pick_split(self, entries: List[K]) -> Tuple[List[K], List[K]]:
        """Split a set of entries into two groups."""
        ...

@dataclass
class GiSTNode(Generic[K, V]):
    """Node in the GiST structure."""
    is_leaf: bool
    entries: List[Tuple[K, Union[V, 'GiSTNode[K, V]']]]
    
    def __init__(self, is_leaf: bool = True):
        self.is_leaf = is_leaf
        self.entries = []

class GiSTIndex(Index, Generic[K, V]):
    """Generalized Search Tree implementation."""
    
    def __init__(
        self,
        name: str,
        table_name: str,
        columns: List[str],
        predicate_strategy: GiSTPredicateStrategy[K],
        max_entries: int = 50,
        min_entries: Optional[int] = None,
        **kwargs
    ):
        super().__init__(name, table_name, columns)
        self.strategy = predicate_strategy
        self.max_entries = max_entries
        self.min_entries = min_entries or max(2, self.max_entries // 3)
        self.root = GiSTNode[K, V](is_leaf=True)
        self.size = 0
        
        # Performance tracking
        self._insert_times: List[float] = []
        self._search_times: List[float] = []
        self._last_rebuild: Optional[datetime] = None
        
    def insert(self, key: K, value: V):
        """Insert a key-value pair into the index."""
        start_time = datetime.now()
        
        if len(self.root.entries) >= self.max_entries and self.root.is_leaf:
            # Split root if it's a leaf and full
            new_root = GiSTNode[K, V](is_leaf=False)
            new_root.entries = [(self.strategy.compress(key), self.root)]
            self.root = new_root
            self._split_node(self.root, 0)
            
        self._insert_recursive(self.root, key, value)
        self.size += 1
        
        # Track performance
        self._insert_times.append((datetime.now() - start_time).total_seconds())
        
    def _insert_recursive(self, node: GiSTNode[K, V], key: K, value: V):
        """Recursively insert an entry into the tree."""
        if node.is_leaf:
            node.entries.append((key, value))
        else:
            # Choose subtree
            best_idx = self._choose_subtree(node, key)
            child_node = node.entries[best_idx][1]
            if isinstance(child_node, GiSTNode):
                self._insert_recursive(child_node, key, value)
                
                # Update predicate
                node.entries[best_idx] = (
                    self.strategy.union([e[0] for e in child_node.entries]),
                    child_node
                )
                
                # Check if node needs splitting
                if len(child_node.entries) > self.max_entries:
                    self._split_node(node, best_idx)
            else:
                raise ValueError("Non-leaf node contains value instead of child node")
                
    def _choose_subtree(self, node: GiSTNode[K, V], key: K) -> int:
        """Choose the best subtree for insertion."""
        min_penalty = float('inf')
        best_idx = 0
        
        for i, (entry_key, _) in enumerate(node.entries):
            penalty = self.strategy.penalty(entry_key, key)
            if penalty < min_penalty:
                min_penalty = penalty
                best_idx = i
                
        return best_idx
    
    def _split_node(self, parent: GiSTNode[K, V], entry_idx: int):
        """Split a node when it exceeds maximum entries."""
        node = parent.entries[entry_idx][1]
        if not isinstance(node, GiSTNode):
            raise ValueError("Cannot split leaf entry")
            
        # Get entries to split
        entries = node.entries
        
        # Use strategy to split entries
        group1, group2 = self.strategy.pick_split([e[0] for e in entries])
        
        # Create new nodes
        left = GiSTNode[K, V](is_leaf=node.is_leaf)
        right = GiSTNode[K, V](is_leaf=node.is_leaf)
        
        # Distribute entries
        entry_dict = {e[0]: e[1] for e in entries}
        left.entries = [(k, entry_dict[k]) for k in group1]
        right.entries = [(k, entry_dict[k]) for k in group2]
        
        # Update parent
        parent.entries[entry_idx] = (
            self.strategy.union([e[0] for e in left.entries]),
            left
        )
        parent.entries.insert(entry_idx + 1, (
            self.strategy.union([e[0] for e in right.entries]),
            right
        ))
        
    def search(self, query: Any) -> List[V]:
        """Search for entries matching the query."""
        start_time = datetime.now()
        results = []
        self._search_recursive(self.root, query, results)
        
        # Track performance
        self._search_times.append((datetime.now() - start_time).total_seconds())
        return results
    
    def _search_recursive(self, node: GiSTNode[K, V], query: Any, results: List[V]):
        """Recursively search the tree."""
        for key, value in node.entries:
            if self.strategy.consistent(key, query):
                if node.is_leaf:
                    results.append(value)
                else:
                    if isinstance(value, GiSTNode):
                        self._search_recursive(value, query, results)
                    else:
                        raise ValueError("Non-leaf node contains value instead of child node")
                        
    def get_statistics(self) -> IndexStats:
        """Get index statistics."""
        return IndexStats(
            total_entries=self.size,
            depth=self._compute_depth(),
            size_bytes=self._compute_size(),
            last_updated=datetime.now(),
            read_count=len(self._search_times),
            write_count=len(self._insert_times),
            avg_lookup_time_ms=np.mean(self._search_times) * 1000 if self._search_times else 0,
            avg_insert_time_ms=np.mean(self._insert_times) * 1000 if self._insert_times else 0
        )
        
    def _compute_depth(self) -> int:
        """Compute the depth of the tree."""
        def get_depth(node: GiSTNode[K, V]) -> int:
            if node.is_leaf:
                return 1
            max_depth = 0
            for _, child in node.entries:
                if isinstance(child, GiSTNode):
                    max_depth = max(max_depth, get_depth(child))
            return 1 + max_depth
            
        return get_depth(self.root)
    
    def _compute_size(self) -> int:
        """Estimate the memory size of the index."""
        def node_size(node: GiSTNode[K, V]) -> int:
            size = 8  # Python object overhead
            size += 24  # list overhead
            size += len(node.entries) * 16  # tuple overhead
            return size
            
        def recursive_size(node: GiSTNode[K, V]) -> int:
            size = node_size(node)
            if not node.is_leaf:
                for _, child in node.entries:
                    if isinstance(child, GiSTNode):
                        size += recursive_size(child)
            return size
            
        return recursive_size(self.root)
    
    def cleanup(self):
        """Clean up resources."""
        self.root = None
        self._insert_times = []
        self._search_times = []
        self.size = 0 