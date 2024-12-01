from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import operator

from .partial import (
    BaseCondition,
    SimpleCondition,
    CompositeCondition,
    ExpressionCondition,
    Operator
)

@dataclass
class OptimizationStats:
    """Statistics about condition optimization."""
    original_depth: int
    optimized_depth: int
    removed_redundant: int
    simplified_expressions: int
    merged_conditions: int

class ConditionOptimizer:
    """Optimizes partial index conditions for better performance."""
    
    def __init__(self):
        self._redundant_count = 0
        self._simplified_count = 0
        self._merged_count = 0
        
    def optimize(self, condition: BaseCondition) -> tuple[BaseCondition, OptimizationStats]:
        """Optimize a condition through multiple passes."""
        original_depth = self._get_condition_depth(condition)
        
        # Reset counters
        self._redundant_count = 0
        self._simplified_count = 0
        self._merged_count = 0
        
        # Apply optimization passes
        optimized = condition
        optimized = self._remove_redundant(optimized)
        optimized = self._simplify_expressions(optimized)
        optimized = self._merge_conditions(optimized)
        optimized = self._reorder_conditions(optimized)
        
        return optimized, OptimizationStats(
            original_depth=original_depth,
            optimized_depth=self._get_condition_depth(optimized),
            removed_redundant=self._redundant_count,
            simplified_expressions=self._simplified_count,
            merged_conditions=self._merged_count
        )
        
    def _get_condition_depth(self, condition: BaseCondition) -> int:
        """Calculate the depth of a condition tree."""
        if isinstance(condition, SimpleCondition):
            return 1
        elif isinstance(condition, ExpressionCondition):
            return 1
        elif isinstance(condition, CompositeCondition):
            return 1 + max(self._get_condition_depth(c) for c in condition.conditions)
        return 1
        
    def _remove_redundant(self, condition: BaseCondition) -> BaseCondition:
        """Remove redundant conditions."""
        if isinstance(condition, (SimpleCondition, ExpressionCondition)):
            return condition
            
        if isinstance(condition, CompositeCondition):
            # First optimize children
            optimized_children = [
                self._remove_redundant(c) for c in condition.conditions
            ]
            
            # Remove duplicates
            unique_conditions = []
            seen_conditions = set()
            
            for child in optimized_children:
                condition_str = child.to_string()
                if condition_str not in seen_conditions:
                    unique_conditions.append(child)
                    seen_conditions.add(condition_str)
                else:
                    self._redundant_count += 1
                    
            # Remove always true/false conditions
            filtered_conditions = []
            for child in unique_conditions:
                if isinstance(child, SimpleCondition):
                    # Skip tautologies like x = x
                    if (child.operator == Operator.EQ and 
                        isinstance(child.value, str) and 
                        child.value == child.column):
                        self._redundant_count += 1
                        continue
                filtered_conditions.append(child)
                
            if len(filtered_conditions) == 1:
                return filtered_conditions[0]
                
            return CompositeCondition(condition.operator, filtered_conditions)
            
        return condition
        
    def _simplify_expressions(self, condition: BaseCondition) -> BaseCondition:
        """Simplify complex expressions into simpler forms."""
        if isinstance(condition, ExpressionCondition):
            # Try to convert expression to simple condition
            if self._is_simple_comparison(condition.expression):
                simple = self._expression_to_simple(condition)
                if simple:
                    self._simplified_count += 1
                    return simple
            return condition
            
        if isinstance(condition, CompositeCondition):
            return CompositeCondition(
                condition.operator,
                [self._simplify_expressions(c) for c in condition.conditions]
            )
            
        return condition
        
    def _merge_conditions(self, condition: BaseCondition) -> BaseCondition:
        """Merge related conditions when possible."""
        if isinstance(condition, CompositeCondition):
            if condition.operator == "AND":
                # Group conditions by column
                column_conditions: Dict[str, List[SimpleCondition]] = {}
                other_conditions = []
                
                for child in condition.conditions:
                    if isinstance(child, SimpleCondition):
                        column_conditions.setdefault(child.column, []).append(child)
                    else:
                        other_conditions.append(child)
                        
                # Try to merge conditions on same column
                merged_conditions = []
                for column, conditions in column_conditions.items():
                    if len(conditions) > 1:
                        merged = self._merge_column_conditions(conditions)
                        if merged:
                            self._merged_count += 1
                            merged_conditions.append(merged)
                        else:
                            merged_conditions.extend(conditions)
                    else:
                        merged_conditions.extend(conditions)
                        
                if other_conditions or merged_conditions:
                    return CompositeCondition(
                        condition.operator,
                        merged_conditions + other_conditions
                    )
                    
        return condition
        
    def _reorder_conditions(self, condition: BaseCondition) -> BaseCondition:
        """Reorder conditions for optimal evaluation."""
        if isinstance(condition, CompositeCondition):
            # Sort conditions by complexity (simpler first)
            sorted_conditions = sorted(
                condition.conditions,
                key=lambda c: (
                    isinstance(c, ExpressionCondition),  # Expression conditions last
                    isinstance(c, CompositeCondition),   # Composite conditions second
                    -self._estimate_selectivity(c)       # Higher selectivity first
                )
            )
            return CompositeCondition(condition.operator, sorted_conditions)
        return condition
        
    def _is_simple_comparison(self, expression: str) -> bool:
        """Check if an expression is a simple comparison."""
        import ast
        try:
            tree = ast.parse(expression)
            if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Expr):
                return False
            compare = tree.body[0].value
            return isinstance(compare, ast.Compare) and len(compare.ops) == 1
        except SyntaxError:
            return False
            
    def _expression_to_simple(
        self,
        condition: ExpressionCondition
    ) -> Optional[SimpleCondition]:
        """Convert a simple expression condition to a simple condition."""
        import ast
        try:
            tree = ast.parse(condition.expression)
            compare = tree.body[0].value
            
            if not isinstance(compare, ast.Compare):
                return None
                
            # Get left side (column name)
            if not isinstance(compare.left, ast.Name):
                return None
            column = compare.left.id
            
            # Get operator
            op_map = {
                ast.Eq: Operator.EQ,
                ast.NotEq: Operator.NE,
                ast.Lt: Operator.LT,
                ast.LtE: Operator.LE,
                ast.Gt: Operator.GT,
                ast.GtE: Operator.GE,
            }
            if type(compare.ops[0]) not in op_map:
                return None
            operator = op_map[type(compare.ops[0])]
            
            # Get right side (value)
            comparator = compare.comparators[0]
            if isinstance(comparator, ast.Constant):
                value = comparator.value
            elif isinstance(comparator, ast.Str):
                value = comparator.s
            elif isinstance(comparator, ast.Num):
                value = comparator.n
            else:
                return None
                
            return SimpleCondition(column, operator, value)
            
        except (SyntaxError, AttributeError):
            return None
            
    def _merge_column_conditions(
        self,
        conditions: List[SimpleCondition]
    ) -> Optional[SimpleCondition]:
        """Try to merge multiple conditions on the same column."""
        if len(conditions) != 2:
            return None
            
        a, b = conditions
        if a.column != b.column:
            return None
            
        # Merge range conditions
        if (a.operator in (Operator.GT, Operator.GE) and 
            b.operator in (Operator.LT, Operator.LE)):
            return SimpleCondition(
                a.column,
                Operator.BETWEEN,
                (
                    a.value if a.operator == Operator.GE else a.value + 1,
                    b.value if b.operator == Operator.LE else b.value - 1
                )
            )
            
        # Merge equality with IN
        if a.operator == Operator.EQ and b.operator == Operator.IN:
            if a.value in b.value:
                return SimpleCondition(a.column, Operator.EQ, a.value)
            return None
            
        return None
        
    def _estimate_selectivity(self, condition: BaseCondition) -> float:
        """Estimate condition selectivity (0-1, lower is more selective)."""
        if isinstance(condition, SimpleCondition):
            # Rough estimates based on operator type
            selectivity_map = {
                Operator.EQ: 0.1,        # Very selective
                Operator.IN: 0.3,        # Moderately selective
                Operator.BETWEEN: 0.4,   # Range is less selective
                Operator.GT: 0.5,        # Half the range
                Operator.LT: 0.5,
                Operator.GE: 0.5,
                Operator.LE: 0.5,
                Operator.NE: 0.9,        # Excludes very little
                Operator.LIKE: 0.7,      # Pattern matching is expensive
                Operator.NOT_LIKE: 0.8,
            }
            return selectivity_map.get(condition.operator, 0.5)
            
        if isinstance(condition, CompositeCondition):
            child_selectivity = [
                self._estimate_selectivity(c) for c in condition.conditions
            ]
            if condition.operator == "AND":
                # Product of selectivities for AND
                return float(
                    __import__("functools").reduce(operator.mul, child_selectivity)
                )
            else:
                # Average for OR (simplified)
                return sum(child_selectivity) / len(child_selectivity)
                
        if isinstance(condition, ExpressionCondition):
            # Expressions are usually less selective
            return 0.8
            
        return 1.0 