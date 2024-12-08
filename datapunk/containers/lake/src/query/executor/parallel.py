from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
from queue import Queue
from threading import Lock
from .query_exec_core import ExecutionOperator, ExecutionContext
from ..parser.query_parser_core import QueryNode

class ParallelContext(ExecutionContext):
    """Extended context for parallel execution."""
    
    def __init__(self, max_workers: Optional[int] = None):
        super().__init__()
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
        self.shared_queue = Queue()
        self.lock = Lock()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

class ParallelOperator(ExecutionOperator):
    """Base class for parallel execution operators."""
    
    def __init__(self, node: QueryNode, context: ParallelContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        
    def partition_data(self, data: Iterator[Dict[str, Any]], 
                      num_partitions: int) -> List[List[Dict[str, Any]]]:
        """Partition data into roughly equal chunks."""
        partitions = [[] for _ in range(num_partitions)]
        for i, item in enumerate(data):
            partitions[i % num_partitions].append(item)
        return partitions

class ParallelTableScan(ParallelOperator):
    """Parallel implementation of table scan."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        table_name = self.node.table_name
        columns = self.node.columns
        
        if self.context.cache_manager:
            cached_data = self.context.cache_manager.get(table_name)
            if cached_data is not None:
                # Partition cached data
                partitions = self.partition_data(
                    iter(cached_data), 
                    self.context.max_workers
                )
                
                # Process partitions in parallel
                futures = []
                for partition in partitions:
                    future = self.context.thread_pool.submit(
                        self._process_partition, partition, columns
                    )
                    futures.append(future)
                    
                # Collect results
                for future in futures:
                    yield from future.result()
                    
    def _process_partition(self, partition: List[Dict[str, Any]], 
                         columns: List[str]) -> List[Dict[str, Any]]:
        """Process a partition of the table data."""
        return [{col: row[col] for col in columns if col in row}
                for row in partition]

class ParallelHashJoin(ParallelOperator):
    """Parallel implementation of hash join."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        left_iter = self.children[0].execute()
        right_iter = self.children[1].execute()
        join_condition = self.node.join_condition
        left_key = join_condition['left']
        right_key = join_condition['right']
        
        # Build phase - partition right relation
        right_partitions = self.partition_data(
            right_iter,
            self.context.max_workers
        )
        
        # Build hash tables in parallel
        hash_table_futures = []
        for partition in right_partitions:
            future = self.context.thread_pool.submit(
                self._build_hash_table, partition, right_key
            )
            hash_table_futures.append(future)
            
        # Collect hash tables
        hash_tables = [future.result() for future in hash_table_futures]
        
        # Probe phase - partition left relation
        left_partitions = self.partition_data(
            left_iter,
            self.context.max_workers
        )
        
        # Process probes in parallel
        probe_futures = []
        for left_part in left_partitions:
            future = self.context.thread_pool.submit(
                self._probe_partition,
                left_part,
                hash_tables,
                left_key
            )
            probe_futures.append(future)
            
        # Collect and yield results
        for future in probe_futures:
            yield from future.result()
            
    def _build_hash_table(self, partition: List[Dict[str, Any]], 
                         key: str) -> Dict[Any, List[Dict[str, Any]]]:
        """Build hash table for a partition."""
        hash_table: Dict[Any, List[Dict[str, Any]]] = {}
        for row in partition:
            k = row.get(key)
            if k is not None:
                if k not in hash_table:
                    hash_table[k] = []
                hash_table[k].append(row)
        return hash_table
        
    def _probe_partition(self, partition: List[Dict[str, Any]],
                        hash_tables: List[Dict[Any, List[Dict[str, Any]]]],
                        key: str) -> List[Dict[str, Any]]:
        """Probe hash tables with a partition of rows."""
        results = []
        for row in partition:
            k = row.get(key)
            if k is not None:
                for hash_table in hash_tables:
                    if k in hash_table:
                        for matching_row in hash_table[k]:
                            results.append({**row, **matching_row})
        return results

class ParallelAggregation(ParallelOperator):
    """Parallel implementation of aggregation."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        child_iter = self.children[0].execute()
        group_by = self.node.group_by or []
        aggregates = self.node.aggregates or []
        
        # Partition data
        partitions = self.partition_data(
            child_iter,
            self.context.max_workers
        )
        
        # Process partitions in parallel
        futures = []
        for partition in partitions:
            future = self.context.process_pool.submit(
                self._process_partition,
                partition,
                group_by,
                aggregates
            )
            futures.append(future)
            
        # Merge partial results
        partial_results = [future.result() for future in futures]
        final_results = self._merge_results(partial_results, group_by, aggregates)
        
        yield from final_results
        
    def _process_partition(self, partition: List[Dict[str, Any]],
                         group_by: List[str],
                         aggregates: List[Dict[str, Any]]) -> Dict[Tuple, Dict[str, Any]]:
        """Process a partition and compute partial aggregates."""
        groups: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in partition:
            group_key = tuple(row[col] for col in group_by)
            
            if group_key not in groups:
                groups[group_key] = {
                    col: row[col] for col in group_by
                }
                for agg in aggregates:
                    groups[group_key][agg['alias']] = self._init_aggregate(agg)
                    
            for agg in aggregates:
                self._update_aggregate(
                    groups[group_key][agg['alias']],
                    agg,
                    row
                )
                
        return groups
        
    def _merge_results(self, partial_results: List[Dict[Tuple, Dict[str, Any]]],
                      group_by: List[str],
                      aggregates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge partial results from different partitions."""
        merged: Dict[Tuple, Dict[str, Any]] = {}
        
        # Merge all partial results
        for partial in partial_results:
            for group_key, group_data in partial.items():
                if group_key not in merged:
                    merged[group_key] = {
                        col: group_data[col] for col in group_by
                    }
                    for agg in aggregates:
                        merged[group_key][agg['alias']] = group_data[agg['alias']]
                else:
                    for agg in aggregates:
                        merged[group_key][agg['alias']] = self._merge_aggregate(
                            merged[group_key][agg['alias']],
                            group_data[agg['alias']],
                            agg
                        )
                        
        # Finalize aggregates
        for group_data in merged.values():
            for agg in aggregates:
                group_data[agg['alias']] = self._finalize_aggregate(
                    group_data[agg['alias']],
                    agg
                )
                
        return list(merged.values())
        
    def _init_aggregate(self, agg: Dict[str, Any]) -> Any:
        """Initialize an aggregate value."""
        func = agg['function']
        if func in ('sum', 'avg'):
            return {'sum': 0, 'count': 0}
        elif func == 'count':
            return 0
        elif func in ('min', 'max'):
            return None
        raise ValueError(f"Unsupported aggregate function: {func}")
        
    def _update_aggregate(self, current: Any, agg: Dict[str, Any],
                         row: Dict[str, Any]) -> None:
        """Update an aggregate value with a new row."""
        func = agg['function']
        col = agg['column']
        value = row.get(col)
        
        if value is None:
            return
            
        if func in ('sum', 'avg'):
            current['sum'] += value
            current['count'] += 1
        elif func == 'count':
            current += 1
        elif func == 'min':
            if current is None or value < current:
                current = value
        elif func == 'max':
            if current is None or value > current:
                current = value
                
    def _merge_aggregate(self, agg1: Any, agg2: Any,
                        agg: Dict[str, Any]) -> Any:
        """Merge two aggregate values."""
        func = agg['function']
        
        if func in ('sum', 'avg'):
            return {
                'sum': agg1['sum'] + agg2['sum'],
                'count': agg1['count'] + agg2['count']
            }
        elif func == 'count':
            return agg1 + agg2
        elif func == 'min':
            if agg1 is None:
                return agg2
            if agg2 is None:
                return agg1
            return min(agg1, agg2)
        elif func == 'max':
            if agg1 is None:
                return agg2
            if agg2 is None:
                return agg1
            return max(agg1, agg2)
            
    def _finalize_aggregate(self, value: Any, agg: Dict[str, Any]) -> Any:
        """Finalize an aggregate value."""
        func = agg['function']
        if func == 'avg':
            return value['sum'] / value['count'] if value['count'] > 0 else None
        elif func in ('sum', 'count', 'min', 'max'):
            return value
        raise ValueError(f"Unsupported aggregate function: {func}")

def create_parallel_operator(node: QueryNode, 
                           context: ParallelContext) -> ExecutionOperator:
    """Factory function to create appropriate parallel operator."""
    if node.operation == 'table_scan':
        return ParallelTableScan(node, context)
    elif node.operation == 'join':
        return ParallelHashJoin(node, context)
    elif node.operation == 'aggregate':
        return ParallelAggregation(node, context)
    else:
        # Fall back to non-parallel operator for other operations
        return ExecutionOperator(node, context) 