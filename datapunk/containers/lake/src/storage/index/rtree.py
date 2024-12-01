from typing import List, Tuple, Optional, Any, Dict
from dataclasses import dataclass
import numpy as np
from datetime import datetime

from .core import Index, IndexType, IndexStats
from ..geometry import BoundingBox, Point, Polygon

@dataclass
class RTreeNode:
    """Node in the R-tree structure."""
    bbox: BoundingBox
    children: List['RTreeNode']
    entries: List[Tuple[BoundingBox, Any]]  # (bbox, value) for leaf nodes
    is_leaf: bool
    
    def __init__(self, is_leaf: bool = False):
        self.bbox = BoundingBox.empty()
        self.children = []
        self.entries = []
        self.is_leaf = is_leaf

class RTreeIndex(Index):
    """R-tree implementation for spatial data indexing."""
    
    def __init__(
        self,
        name: str,
        table_name: str,
        columns: List[str],
        max_entries: int = 50,
        min_entries: Optional[int] = None,
        dimension: int = 2,
        **kwargs
    ):
        super().__init__(name, table_name, columns)
        self.max_entries = max_entries
        self.min_entries = min_entries or max(2, self.max_entries // 3)
        self.dimension = dimension
        self.root = RTreeNode(is_leaf=True)
        self.size = 0
        
        # Performance tracking
        self._insert_times: List[float] = []
        self._search_times: List[float] = []
        self._last_rebuild: Optional[datetime] = None
        
    def insert(self, bbox: BoundingBox, value: Any):
        """Insert a spatial object into the index."""
        start_time = datetime.now()
        
        if len(self.root.entries) >= self.max_entries and self.root.is_leaf:
            # Split root if it's a leaf and full
            new_root = RTreeNode(is_leaf=False)
            new_root.children = [self.root]
            new_root.bbox = self.root.bbox
            self.root = new_root
            self._split_node(self.root, 0)
            
        self._insert_recursive(self.root, bbox, value)
        self.size += 1
        
        # Track performance
        self._insert_times.append((datetime.now() - start_time).total_seconds())
        
    def _insert_recursive(self, node: RTreeNode, bbox: BoundingBox, value: Any):
        """Recursively insert an entry into the tree."""
        if node.is_leaf:
            node.entries.append((bbox, value))
            node.bbox = node.bbox.union(bbox)
        else:
            # Choose subtree
            best_child = self._choose_subtree(node, bbox)
            self._insert_recursive(best_child, bbox, value)
            
            # Update bounding box
            node.bbox = BoundingBox.empty()
            for child in node.children:
                node.bbox = node.bbox.union(child.bbox)
                
            # Check if node needs splitting
            if len(node.children) > self.max_entries:
                self._split_node(node, node.children.index(best_child))
                
    def _choose_subtree(self, node: RTreeNode, bbox: BoundingBox) -> RTreeNode:
        """Choose the best subtree for insertion."""
        min_increase = float('inf')
        best_child = None
        
        for child in node.children:
            increase = child.bbox.union(bbox).area() - child.bbox.area()
            if increase < min_increase:
                min_increase = increase
                best_child = child
                
        return best_child
    
    def _split_node(self, node: RTreeNode, promoted_index: int):
        """Split a node when it exceeds maximum entries."""
        if node.is_leaf:
            entries = node.entries
        else:
            entries = [(child.bbox, child) for child in node.children]
            
        # Choose split axis and index using the R*-tree algorithm
        axis = self._choose_split_axis(entries)
        index = self._choose_split_index(entries, axis)
        
        # Create new nodes
        left = RTreeNode(is_leaf=node.is_leaf)
        right = RTreeNode(is_leaf=node.is_leaf)
        
        # Sort entries by the chosen axis
        entries.sort(key=lambda x: x[0].center()[axis])
        
        # Distribute entries
        if node.is_leaf:
            left.entries = entries[:index]
            right.entries = entries[index:]
        else:
            left.children = [e[1] for e in entries[:index]]
            right.children = [e[1] for e in entries[index:]]
            
        # Update bounding boxes
        left.bbox = BoundingBox.empty()
        right.bbox = BoundingBox.empty()
        
        if node.is_leaf:
            for bbox, _ in left.entries:
                left.bbox = left.bbox.union(bbox)
            for bbox, _ in right.entries:
                right.bbox = right.bbox.union(bbox)
        else:
            for child in left.children:
                left.bbox = left.bbox.union(child.bbox)
            for child in right.children:
                right.bbox = right.bbox.union(child.bbox)
                
        # Update parent
        if node == self.root:
            new_root = RTreeNode(is_leaf=False)
            new_root.children = [left, right]
            new_root.bbox = left.bbox.union(right.bbox)
            self.root = new_root
        else:
            parent = self._find_parent(self.root, node)
            parent.children[promoted_index] = left
            parent.children.insert(promoted_index + 1, right)
            
    def _choose_split_axis(self, entries: List[Tuple[BoundingBox, Any]]) -> int:
        """Choose the best axis for splitting using the R*-tree algorithm."""
        min_margin = float('inf')
        best_axis = 0
        
        for axis in range(self.dimension):
            margin = self._compute_margin_value(entries, axis)
            if margin < min_margin:
                min_margin = margin
                best_axis = axis
                
        return best_axis
    
    def _choose_split_index(self, entries: List[Tuple[BoundingBox, Any]], axis: int) -> int:
        """Choose the best split index using the R*-tree algorithm."""
        entries.sort(key=lambda x: x[0].center()[axis])
        
        min_overlap = float('inf')
        best_index = self.min_entries
        
        for i in range(self.min_entries, len(entries) - self.min_entries + 1):
            overlap = self._compute_overlap_value(entries, i)
            if overlap < min_overlap:
                min_overlap = overlap
                best_index = i
                
        return best_index
    
    def _compute_margin_value(self, entries: List[Tuple[BoundingBox, Any]], axis: int) -> float:
        """Compute the margin value for a set of entries along an axis."""
        entries.sort(key=lambda x: x[0].center()[axis])
        margin_sum = 0
        
        for i in range(self.min_entries, len(entries) - self.min_entries + 1):
            left_box = BoundingBox.empty()
            right_box = BoundingBox.empty()
            
            for j in range(i):
                left_box = left_box.union(entries[j][0])
            for j in range(i, len(entries)):
                right_box = right_box.union(entries[j][0])
                
            margin_sum += left_box.perimeter() + right_box.perimeter()
            
        return margin_sum
    
    def _compute_overlap_value(self, entries: List[Tuple[BoundingBox, Any]], split_index: int) -> float:
        """Compute the overlap value for a potential split."""
        left_box = BoundingBox.empty()
        right_box = BoundingBox.empty()
        
        for i in range(split_index):
            left_box = left_box.union(entries[i][0])
        for i in range(split_index, len(entries)):
            right_box = right_box.union(entries[i][0])
            
        return left_box.intersection_area(right_box)
    
    def _find_parent(self, node: RTreeNode, target: RTreeNode) -> Optional[RTreeNode]:
        """Find the parent node of a given node."""
        if node.is_leaf:
            return None
            
        for child in node.children:
            if child == target:
                return node
            parent = self._find_parent(child, target)
            if parent:
                return parent
                
        return None
    
    def search(self, query_bbox: BoundingBox) -> List[Any]:
        """Search for objects that intersect with the query bbox."""
        start_time = datetime.now()
        results = []
        self._search_recursive(self.root, query_bbox, results)
        
        # Track performance
        self._search_times.append((datetime.now() - start_time).total_seconds())
        return results
    
    def _search_recursive(self, node: RTreeNode, query_bbox: BoundingBox, results: List[Any]):
        """Recursively search the tree."""
        if not node.bbox.intersects(query_bbox):
            return
            
        if node.is_leaf:
            for bbox, value in node.entries:
                if bbox.intersects(query_bbox):
                    results.append(value)
        else:
            for child in node.children:
                self._search_recursive(child, query_bbox, results)
                
    def nearest(self, point: Point, k: int = 1) -> List[Tuple[Any, float]]:
        """Find k nearest neighbors to a point."""
        start_time = datetime.now()
        results = []
        self._nearest_recursive(self.root, point, k, results)
        
        # Track performance
        self._search_times.append((datetime.now() - start_time).total_seconds())
        return sorted(results, key=lambda x: x[1])[:k]
    
    def _nearest_recursive(self, node: RTreeNode, point: Point, k: int, results: List[Tuple[Any, float]]):
        """Recursively find nearest neighbors."""
        if node.is_leaf:
            for bbox, value in node.entries:
                dist = bbox.distance_to_point(point)
                if len(results) < k or dist < results[-1][1]:
                    results.append((value, dist))
                    results.sort(key=lambda x: x[1])
                    if len(results) > k:
                        results.pop()
        else:
            # Sort children by distance to point
            children_dist = [(child, child.bbox.distance_to_point(point))
                           for child in node.children]
            children_dist.sort(key=lambda x: x[1])
            
            for child, dist in children_dist:
                if len(results) < k or dist < results[-1][1]:
                    self._nearest_recursive(child, point, k, results)
                    
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
        def get_depth(node: RTreeNode) -> int:
            if node.is_leaf:
                return 1
            return 1 + max(get_depth(child) for child in node.children)
            
        return get_depth(self.root)
    
    def _compute_size(self) -> int:
        """Estimate the memory size of the index."""
        def node_size(node: RTreeNode) -> int:
            size = 8  # Python object overhead
            size += 16  # bbox reference
            size += 24  # lists overhead
            size += len(node.children) * 8  # child references
            size += len(node.entries) * 16  # entry tuples
            return size
            
        def recursive_size(node: RTreeNode) -> int:
            size = node_size(node)
            if not node.is_leaf:
                size += sum(recursive_size(child) for child in node.children)
            return size
            
        return recursive_size(self.root)
    
    def cleanup(self):
        """Clean up resources."""
        self.root = None
        self._insert_times = []
        self._search_times = []
        self.size = 0 