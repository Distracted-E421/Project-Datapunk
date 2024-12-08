from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional
from ..parser.query_parser_core import QueryPlan, QueryNode
from ...storage.cache import CacheManager

class ExecutionContext:
    """Holds the context for query execution including variables and statistics."""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.statistics: Dict[str, Any] = {}
        self.cache_manager: Optional[CacheManager] = None
        
    def set_variable(self, name: str, value: Any) -> None:
        """Set a context variable."""
        self.variables[name] = value
        
    def get_variable(self, name: str) -> Optional[Any]:
        """Get a context variable."""
        return self.variables.get(name)
        
    def update_statistics(self, key: str, value: Any) -> None:
        """Update execution statistics."""
        self.statistics[key] = value

class ExecutionOperator(ABC):
    """Base class for all execution operators."""
    
    def __init__(self, node: QueryNode, context: ExecutionContext):
        self.node = node
        self.context = context
        self.children: List['ExecutionOperator'] = []
        
    @abstractmethod
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute this operator and yield result rows."""
        pass
        
    def add_child(self, child: 'ExecutionOperator') -> None:
        """Add a child operator."""
        self.children.append(child)

class TableScanOperator(ExecutionOperator):
    """Operator for scanning table data."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        table_name = self.node.table_name
        columns = self.node.columns
        
        # Use cache if available
        if self.context.cache_manager:
            cached_data = self.context.cache_manager.get(table_name)
            if cached_data is not None:
                for row in cached_data:
                    yield {col: row[col] for col in columns if col in row}
                return
                
        # Fallback to direct table scan
        # This should be implemented based on your storage engine
        raise NotImplementedError("Direct table scan not implemented")

class FilterOperator(ExecutionOperator):
    """Operator for filtering rows based on predicates."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        child_iter = self.children[0].execute()
        predicate = self.node.predicate
        
        for row in child_iter:
            if self._evaluate_predicate(predicate, row):
                yield row
                
    def _evaluate_predicate(self, predicate: Dict[str, Any], row: Dict[str, Any]) -> bool:
        column = predicate['column']
        operator = predicate['op']
        value = predicate['value']
        
        if column not in row:
            return False
            
        row_value = row[column]
        
        if operator == '=':
            return row_value == value
        elif operator == '>':
            return row_value > value
        elif operator == '<':
            return row_value < value
        elif operator == '>=':
            return row_value >= value
        elif operator == '<=':
            return row_value <= value
        elif operator == '!=':
            return row_value != value
        else:
            raise ValueError(f"Unsupported operator: {operator}")

class JoinOperator(ExecutionOperator):
    """Operator for joining two result sets."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        left_iter = self.children[0].execute()
        right_iter = self.children[1].execute()
        join_condition = self.node.join_condition
        
        # Buffer right side for nested loop join
        right_rows = list(right_iter)
        
        for left_row in left_iter:
            for right_row in right_rows:
                if self._evaluate_join_condition(join_condition, left_row, right_row):
                    # Merge the matching rows
                    yield {**left_row, **right_row}
                    
    def _evaluate_join_condition(self, condition: Dict[str, str], 
                               left_row: Dict[str, Any],
                               right_row: Dict[str, Any]) -> bool:
        left_key = condition['left']
        right_key = condition['right']
        
        return left_row.get(left_key) == right_row.get(right_key)

class ProjectOperator(ExecutionOperator):
    """Operator for projecting specific columns."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        child_iter = self.children[0].execute()
        columns = self.node.columns
        
        for row in child_iter:
            yield {col: row[col] for col in columns if col in row}

class AggregateOperator(ExecutionOperator):
    """Operator for performing aggregations."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        child_iter = self.children[0].execute()
        group_by = self.node.group_by or []
        aggregates = self.node.aggregates or []
        
        groups: Dict[tuple, Dict[str, Any]] = {}
        
        # Process each input row
        for row in child_iter:
            group_key = tuple(row[col] for col in group_by)
            
            if group_key not in groups:
                groups[group_key] = {
                    col: row[col] for col in group_by
                }
                for agg in aggregates:
                    groups[group_key][agg['alias']] = self._init_aggregate(agg)
                    
            # Update aggregates for this group
            for agg in aggregates:
                self._update_aggregate(groups[group_key][agg['alias']], 
                                    agg, row)
                
        # Finalize and yield results
        for group in groups.values():
            for agg in aggregates:
                group[agg['alias']] = self._finalize_aggregate(
                    group[agg['alias']], agg)
            yield group
            
    def _init_aggregate(self, agg: Dict[str, Any]) -> Any:
        """Initialize an aggregate value."""
        func = agg['function']
        if func in ('sum', 'avg'):
            return 0
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
            current += value
        elif func == 'count':
            current += 1
        elif func == 'min':
            if current is None or value < current:
                current = value
        elif func == 'max':
            if current is None or value > current:
                current = value
                
    def _finalize_aggregate(self, value: Any, agg: Dict[str, Any]) -> Any:
        """Finalize an aggregate value."""
        func = agg['function']
        if func == 'avg':
            count = agg.get('count', 1)
            return value / count if count > 0 else None
        return value

class ExecutionEngine:
    """Main execution engine that orchestrates query execution."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager
        
    def execute_plan(self, plan: QueryPlan) -> Iterator[Dict[str, Any]]:
        """Execute a query plan and return results."""
        context = ExecutionContext()
        if self.cache_manager:
            context.cache_manager = self.cache_manager
            
        # Build execution tree
        root_operator = self._build_execution_tree(plan.root, context)
        
        # Execute and return results
        yield from root_operator.execute()
        
    def _build_execution_tree(self, node: QueryNode, 
                            context: ExecutionContext) -> ExecutionOperator:
        """Recursively build the execution operator tree."""
        operator: ExecutionOperator
        
        if node.operation == 'table_scan':
            operator = TableScanOperator(node, context)
        elif node.operation == 'filter':
            operator = FilterOperator(node, context)
        elif node.operation == 'join':
            operator = JoinOperator(node, context)
        elif node.operation == 'project':
            operator = ProjectOperator(node, context)
        elif node.operation == 'aggregate':
            operator = AggregateOperator(node, context)
        else:
            raise ValueError(f"Unsupported operation: {node.operation}")
            
        # Recursively build children
        for child in node.children:
            child_operator = self._build_execution_tree(child, context)
            operator.add_child(child_operator)
            
        return operator 