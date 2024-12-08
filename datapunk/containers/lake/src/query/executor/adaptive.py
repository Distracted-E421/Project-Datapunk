from typing import Any, Dict, Iterator, List, Optional, Tuple
from abc import ABC, abstractmethod
import time
from .query_exec_core import ExecutionOperator, ExecutionContext
from .joins import HashJoinOperator, MergeJoinOperator
from ..parser.query_parser_core import QueryNode, QueryPlan

class Statistics:
    """Maintains runtime statistics for adaptive execution."""
    
    def __init__(self):
        self.row_counts: Dict[str, int] = {}
        self.execution_times: Dict[str, float] = {}
        self.memory_usage: Dict[str, int] = {}
        self.cardinality_estimates: Dict[str, int] = {}
        
    def update_row_count(self, operator_id: str, count: int) -> None:
        """Update row count for an operator."""
        self.row_counts[operator_id] = count
        
    def update_execution_time(self, operator_id: str, time: float) -> None:
        """Update execution time for an operator."""
        self.execution_times[operator_id] = time
        
    def update_memory_usage(self, operator_id: str, memory: int) -> None:
        """Update memory usage for an operator."""
        self.memory_usage[operator_id] = memory
        
    def update_cardinality(self, operator_id: str, estimate: int) -> None:
        """Update cardinality estimate for an operator."""
        self.cardinality_estimates[operator_id] = estimate

class AdaptiveContext(ExecutionContext):
    """Extended context with adaptive execution support."""
    
    def __init__(self):
        super().__init__()
        self.statistics = Statistics()
        self.adaptation_threshold = 0.5  # Threshold for plan changes
        self.sample_size = 1000  # Size for sampling data
        
    def should_adapt(self, operator_id: str, actual: int, 
                    estimated: int) -> bool:
        """Determine if adaptation is needed based on statistics."""
        if estimated == 0:
            return True
        error = abs(actual - estimated) / estimated
        return error > self.adaptation_threshold

class AdaptiveOperator(ExecutionOperator):
    """Base class for adaptive operators."""
    
    def __init__(self, node: QueryNode, context: AdaptiveContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        self.operator_id = str(id(self))
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with runtime adaptation."""
        start_time = time.time()
        
        # Sample data for statistics
        sample_iter = self._sample_data()
        sample_stats = self._analyze_sample(sample_iter)
        
        # Choose execution strategy
        strategy = self._choose_strategy(sample_stats)
        
        # Execute with chosen strategy
        result_iter = strategy.execute()
        
        # Wrap iterator to collect statistics
        for i, row in enumerate(result_iter, 1):
            if i % 1000 == 0:  # Update stats periodically
                self.context.statistics.update_row_count(self.operator_id, i)
                current_time = time.time() - start_time
                self.context.statistics.update_execution_time(
                    self.operator_id, current_time)
                
                # Check if adaptation is needed
                if self._should_adapt(i, sample_stats):
                    # Re-choose strategy based on actual statistics
                    new_strategy = self._choose_strategy({
                        'row_count': i,
                        'execution_time': current_time
                    })
                    if new_strategy != strategy:
                        strategy = new_strategy
                        result_iter = strategy.execute()
            
            yield row
            
        # Final statistics update
        end_time = time.time()
        self.context.statistics.update_execution_time(
            self.operator_id, end_time - start_time)
            
    def _sample_data(self) -> Iterator[Dict[str, Any]]:
        """Sample input data for statistics."""
        sample = []
        for i, row in enumerate(super().execute()):
            if i < self.context.sample_size:
                sample.append(row)
            else:
                break
        return iter(sample)
        
    def _analyze_sample(self, sample_iter: Iterator[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sample data for statistics."""
        stats = {'row_count': 0, 'distinct_values': set()}
        
        for row in sample_iter:
            stats['row_count'] += 1
            for key in row:
                if key not in stats['distinct_values']:
                    stats['distinct_values'].add(key)
                    
        return stats
        
    @abstractmethod
    def _choose_strategy(self, stats: Dict[str, Any]) -> ExecutionOperator:
        """Choose execution strategy based on statistics."""
        pass
        
    def _should_adapt(self, current_count: int, 
                     sample_stats: Dict[str, Any]) -> bool:
        """Determine if adaptation is needed."""
        estimated = sample_stats['row_count'] * \
                   (current_count / self.context.sample_size)
        return self.context.should_adapt(
            self.operator_id, current_count, int(estimated))

class AdaptiveJoin(AdaptiveOperator):
    """Adaptive join operator that switches strategies based on data."""
    
    def _choose_strategy(self, stats: Dict[str, Any]) -> ExecutionOperator:
        """Choose join strategy based on statistics."""
        row_count = stats['row_count']
        
        if row_count < 1000:
            # For small datasets, use hash join
            return HashJoinOperator(self.node, self.context)
        else:
            # For large datasets, use merge join
            return MergeJoinOperator(self.node, self.context)

class AdaptiveAggregation(AdaptiveOperator):
    """Adaptive aggregation operator."""
    
    def _choose_strategy(self, stats: Dict[str, Any]) -> ExecutionOperator:
        """Choose aggregation strategy based on statistics."""
        from .aggregates import EnhancedAggregateOperator
        from .parallel import ParallelAggregation
        
        row_count = stats['row_count']
        distinct_values = len(stats['distinct_values'])
        
        if row_count > 10000 and distinct_values < row_count / 10:
            # Many rows, few distinct values: use parallel
            return ParallelAggregation(self.node, self.context)
        else:
            # Few rows or many distinct values: use standard
            return EnhancedAggregateOperator(self.node, self.context)

class AdaptiveExecutionEngine:
    """Execution engine with adaptive query processing."""
    
    def __init__(self):
        self.context = AdaptiveContext()
        
    def execute_plan(self, plan: QueryPlan) -> Iterator[Dict[str, Any]]:
        """Execute a query plan with runtime adaptation."""
        # Build initial execution tree
        root_operator = self._build_adaptive_tree(plan.root)
        
        # Execute and collect results
        yield from root_operator.execute()
        
        # Log execution statistics
        self._log_statistics()
        
    def _build_adaptive_tree(self, node: QueryNode) -> ExecutionOperator:
        """Build an adaptive execution tree."""
        if node.operation == 'join':
            operator = AdaptiveJoin(node, self.context)
        elif node.operation == 'aggregate':
            operator = AdaptiveAggregation(node, self.context)
        else:
            operator = ExecutionOperator(node, self.context)
            
        # Recursively build children
        for child in node.children:
            child_operator = self._build_adaptive_tree(child)
            operator.add_child(child_operator)
            
        return operator
        
    def _log_statistics(self) -> None:
        """Log execution statistics for analysis."""
        stats = self.context.statistics
        print("Execution Statistics:")
        print(f"Row counts: {stats.row_counts}")
        print(f"Execution times: {stats.execution_times}")
        print(f"Memory usage: {stats.memory_usage}")
        print(f"Cardinality estimates: {stats.cardinality_estimates}") 