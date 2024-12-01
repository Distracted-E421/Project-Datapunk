from typing import Any, Dict, Iterator, List, Optional, Tuple
from abc import ABC, abstractmethod
from .core import ExecutionOperator
from ..parser.core import QueryNode

class WindowFunction(ABC):
    """Base class for window functions."""
    
    @abstractmethod
    def process_partition(self, partition: List[Dict[str, Any]], 
                         order_by: Optional[List[str]] = None) -> List[Any]:
        """Process a partition of rows and return window function results."""
        pass

class RankFunction(WindowFunction):
    """Implements RANK() window function."""
    
    def process_partition(self, partition: List[Dict[str, Any]], 
                         order_by: Optional[List[str]] = None) -> List[int]:
        if not order_by:
            return [1] * len(partition)
            
        # Sort partition by order by columns
        sorted_partition = sorted(
            enumerate(partition),
            key=lambda x: tuple(x[1][col] for col in order_by)
        )
        
        ranks = [0] * len(partition)
        current_rank = 1
        current_values = None
        
        for i, (orig_idx, row) in enumerate(sorted_partition):
            values = tuple(row[col] for col in order_by)
            if values != current_values:
                current_rank = i + 1
                current_values = values
            ranks[orig_idx] = current_rank
            
        return ranks

class DenseRankFunction(WindowFunction):
    """Implements DENSE_RANK() window function."""
    
    def process_partition(self, partition: List[Dict[str, Any]], 
                         order_by: Optional[List[str]] = None) -> List[int]:
        if not order_by:
            return [1] * len(partition)
            
        sorted_partition = sorted(
            enumerate(partition),
            key=lambda x: tuple(x[1][col] for col in order_by)
        )
        
        ranks = [0] * len(partition)
        current_rank = 1
        current_values = None
        
        for orig_idx, row in sorted_partition:
            values = tuple(row[col] for col in order_by)
            if values != current_values:
                current_values = values
                current_rank += 1
            ranks[orig_idx] = current_rank
            
        return ranks

class RowNumberFunction(WindowFunction):
    """Implements ROW_NUMBER() window function."""
    
    def process_partition(self, partition: List[Dict[str, Any]], 
                         order_by: Optional[List[str]] = None) -> List[int]:
        if not order_by:
            return list(range(1, len(partition) + 1))
            
        sorted_indices = sorted(
            range(len(partition)),
            key=lambda i: tuple(partition[i][col] for col in order_by)
        )
        
        row_numbers = [0] * len(partition)
        for new_idx, orig_idx in enumerate(sorted_indices, 1):
            row_numbers[orig_idx] = new_idx
            
        return row_numbers

class LeadLagFunction(WindowFunction):
    """Implements LEAD() and LAG() window functions."""
    
    def __init__(self, offset: int = 1, is_lead: bool = True, 
                 default_value: Any = None):
        self.offset = offset
        self.is_lead = is_lead
        self.default_value = default_value
    
    def process_partition(self, partition: List[Dict[str, Any]], 
                         order_by: Optional[List[str]] = None) -> List[Any]:
        if not order_by:
            return [self.default_value] * len(partition)
            
        sorted_indices = sorted(
            range(len(partition)),
            key=lambda i: tuple(partition[i][col] for col in order_by)
        )
        
        results = [self.default_value] * len(partition)
        
        for i, orig_idx in enumerate(sorted_indices):
            if self.is_lead:
                offset_idx = i + self.offset
            else:
                offset_idx = i - self.offset
                
            if 0 <= offset_idx < len(sorted_indices):
                results[orig_idx] = partition[sorted_indices[offset_idx]]
                
        return results

class FirstLastFunction(WindowFunction):
    """Implements FIRST_VALUE() and LAST_VALUE() window functions."""
    
    def __init__(self, is_first: bool = True):
        self.is_first = is_first
    
    def process_partition(self, partition: List[Dict[str, Any]], 
                         order_by: Optional[List[str]] = None) -> List[Any]:
        if not partition:
            return []
            
        if not order_by:
            value = partition[0] if self.is_first else partition[-1]
            return [value] * len(partition)
            
        sorted_partition = sorted(
            partition,
            key=lambda x: tuple(x[col] for col in order_by)
        )
        
        value = sorted_partition[0] if self.is_first else sorted_partition[-1]
        return [value] * len(partition)

class NtileFunction(WindowFunction):
    """Implements NTILE() window function."""
    
    def __init__(self, num_buckets: int):
        self.num_buckets = max(1, num_buckets)
    
    def process_partition(self, partition: List[Dict[str, Any]], 
                         order_by: Optional[List[str]] = None) -> List[int]:
        if not partition:
            return []
            
        n = len(partition)
        base_size = n // self.num_buckets
        remainder = n % self.num_buckets
        
        results = [0] * n
        current_bucket = 1
        used_rows = 0
        
        sorted_indices = (
            sorted(range(n), key=lambda i: tuple(partition[i][col] for col in order_by))
            if order_by else range(n)
        )
        
        for i in sorted_indices:
            bucket_size = base_size + (1 if current_bucket <= remainder else 0)
            results[i] = current_bucket
            used_rows += 1
            
            if used_rows == bucket_size:
                current_bucket += 1
                used_rows = 0
                
        return results

class WindowOperator(ExecutionOperator):
    """Operator that implements window functions."""
    
    def __init__(self, node: QueryNode, context: Any):
        super().__init__(node, context)
        self.functions: Dict[str, WindowFunction] = {
            'rank': RankFunction(),
            'dense_rank': DenseRankFunction(),
            'row_number': RowNumberFunction(),
            'lead': lambda offset=1, default=None: LeadLagFunction(offset, True, default),
            'lag': lambda offset=1, default=None: LeadLagFunction(offset, False, default),
            'first_value': lambda: FirstLastFunction(True),
            'last_value': lambda: FirstLastFunction(False),
            'ntile': lambda n: NtileFunction(n)
        }
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        child_iter = self.children[0].execute()
        partition_by = self.node.partition_by or []
        order_by = self.node.order_by
        window_funcs = self.node.window_functions
        
        # Collect all rows and organize by partition
        partitions: Dict[Tuple, List[Dict[str, Any]]] = {}
        all_rows = []
        
        for row in child_iter:
            all_rows.append(row)
            partition_key = tuple(row[col] for col in partition_by)
            if partition_key not in partitions:
                partitions[partition_key] = []
            partitions[partition_key].append(row)
            
        # Process each window function
        for func_spec in window_funcs:
            func_name = func_spec['function']
            alias = func_spec['alias']
            params = func_spec.get('params', {})
            
            if func_name not in self.functions:
                raise ValueError(f"Unsupported window function: {func_name}")
                
            # Create function instance
            if callable(self.functions[func_name]):
                window_func = self.functions[func_name](**params)
            else:
                window_func = self.functions[func_name]
                
            # Process each partition
            for partition in partitions.values():
                results = window_func.process_partition(partition, order_by)
                
                # Assign results back to rows
                for row, result in zip(partition, results):
                    row[alias] = result
                    
        # Yield rows in original order
        yield from all_rows 