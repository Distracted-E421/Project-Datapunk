from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum, auto
from .sql_advanced import AdvancedSQLParser
from .core import QueryNode, QueryPlan

@dataclass
class PivotSpec:
    """Specification for PIVOT operation."""
    pivot_column: str
    value_column: str
    pivot_values: List[str]
    aggregate_function: str

@dataclass
class UnpivotSpec:
    """Specification for UNPIVOT operation."""
    value_column: str
    name_column: str
    unpivot_columns: List[str]

@dataclass
class PatternSpec:
    """Specification for pattern matching."""
    pattern: str
    variables: Dict[str, Dict[str, Any]]
    defines: Dict[str, str]
    measures: Dict[str, str]

class ExtendedSQLParser(AdvancedSQLParser):
    """Extended SQL parser with additional advanced features."""
    
    def parse_query(self, query: str) -> QueryPlan:
        """Parse an extended SQL query."""
        # Check for PIVOT
        if "PIVOT" in query.upper():
            return self._parse_pivot_query(query)
            
        # Check for UNPIVOT
        if "UNPIVOT" in query.upper():
            return self._parse_unpivot_query(query)
            
        # Check for MATCH_RECOGNIZE
        if "MATCH_RECOGNIZE" in query.upper():
            return self._parse_pattern_query(query)
            
        # Check for MODEL clause
        if "MODEL" in query.upper():
            return self._parse_model_query(query)
            
        return super().parse_query(query)
        
    def _parse_pivot_query(self, query: str) -> QueryPlan:
        """Parse a PIVOT query."""
        # Split into source and pivot parts
        parts = query.split("PIVOT", 1)
        source_query = parts[0].strip()
        pivot_clause = parts[1].strip()
        
        # Parse pivot specification
        pivot_spec = self._parse_pivot_spec(pivot_clause)
        
        # Parse source query
        source_plan = super().parse_query(source_query)
        
        # Create pivot node
        root = QueryNode(
            operation='pivot',
            pivot_spec=pivot_spec,
            children=[source_plan.root]
        )
        
        return QueryPlan(root)
        
    def _parse_unpivot_query(self, query: str) -> QueryPlan:
        """Parse an UNPIVOT query."""
        # Split into source and unpivot parts
        parts = query.split("UNPIVOT", 1)
        source_query = parts[0].strip()
        unpivot_clause = parts[1].strip()
        
        # Parse unpivot specification
        unpivot_spec = self._parse_unpivot_spec(unpivot_clause)
        
        # Parse source query
        source_plan = super().parse_query(source_query)
        
        # Create unpivot node
        root = QueryNode(
            operation='unpivot',
            unpivot_spec=unpivot_spec,
            children=[source_plan.root]
        )
        
        return QueryPlan(root)
        
    def _parse_pattern_query(self, query: str) -> QueryPlan:
        """Parse a MATCH_RECOGNIZE query."""
        # Split into source and pattern parts
        parts = query.split("MATCH_RECOGNIZE", 1)
        source_query = parts[0].strip()
        pattern_clause = parts[1].strip()
        
        # Parse pattern specification
        pattern_spec = self._parse_pattern_spec(pattern_clause)
        
        # Parse source query
        source_plan = super().parse_query(source_query)
        
        # Create pattern matching node
        root = QueryNode(
            operation='pattern_match',
            pattern_spec=pattern_spec,
            children=[source_plan.root]
        )
        
        return QueryPlan(root)
        
    def _parse_model_query(self, query: str) -> QueryPlan:
        """Parse a MODEL clause query."""
        # Split into source and model parts
        parts = query.split("MODEL", 1)
        source_query = parts[0].strip()
        model_clause = parts[1].strip()
        
        # Parse model specification
        dimensions, measures, rules = self._parse_model_spec(model_clause)
        
        # Parse source query
        source_plan = super().parse_query(source_query)
        
        # Create model node
        root = QueryNode(
            operation='model',
            dimensions=dimensions,
            measures=measures,
            rules=rules,
            children=[source_plan.root]
        )
        
        return QueryPlan(root)
        
    def _parse_pivot_spec(self, clause: str) -> PivotSpec:
        """Parse PIVOT specification."""
        # Extract components from clause
        in_list_start = clause.find("IN (")
        agg_end = clause.find("FOR")
        
        # Parse aggregate function
        agg_part = clause[:agg_end].strip("()")
        agg_func, value_col = self._parse_aggregate(agg_part)
        
        # Parse pivot column
        pivot_col = clause[agg_end:in_list_start].strip()[4:].strip()
        
        # Parse pivot values
        values_part = clause[in_list_start + 3:].strip("()")
        pivot_values = [v.strip().strip("'") for v in values_part.split(",")]
        
        return PivotSpec(
            pivot_column=pivot_col,
            value_column=value_col,
            pivot_values=pivot_values,
            aggregate_function=agg_func
        )
        
    def _parse_unpivot_spec(self, clause: str) -> UnpivotSpec:
        """Parse UNPIVOT specification."""
        # Extract components from clause
        value_start = clause.find("(")
        for_start = clause.find("FOR")
        in_start = clause.find("IN")
        
        # Parse value column
        value_col = clause[value_start:for_start].strip("()")
        
        # Parse name column
        name_col = clause[for_start:in_start].strip()[4:].strip()
        
        # Parse unpivot columns
        cols_part = clause[in_start + 2:].strip("()")
        unpivot_cols = [c.strip() for c in cols_part.split(",")]
        
        return UnpivotSpec(
            value_column=value_col,
            name_column=name_col,
            unpivot_columns=unpivot_cols
        )
        
    def _parse_pattern_spec(self, clause: str) -> PatternSpec:
        """Parse MATCH_RECOGNIZE specification."""
        # Extract main components
        partition_end = clause.find("PATTERN")
        pattern_end = clause.find("DEFINE")
        measures_start = clause.find("MEASURES")
        
        # Parse pattern
        pattern_part = clause[partition_end:pattern_end].strip()[8:].strip("()")
        pattern = pattern_part
        
        # Parse variable definitions
        defines_part = clause[pattern_end:].strip()[7:]
        defines = self._parse_pattern_defines(defines_part)
        
        # Parse measures if present
        measures = {}
        if measures_start >= 0:
            measures_part = clause[measures_start:partition_end].strip()[9:]
            measures = self._parse_pattern_measures(measures_part)
        
        return PatternSpec(
            pattern=pattern,
            variables=defines,
            defines=defines,
            measures=measures
        )
        
    def _parse_model_spec(self, clause: str) -> tuple[List[str], List[str], List[Dict[str, Any]]]:
        """Parse MODEL clause specification."""
        # Extract main components
        dimension_start = clause.find("DIMENSION BY")
        measures_start = clause.find("MEASURES")
        rules_start = clause.find("RULES")
        
        # Parse dimensions
        dim_part = clause[dimension_start:measures_start].strip()[12:]
        dimensions = [d.strip() for d in dim_part.split(",")]
        
        # Parse measures
        meas_part = clause[measures_start:rules_start].strip()[9:]
        measures = [m.strip() for m in meas_part.split(",")]
        
        # Parse rules
        rules_part = clause[rules_start:].strip()[6:]
        rules = self._parse_model_rules(rules_part)
        
        return dimensions, measures, rules
        
    def _parse_aggregate(self, agg_expr: str) -> tuple[str, str]:
        """Parse aggregate expression."""
        func_end = agg_expr.find("(")
        func = agg_expr[:func_end].strip()
        col = agg_expr[func_end:].strip("()")
        return func, col
        
    def _parse_pattern_defines(self, defines: str) -> Dict[str, Dict[str, Any]]:
        """Parse pattern variable definitions."""
        result = {}
        current_var = None
        current_def = []
        
        for line in defines.split("\n"):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("AS"):
                if current_var:
                    result[current_var] = self._parse_pattern_condition(
                        " ".join(current_def)
                    )
                current_var = line[2:].strip()
                current_def = []
            else:
                current_def.append(line)
                
        if current_var:
            result[current_var] = self._parse_pattern_condition(
                " ".join(current_def)
            )
            
        return result
        
    def _parse_pattern_measures(self, measures: str) -> Dict[str, str]:
        """Parse pattern measures."""
        result = {}
        for measure in measures.split(","):
            parts = measure.split("AS")
            expr = parts[0].strip()
            alias = parts[1].strip() if len(parts) > 1 else expr
            result[alias] = expr
        return result
        
    def _parse_pattern_condition(self, condition: str) -> Dict[str, Any]:
        """Parse a pattern matching condition."""
        return {'condition': condition}  # Simplified for now
        
    def _parse_model_rules(self, rules: str) -> List[Dict[str, Any]]:
        """Parse MODEL rules."""
        result = []
        for rule in rules.split(")"):
            if not rule.strip():
                continue
            cell_assignment = rule.split("=")
            if len(cell_assignment) != 2:
                continue
            target = cell_assignment[0].strip()
            value = cell_assignment[1].strip()
            result.append({
                'target': target,
                'value': value
            })
        return result 