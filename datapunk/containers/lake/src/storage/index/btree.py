from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime
import bisect
from .core import Index, IndexType

K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type

@dataclass
class BTreeNode(Generic[K, V]):
    """Node in a B-tree."""
    keys: List[K]
    values: List[V]
    children: List['BTreeNode[K, V]']
    is_leaf: bool
    
    def __init__(self, is_leaf: bool = True):
        self.keys = []
        self.values = []
        self.children = []
        self.is_leaf = is_leaf

class BTreeIndex(Index[K, V]):
    """B-tree index implementation."""
    
    def __init__(
        self,
        name: str,
        key_type: str,
        value_type: str,
        order: int = 4,  # Default B-tree order
        is_unique: bool = False,
        is_primary: bool = False,
        properties: Dict[str, Any] = None
    ):
        super().__init__(
            name,
            key_type,
            value_type,
            is_unique,
            is_primary,
            properties
        )
        self.order = order
        self.root = BTreeNode[K, V](is_leaf=True)
        self.stats.depth = 1
        
    def insert(self, key: K, value: V) -> None:
        """Insert a key-value pair into the B-tree."""
        start_time = datetime.now()
        
        with self._lock:
            if self.is_unique and self.search(key) is not None:
                raise ValueError(f"Duplicate key {key} in unique index")
                
            # Handle root split if needed
            if len(self.root.keys) == (2 * self.order - 1):
                new_root = BTreeNode[K, V](is_leaf=False)
                new_root.children.append(self.root)
                self._split_child(new_root, 0)
                self.root = new_root
                self.stats.depth += 1
                
            self._insert_non_full(self.root, key, value)
            self.stats.total_entries += 1
            
        duration = (datetime.now() - start_time).total_seconds() * 1000
        self.update_stats('write', duration)
        
    def delete(self, key: K) -> None:
        """Delete a key from the B-tree."""
        with self._lock:
            if not self._delete_key(self.root, key):
                raise KeyError(f"Key {key} not found")
                
            # If root is empty and has children, promote first child
            if not self.root.keys and self.root.children:
                self.root = self.root.children[0]
                self.stats.depth -= 1
                
            self.stats.total_entries -= 1
            
    def search(self, key: K) -> Optional[V]:
        """Search for a value by key."""
        start_time = datetime.now()
        
        with self._lock:
            result = self._search_node(self.root, key)
            
        duration = (datetime.now() - start_time).total_seconds() * 1000
        self.update_stats('read', duration)
        
        return result
        
    def range_search(self, start_key: K, end_key: K) -> List[V]:
        """Search for values in a key range."""
        start_time = datetime.now()
        result = []
        
        with self._lock:
            self._range_search_node(self.root, start_key, end_key, result)
            
        duration = (datetime.now() - start_time).total_seconds() * 1000
        self.update_stats('read', duration)
        
        return result
        
    def clear(self) -> None:
        """Clear all entries from the B-tree."""
        with self._lock:
            self.root = BTreeNode[K, V](is_leaf=True)
            self.stats.total_entries = 0
            self.stats.depth = 1
            
    def _get_index_type(self) -> IndexType:
        """Get the type of this index."""
        return IndexType.BTREE
        
    def _get_indexed_columns(self) -> List[str]:
        """Get the columns covered by this index."""
        return self.properties.get('columns', [])
        
    def optimize(self) -> None:
        """Optimize the B-tree structure."""
        with self._lock:
            # Rebalance tree if needed
            self._rebalance(self.root)
            
    def _search_node(
        self,
        node: BTreeNode[K, V],
        key: K
    ) -> Optional[V]:
        """Search for a key in a node and its children."""
        i = bisect.bisect_left(node.keys, key)
        
        if i < len(node.keys) and node.keys[i] == key:
            return node.values[i]
            
        if node.is_leaf:
            return None
            
        return self._search_node(node.children[i], key)
        
    def _range_search_node(
        self,
        node: BTreeNode[K, V],
        start_key: K,
        end_key: K,
        result: List[V]
    ) -> None:
        """Search for keys in a range in a node and its children."""
        i = bisect.bisect_left(node.keys, start_key)
        
        # Add values from current node
        while i < len(node.keys) and node.keys[i] <= end_key:
            if node.keys[i] >= start_key:
                result.append(node.values[i])
            i += 1
            
        # Recurse into children if not leaf
        if not node.is_leaf:
            j = bisect.bisect_right(node.keys, start_key)
            while j < len(node.children) and \
                  (j == 0 or node.keys[j-1] <= end_key):
                self._range_search_node(
                    node.children[j],
                    start_key,
                    end_key,
                    result
                )
                j += 1
                
    def _insert_non_full(
        self,
        node: BTreeNode[K, V],
        key: K,
        value: V
    ) -> None:
        """Insert into a non-full node."""
        i = len(node.keys) - 1
        
        if node.is_leaf:
            # Insert into leaf node
            insert_pos = bisect.bisect_left(node.keys, key)
            node.keys.insert(insert_pos, key)
            node.values.insert(insert_pos, value)
        else:
            # Find child to recurse into
            i = bisect.bisect_right(node.keys, key)
            if len(node.children[i].keys) == (2 * self.order - 1):
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)
            
    def _split_child(
        self,
        parent: BTreeNode[K, V],
        child_index: int
    ) -> None:
        """Split a child node."""
        child = parent.children[child_index]
        new_node = BTreeNode[K, V](is_leaf=child.is_leaf)
        
        # Move half of keys and values to new node
        mid = self.order - 1
        new_node.keys = child.keys[mid+1:]
        new_node.values = child.values[mid+1:]
        
        # If not leaf, move children too
        if not child.is_leaf:
            new_node.children = child.children[mid+1:]
            child.children = child.children[:mid+1]
            
        # Insert middle key and value into parent
        parent.keys.insert(child_index, child.keys[mid])
        parent.values.insert(child_index, child.values[mid])
        parent.children.insert(child_index + 1, new_node)
        
        # Update original child
        child.keys = child.keys[:mid]
        child.values = child.values[:mid]
        
    def _delete_key(
        self,
        node: BTreeNode[K, V],
        key: K
    ) -> bool:
        """Delete a key from a node and its children."""
        i = bisect.bisect_left(node.keys, key)
        
        if i < len(node.keys) and node.keys[i] == key:
            if node.is_leaf:
                # Delete from leaf
                node.keys.pop(i)
                node.values.pop(i)
                return True
            else:
                # Delete from internal node
                return self._delete_from_internal(node, i)
                
        if node.is_leaf:
            return False
            
        # Ensure child has enough keys
        if len(node.children[i].keys) < self.order:
            self._fill_child(node, i)
            
        # Recurse into appropriate child
        if i >= len(node.children):
            return self._delete_key(node.children[i-1], key)
        return self._delete_key(node.children[i], key)
        
    def _delete_from_internal(
        self,
        node: BTreeNode[K, V],
        index: int
    ) -> bool:
        """Delete a key from an internal node."""
        key = node.keys[index]
        
        # Case 1: If left child has >= order keys
        if len(node.children[index].keys) >= self.order:
            pred_key, pred_value = self._get_predecessor(node, index)
            node.keys[index] = pred_key
            node.values[index] = pred_value
            return self._delete_key(node.children[index], pred_key)
            
        # Case 2: If right child has >= order keys
        elif len(node.children[index+1].keys) >= self.order:
            succ_key, succ_value = self._get_successor(node, index)
            node.keys[index] = succ_key
            node.values[index] = succ_value
            return self._delete_key(node.children[index+1], succ_key)
            
        # Case 3: Merge children
        else:
            self._merge_children(node, index)
            return self._delete_key(node.children[index], key)
            
    def _get_predecessor(
        self,
        node: BTreeNode[K, V],
        index: int
    ) -> tuple[K, V]:
        """Get predecessor key-value pair."""
        curr = node.children[index]
        while not curr.is_leaf:
            curr = curr.children[-1]
        return curr.keys[-1], curr.values[-1]
        
    def _get_successor(
        self,
        node: BTreeNode[K, V],
        index: int
    ) -> tuple[K, V]:
        """Get successor key-value pair."""
        curr = node.children[index+1]
        while not curr.is_leaf:
            curr = curr.children[0]
        return curr.keys[0], curr.values[0]
        
    def _fill_child(
        self,
        node: BTreeNode[K, V],
        index: int
    ) -> None:
        """Fill child node that has fewer than order-1 keys."""
        if index != 0 and len(node.children[index-1].keys) >= self.order:
            self._borrow_from_prev(node, index)
        elif index != len(node.children)-1 and \
             len(node.children[index+1].keys) >= self.order:
            self._borrow_from_next(node, index)
        else:
            if index != len(node.children)-1:
                self._merge_children(node, index)
            else:
                self._merge_children(node, index-1)
                
    def _borrow_from_prev(
        self,
        node: BTreeNode[K, V],
        index: int
    ) -> None:
        """Borrow a key from previous sibling."""
        child = node.children[index]
        sibling = node.children[index-1]
        
        # Move parent key to child
        child.keys.insert(0, node.keys[index-1])
        child.values.insert(0, node.values[index-1])
        
        # Move sibling's last key to parent
        node.keys[index-1] = sibling.keys[-1]
        node.values[index-1] = sibling.values[-1]
        
        if not child.is_leaf:
            child.children.insert(0, sibling.children.pop())
            
        sibling.keys.pop()
        sibling.values.pop()
        
    def _borrow_from_next(
        self,
        node: BTreeNode[K, V],
        index: int
    ) -> None:
        """Borrow a key from next sibling."""
        child = node.children[index]
        sibling = node.children[index+1]
        
        # Move parent key to child
        child.keys.append(node.keys[index])
        child.values.append(node.values[index])
        
        # Move sibling's first key to parent
        node.keys[index] = sibling.keys[0]
        node.values[index] = sibling.values[0]
        
        if not child.is_leaf:
            child.children.append(sibling.children.pop(0))
            
        sibling.keys.pop(0)
        sibling.values.pop(0)
        
    def _merge_children(
        self,
        node: BTreeNode[K, V],
        index: int
    ) -> None:
        """Merge two child nodes."""
        child = node.children[index]
        sibling = node.children[index+1]
        
        # Add parent key to child
        child.keys.append(node.keys[index])
        child.values.append(node.values[index])
        
        # Add sibling's keys and children to child
        child.keys.extend(sibling.keys)
        child.values.extend(sibling.values)
        if not child.is_leaf:
            child.children.extend(sibling.children)
            
        # Remove parent key and sibling
        node.keys.pop(index)
        node.values.pop(index)
        node.children.pop(index+1)
        
    def _rebalance(self, node: BTreeNode[K, V]) -> None:
        """Rebalance a node and its children."""
        if not node.is_leaf:
            # Rebalance children first
            for child in node.children:
                self._rebalance(child)
                
            # Check if node needs rebalancing
            min_keys = (2 * self.order - 1) // 3
            if len(node.keys) < min_keys:
                # Try to borrow or merge
                parent_index = self._find_parent_index(node)
                if parent_index is not None:
                    self._fill_child(self.root, parent_index) 