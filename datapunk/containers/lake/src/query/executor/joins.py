from typing import Any, Dict, Iterator, List, Optional, Set
from .core import ExecutionOperator
from ..parser.core import QueryNode

class HashJoinOperator(ExecutionOperator):
    """Operator that implements hash join algorithm."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        left_iter = self.children[0].execute()
        right_iter = self.children[1].execute()
        join_condition = self.node.join_condition
        left_key = join_condition['left']
        right_key = join_condition['right']
        
        # Build hash table from smaller relation (right)
        hash_table: Dict[Any, List[Dict[str, Any]]] = {}
        for right_row in right_iter:
            key = right_row.get(right_key)
            if key is not None:
                if key not in hash_table:
                    hash_table[key] = []
                hash_table[key].append(right_row)
        
        # Probe phase
        for left_row in left_iter:
            key = left_row.get(left_key)
            if key is not None and key in hash_table:
                for right_row in hash_table[key]:
                    yield {**left_row, **right_row}

class MergeJoinOperator(ExecutionOperator):
    """Operator that implements merge join algorithm."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        left_iter = self.children[0].execute()
        right_iter = self.children[1].execute()
        join_condition = self.node.join_condition
        left_key = join_condition['left']
        right_key = join_condition['right']
        
        # Convert iterators to sorted lists
        left_rows = sorted(left_iter, key=lambda x: x.get(left_key))
        right_rows = sorted(right_iter, key=lambda x: x.get(right_key))
        
        left_idx = right_idx = 0
        
        while left_idx < len(left_rows) and right_idx < len(right_rows):
            left_val = left_rows[left_idx].get(left_key)
            right_val = right_rows[right_idx].get(right_key)
            
            if left_val == right_val:
                # Find all matching rows in both relations
                left_matches = [left_rows[left_idx]]
                right_matches = [right_rows[right_idx]]
                
                # Gather all equal values from left
                i = left_idx + 1
                while i < len(left_rows) and left_rows[i].get(left_key) == left_val:
                    left_matches.append(left_rows[i])
                    i += 1
                    
                # Gather all equal values from right
                j = right_idx + 1
                while j < len(right_rows) and right_rows[j].get(right_key) == right_val:
                    right_matches.append(right_rows[j])
                    j += 1
                    
                # Output cartesian product of matches
                for left_row in left_matches:
                    for right_row in right_matches:
                        yield {**left_row, **right_row}
                        
                left_idx = i
                right_idx = j
            elif left_val < right_val:
                left_idx += 1
            else:
                right_idx += 1

class IndexNestedLoopJoinOperator(ExecutionOperator):
    """Operator that implements index nested loop join algorithm."""
    
    def __init__(self, node: QueryNode, context: Any, index: Dict[Any, List[Dict[str, Any]]]):
        super().__init__(node, context)
        self.index = index
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        outer_iter = self.children[0].execute()
        join_condition = self.node.join_condition
        outer_key = join_condition['left']
        inner_key = join_condition['right']
        
        for outer_row in outer_iter:
            key = outer_row.get(outer_key)
            if key is not None and key in self.index:
                for inner_row in self.index[key]:
                    yield {**outer_row, **inner_row}

class PartitionedHashJoinOperator(ExecutionOperator):
    """Operator that implements partitioned hash join for large datasets."""
    
    def __init__(self, node: QueryNode, context: Any, num_partitions: int = 16):
        super().__init__(node, context)
        self.num_partitions = num_partitions
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        left_iter = self.children[0].execute()
        right_iter = self.children[1].execute()
        join_condition = self.node.join_condition
        left_key = join_condition['left']
        right_key = join_condition['right']
        
        # Create partitions
        left_partitions: List[List[Dict[str, Any]]] = [[] for _ in range(self.num_partitions)]
        right_partitions: List[List[Dict[str, Any]]] = [[] for _ in range(self.num_partitions)]
        
        # Partition phase
        for row in left_iter:
            key = row.get(left_key)
            if key is not None:
                partition = hash(key) % self.num_partitions
                left_partitions[partition].append(row)
                
        for row in right_iter:
            key = row.get(right_key)
            if key is not None:
                partition = hash(key) % self.num_partitions
                right_partitions[partition].append(row)
        
        # Join each partition pair
        for left_part, right_part in zip(left_partitions, right_partitions):
            # Build hash table for right partition
            hash_table: Dict[Any, List[Dict[str, Any]]] = {}
            for right_row in right_part:
                key = right_row.get(right_key)
                if key is not None:
                    if key not in hash_table:
                        hash_table[key] = []
                    hash_table[key].append(right_row)
            
            # Probe with left partition
            for left_row in left_part:
                key = left_row.get(left_key)
                if key is not None and key in hash_table:
                    for right_row in hash_table[key]:
                        yield {**left_row, **right_row}

def create_join_operator(node: QueryNode, context: Any, 
                        join_type: str = 'hash',
                        **kwargs) -> ExecutionOperator:
    """Factory function to create appropriate join operator."""
    if join_type == 'hash':
        return HashJoinOperator(node, context)
    elif join_type == 'merge':
        return MergeJoinOperator(node, context)
    elif join_type == 'index':
        if 'index' not in kwargs:
            raise ValueError("Index required for index nested loop join")
        return IndexNestedLoopJoinOperator(node, context, kwargs['index'])
    elif join_type == 'partitioned_hash':
        num_partitions = kwargs.get('num_partitions', 16)
        return PartitionedHashJoinOperator(node, context, num_partitions)
    else:
        raise ValueError(f"Unsupported join type: {join_type}") 