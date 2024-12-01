from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import math
import statistics
from .core import ExecutionOperator
from ..parser.core import QueryNode

class AggregateFunction(ABC):
    """Base class for aggregate functions."""
    
    @abstractmethod
    def init(self) -> Any:
        """Initialize the aggregate value."""
        pass
        
    @abstractmethod
    def update(self, current: Any, value: Any) -> Any:
        """Update the aggregate with a new value."""
        pass
        
    @abstractmethod
    def finalize(self, value: Any) -> Any:
        """Finalize the aggregate value."""
        pass

class Sum(AggregateFunction):
    def init(self) -> float:
        return 0.0
        
    def update(self, current: float, value: Any) -> float:
        if value is not None:
            return current + float(value)
        return current
        
    def finalize(self, value: float) -> float:
        return value

class Average(AggregateFunction):
    def init(self) -> Dict[str, float]:
        return {'sum': 0.0, 'count': 0}
        
    def update(self, current: Dict[str, float], value: Any) -> Dict[str, float]:
        if value is not None:
            current['sum'] += float(value)
            current['count'] += 1
        return current
        
    def finalize(self, value: Dict[str, float]) -> Optional[float]:
        if value['count'] == 0:
            return None
        return value['sum'] / value['count']

class StandardDeviation(AggregateFunction):
    def init(self) -> List[float]:
        return []
        
    def update(self, current: List[float], value: Any) -> List[float]:
        if value is not None:
            current.append(float(value))
        return current
        
    def finalize(self, value: List[float]) -> Optional[float]:
        if not value:
            return None
        return statistics.stdev(value) if len(value) > 1 else 0.0

class Variance(AggregateFunction):
    def init(self) -> List[float]:
        return []
        
    def update(self, current: List[float], value: Any) -> List[float]:
        if value is not None:
            current.append(float(value))
        return current
        
    def finalize(self, value: List[float]) -> Optional[float]:
        if not value:
            return None
        return statistics.variance(value) if len(value) > 1 else 0.0

class Median(AggregateFunction):
    def init(self) -> List[float]:
        return []
        
    def update(self, current: List[float], value: Any) -> List[float]:
        if value is not None:
            current.append(float(value))
        return current
        
    def finalize(self, value: List[float]) -> Optional[float]:
        if not value:
            return None
        return statistics.median(value)

class Mode(AggregateFunction):
    def init(self) -> List[Any]:
        return []
        
    def update(self, current: List[Any], value: Any) -> List[Any]:
        if value is not None:
            current.append(value)
        return current
        
    def finalize(self, value: List[Any]) -> Optional[Any]:
        if not value:
            return None
        return statistics.mode(value)

class Percentile(AggregateFunction):
    def __init__(self, percentile: float):
        self.percentile = percentile
        
    def init(self) -> List[float]:
        return []
        
    def update(self, current: List[float], value: Any) -> List[float]:
        if value is not None:
            current.append(float(value))
        return current
        
    def finalize(self, value: List[float]) -> Optional[float]:
        if not value:
            return None
        return statistics.quantiles(value, n=100)[int(self.percentile) - 1]

class MovingAverage(AggregateFunction):
    def __init__(self, window_size: int):
        self.window_size = window_size
        
    def init(self) -> List[float]:
        return []
        
    def update(self, current: List[float], value: Any) -> List[float]:
        if value is not None:
            current.append(float(value))
            if len(current) > self.window_size:
                current.pop(0)
        return current
        
    def finalize(self, value: List[float]) -> Optional[float]:
        if not value:
            return None
        return sum(value) / len(value)

class Correlation(AggregateFunction):
    def init(self) -> Dict[str, List[float]]:
        return {'x': [], 'y': []}
        
    def update(self, current: Dict[str, List[float]], 
               value: Dict[str, Any]) -> Dict[str, List[float]]:
        if 'x' in value and 'y' in value and value['x'] is not None and value['y'] is not None:
            current['x'].append(float(value['x']))
            current['y'].append(float(value['y']))
        return current
        
    def finalize(self, value: Dict[str, List[float]]) -> Optional[float]:
        if len(value['x']) < 2:
            return None
        return statistics.correlation(value['x'], value['y'])

class EnhancedAggregateOperator(ExecutionOperator):
    """Enhanced operator for performing advanced aggregations."""
    
    def __init__(self, node: QueryNode, context: Any):
        super().__init__(node, context)
        self.functions: Dict[str, AggregateFunction] = {
            'sum': Sum(),
            'avg': Average(),
            'stddev': StandardDeviation(),
            'variance': Variance(),
            'median': Median(),
            'mode': Mode(),
            'percentile': lambda p: Percentile(p),
            'moving_avg': lambda w: MovingAverage(w),
            'correlation': Correlation()
        }
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        child_iter = self.children[0].execute()
        group_by = self.node.group_by or []
        aggregates = self.node.aggregates or []
        
        groups: Dict[tuple, Dict[str, Any]] = {}
        
        # Initialize aggregate functions
        agg_functions = {}
        for agg in aggregates:
            func_name = agg['function']
            if func_name in self.functions:
                if callable(self.functions[func_name]):
                    # Handle parameterized functions
                    params = agg.get('params', {})
                    agg_functions[agg['alias']] = self.functions[func_name](**params)
                else:
                    agg_functions[agg['alias']] = self.functions[func_name]
            else:
                raise ValueError(f"Unsupported aggregate function: {func_name}")
        
        # Process rows
        for row in child_iter:
            group_key = tuple(row[col] for col in group_by)
            
            if group_key not in groups:
                groups[group_key] = {
                    col: row[col] for col in group_by
                }
                for alias, func in agg_functions.items():
                    groups[group_key][alias] = func.init()
            
            # Update aggregates
            for agg in aggregates:
                alias = agg['alias']
                if agg['function'] == 'correlation':
                    # Special handling for correlation
                    value = {
                        'x': row.get(agg['columns'][0]),
                        'y': row.get(agg['columns'][1])
                    }
                else:
                    value = row.get(agg['column'])
                groups[group_key][alias] = agg_functions[alias].update(
                    groups[group_key][alias], value)
        
        # Finalize results
        for group in groups.values():
            for alias, func in agg_functions.items():
                group[alias] = func.finalize(group[alias])
            yield group 