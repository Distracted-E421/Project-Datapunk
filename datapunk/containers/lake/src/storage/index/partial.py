from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic, Union
from dataclasses import dataclass
from datetime import datetime
import operator
from enum import Enum
from abc import ABC, abstractmethod

from .core import Index, IndexType, IndexStats

K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type

class Operator(Enum):
    """Supported operators for partial index conditions."""
    EQ = "="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"

class BaseCondition(ABC):
    """Abstract base class for all conditions."""
    @abstractmethod
    def evaluate(self, row: Dict[str, Any]) -> bool:
        """Evaluate the condition against a row."""
        pass

    @abstractmethod
    def to_string(self) -> str:
        """Convert condition to string representation."""
        pass

@dataclass
class SimpleCondition(BaseCondition):
    """Represents a simple column condition."""
    column: str
    operator: Operator
    value: Any

    def evaluate(self, row: Dict[str, Any]) -> bool:
        if self.column not in row:
            return False
            
        column_value = row[self.column]
        
        if self.operator == Operator.IS_NULL:
            return column_value is None
        if self.operator == Operator.IS_NOT_NULL:
            return column_value is not None
            
        if column_value is None:
            return False
            
        op_map = {
            Operator.EQ: operator.eq,
            Operator.NE: operator.ne,
            Operator.LT: operator.lt,
            Operator.LE: operator.le,
            Operator.GT: operator.gt,
            Operator.GE: operator.ge,
            Operator.IN: lambda x, y: x in y,
            Operator.NOT_IN: lambda x, y: x not in y,
            Operator.LIKE: self._like_match,
            Operator.NOT_LIKE: lambda x, y: not self._like_match(x, y),
            Operator.BETWEEN: lambda x, y: y[0] <= x <= y[1]
        }
        
        try:
            return op_map[self.operator](column_value, self.value)
        except (TypeError, ValueError):
            return False

    def _like_match(self, value: str, pattern: str) -> bool:
        if not isinstance(value, str) or not isinstance(pattern, str):
            return False
            
        import re
        regex_pattern = (
            pattern
            .replace("%", ".*")
            .replace("_", ".")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )
        return bool(re.match(f"^{regex_pattern}$", value))

    def to_string(self) -> str:
        if self.operator in (Operator.IS_NULL, Operator.IS_NOT_NULL):
            return f"{self.column} {self.operator.value}"
        return f"{self.column} {self.operator.value} {self.value}"

class CompositeCondition(BaseCondition):
    """Represents a composite condition using AND/OR logic."""
    def __init__(self, operator: str, conditions: List[BaseCondition]):
        if operator not in ("AND", "OR"):
            raise ValueError("Operator must be 'AND' or 'OR'")
        self.operator = operator
        self.conditions = conditions

    def evaluate(self, row: Dict[str, Any]) -> bool:
        if self.operator == "AND":
            return all(cond.evaluate(row) for cond in self.conditions)
        return any(cond.evaluate(row) for cond in self.conditions)

    def to_string(self) -> str:
        conditions_str = [f"({cond.to_string()})" for cond in self.conditions]
        return f" {self.operator} ".join(conditions_str)

class ExpressionCondition(BaseCondition):
    """Represents a condition based on a Python expression."""
    def __init__(self, expression: str, columns: List[str]):
        self.expression = expression
        self.columns = columns
        # Compile expression for better performance
        self._code = compile(expression, "<string>", "eval")

    def evaluate(self, row: Dict[str, Any]) -> bool:
        # Check if all required columns are present
        if not all(col in row for col in self.columns):
            return False

        try:
            # Create evaluation context with row values
            context = {col: row[col] for col in self.columns}
            return bool(eval(self._code, {"__builtins__": {}}, context))
        except Exception:
            return False

    def to_string(self) -> str:
        return f"EXPR({self.expression})"

@dataclass
class PartialIndexMetadata:
    """Metadata for a partial index."""
    condition: BaseCondition
    included_count: int
    excluded_count: int
    last_updated: datetime
    estimated_selectivity: float
    last_reindex: Optional[datetime] = None
    avg_condition_evaluation_time: float = 0.0
    false_positive_rate: float = 0.0

class PartialIndex(Index, Generic[K, V]):
    """Index implementation that only includes rows matching a condition."""
    
    def __init__(
        self,
        name: str,
        table_name: str,
        columns: List[str],
        condition: BaseCondition,
        base_index: Index[K, V],
        **kwargs
    ):
        super().__init__(name, table_name, columns)
        self.condition = condition
        self.base_index = base_index
        self.included_count = 0
        self.excluded_count = 0
        self._last_updated = datetime.now()
        self._last_reindex = datetime.now()
        
        # Performance tracking
        self._insert_times: List[float] = []
        self._search_times: List[float] = []
        self._condition_eval_times: List[float] = []
        self._false_positives = 0
        self._total_evaluations = 0
        
    def insert(self, key: K, value: V, row_data: Dict[str, Any]):
        """Insert a key-value pair if it matches the condition."""
        start_time = datetime.now()
        
        eval_start = datetime.now()
        matches = self.condition.evaluate(row_data)
        eval_time = (datetime.now() - eval_start).total_seconds()
        self._condition_eval_times.append(eval_time)
        
        if matches:
            self.base_index.insert(key, value)
            self.included_count += 1
        else:
            self.excluded_count += 1
            
        self._last_updated = datetime.now()
        self._insert_times.append((datetime.now() - start_time).total_seconds())
        
    def search(self, query: Any, context: Optional[Dict[str, Any]] = None) -> List[V]:
        """Search the index, considering the partial condition."""
        start_time = datetime.now()
        
        if context:
            eval_start = datetime.now()
            matches = self.condition.evaluate(context)
            eval_time = (datetime.now() - eval_start).total_seconds()
            self._condition_eval_times.append(eval_time)
            
            if not matches:
                return []
        
        results = self.base_index.search(query)
        
        # Track potential false positives
        if context and results:
            self._false_positives += 1
        self._total_evaluations += 1
        
        self._search_times.append((datetime.now() - start_time).total_seconds())
        return results

    def reindex(self, data_iterator: Callable[[], List[tuple[K, V, Dict[str, Any]]]]):
        """Rebuild the index from scratch."""
        # Create new base index
        self.cleanup()
        
        # Reindex data
        for key, value, row_data in data_iterator():
            self.insert(key, value, row_data)
            
        self._last_reindex = datetime.now()

    def get_statistics(self) -> IndexStats:
        """Get index statistics."""
        base_stats = self.base_index.get_statistics()
        return IndexStats(
            total_entries=self.included_count,
            depth=base_stats.depth,
            size_bytes=base_stats.size_bytes,
            last_updated=self._last_updated,
            read_count=len(self._search_times),
            write_count=len(self._insert_times),
            avg_lookup_time_ms=base_stats.avg_lookup_time_ms,
            avg_insert_time_ms=base_stats.avg_insert_time_ms
        )
        
    def get_partial_metadata(self) -> PartialIndexMetadata:
        """Get metadata specific to partial indexing."""
        total = self.included_count + self.excluded_count
        selectivity = self.included_count / total if total > 0 else 0
        
        # Calculate average condition evaluation time
        avg_eval_time = (
            sum(self._condition_eval_times) / len(self._condition_eval_times)
            if self._condition_eval_times
            else 0.0
        )
        
        # Calculate false positive rate
        false_positive_rate = (
            self._false_positives / self._total_evaluations
            if self._total_evaluations > 0
            else 0.0
        )
        
        return PartialIndexMetadata(
            condition=self.condition,
            included_count=self.included_count,
            excluded_count=self.excluded_count,
            last_updated=self._last_updated,
            estimated_selectivity=selectivity,
            last_reindex=self._last_reindex,
            avg_condition_evaluation_time=avg_eval_time,
            false_positive_rate=false_positive_rate
        )
        
    def cleanup(self):
        """Clean up resources."""
        self.base_index.cleanup()
        self.included_count = 0
        self.excluded_count = 0
        self._insert_times = []
        self._search_times = []
        self._condition_eval_times = []
        self._false_positives = 0
        self._total_evaluations = 0

def create_partial_index(
    name: str,
    table_name: str,
    columns: List[str],
    condition: Union[BaseCondition, Dict[str, Any]],
    base_index_type: IndexType,
    **kwargs
) -> PartialIndex:
    """Helper function to create a partial index with a specific base index type."""
    from .manager import IndexManager
    
    # Convert dict condition to SimpleCondition if needed
    if isinstance(condition, dict):
        condition = SimpleCondition(
            column=condition["column"],
            operator=Operator(condition["operator"]),
            value=condition["value"]
        )
    
    # Create base index
    manager = IndexManager()
    base_index = manager._create_base_index(
        name=f"{name}_base",
        table_name=table_name,
        columns=columns,
        index_type=base_index_type,
        **kwargs
    )
    
    return PartialIndex(
        name=name,
        table_name=table_name,
        columns=columns,
        condition=condition,
        base_index=base_index
    ) 