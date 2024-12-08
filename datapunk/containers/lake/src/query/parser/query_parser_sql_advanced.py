from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum, auto
from .query_parser_core import QueryNode, QueryPlan
from .query_parser_sql import SQLParser

class WindowFrameType(Enum):
    """Types of window frames."""
    ROWS = auto()
    RANGE = auto()

@dataclass
class WindowFrame:
    """Window frame specification."""
    frame_type: WindowFrameType
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    start_expr: Optional[str] = None
    end_expr: Optional[str] = None

@dataclass
class WindowSpec:
    """Window specification."""
    partition_by: List[str]
    order_by: List[str]
    frame: Optional[WindowFrame] = None

class AdvancedSQLParser(SQLParser):
    """Enhanced SQL parser with support for advanced features."""
    
    def parse_query(self, query: str) -> QueryPlan:
        """Parse an advanced SQL query."""
        # Check for CTEs
        if "WITH" in query.upper():
            return self._parse_with_query(query)
            
        # Check for set operations
        for op in ["UNION", "INTERSECT", "EXCEPT"]:
            if op in query.upper():
                return self._parse_set_operation(query, op)
                
        # Check for MERGE
        if "MERGE" in query.upper():
            return self._parse_merge(query)
            
        return super().parse_query(query)
        
    def _parse_with_query(self, query: str) -> QueryPlan:
        """Parse a query with CTEs."""
        # Split into CTE definitions and main query
        parts = query.split("WITH", 1)[1].split("SELECT", 1)
        cte_defs = parts[0].strip()
        main_query = "SELECT" + parts[1]
        
        # Parse each CTE
        ctes: Dict[str, QueryNode] = {}
        for cte_def in self._split_ctes(cte_defs):
            name, subquery = self._parse_cte_def(cte_def)
            ctes[name] = self.parse_query(subquery).root
            
        # Parse main query with CTE references
        main_plan = super().parse_query(main_query)
        self._resolve_cte_references(main_plan.root, ctes)
        
        return main_plan
        
    def _parse_set_operation(self, query: str, operation: str) -> QueryPlan:
        """Parse a set operation query."""
        # Split into component queries
        parts = query.split(operation)
        left_query = parts[0].strip()
        right_query = parts[1].strip()
        
        # Parse component queries
        left_plan = self.parse_query(left_query)
        right_plan = self.parse_query(right_query)
        
        # Create set operation node
        root = QueryNode(
            operation=operation.lower(),
            children=[left_plan.root, right_plan.root]
        )
        
        return QueryPlan(root)
        
    def _parse_merge(self, query: str) -> QueryPlan:
        """Parse a MERGE statement."""
        # Extract target table and source
        parts = query.split("MERGE INTO", 1)[1].split("USING", 1)
        target_table = parts[0].strip()
        source_parts = parts[1].split("ON", 1)
        source = source_parts[0].strip()
        condition = source_parts[1].strip()
        
        # Parse match clauses
        matched_clause = self._extract_matched_clause(query)
        not_matched_clause = self._extract_not_matched_clause(query)
        
        # Create merge operation node
        root = QueryNode(
            operation='merge',
            target_table=target_table,
            source=self.parse_query(source).root,
            merge_condition=self._parse_condition(condition),
            matched_action=matched_clause,
            not_matched_action=not_matched_clause
        )
        
        return QueryPlan(root)
        
    def parse_window_function(self, expr: str) -> Dict[str, Any]:
        """Parse a window function expression."""
        # Extract function and window spec
        parts = expr.split("OVER", 1)
        func = parts[0].strip()
        window = parts[1].strip("()")
        
        # Parse window components
        partition = self._extract_partition(window)
        order = self._extract_order(window)
        frame = self._extract_frame(window)
        
        return {
            'function': func,
            'window': WindowSpec(
                partition_by=partition,
                order_by=order,
                frame=frame
            )
        }
        
    def parse_subquery(self, subquery: str) -> QueryNode:
        """Parse a subquery expression."""
        # Remove outer parentheses
        subquery = subquery.strip("()")
        
        # Check for scalar subquery
        if "SELECT" in subquery.upper() and \
           "FROM" not in subquery.upper():
            return self._parse_scalar_subquery(subquery)
            
        # Check for EXISTS
        if subquery.upper().startswith("EXISTS"):
            return self._parse_exists_subquery(subquery)
            
        # Regular subquery
        return self.parse_query(subquery).root
        
    def _split_ctes(self, cte_defs: str) -> List[str]:
        """Split CTE definitions."""
        defs = []
        current = []
        paren_count = 0
        
        for char in cte_defs:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                defs.append(''.join(current))
                current = []
                continue
                
            current.append(char)
            
        if current:
            defs.append(''.join(current))
            
        return defs
        
    def _parse_cte_def(self, cte_def: str) -> tuple[str, str]:
        """Parse a CTE definition."""
        parts = cte_def.split("AS", 1)
        name = parts[0].strip()
        subquery = parts[1].strip("()")
        return name, subquery
        
    def _resolve_cte_references(self, node: QueryNode, 
                              ctes: Dict[str, QueryNode]) -> None:
        """Resolve CTE references in a query plan."""
        if hasattr(node, 'table_name') and \
           node.table_name in ctes:
            # Replace table scan with CTE subquery
            cte_node = ctes[node.table_name]
            node.operation = cte_node.operation
            node.children = cte_node.children
            for attr in cte_node.__dict__:
                if attr not in ('operation', 'children'):
                    setattr(node, attr, getattr(cte_node, attr))
                    
        for child in node.children:
            self._resolve_cte_references(child, ctes)
            
    def _extract_matched_clause(self, query: str) -> Dict[str, Any]:
        """Extract WHEN MATCHED clause from MERGE."""
        if "WHEN MATCHED" not in query.upper():
            return None
            
        clause = query.split("WHEN MATCHED", 1)[1]
        if "WHEN NOT MATCHED" in clause.upper():
            clause = clause.split("WHEN NOT MATCHED")[0]
            
        action = "UPDATE" if "UPDATE" in clause.upper() else "DELETE"
        if action == "UPDATE":
            set_clause = clause.split("SET", 1)[1].strip()
            return {
                'action': action,
                'set_clause': self._parse_set_clause(set_clause)
            }
        return {'action': action}
        
    def _extract_not_matched_clause(self, query: str) -> Dict[str, Any]:
        """Extract WHEN NOT MATCHED clause from MERGE."""
        if "WHEN NOT MATCHED" not in query.upper():
            return None
            
        clause = query.split("WHEN NOT MATCHED", 1)[1]
        if "THEN INSERT" not in clause.upper():
            return None
            
        parts = clause.split("THEN INSERT", 1)[1].strip()
        columns = self._extract_columns(parts)
        values = self._extract_values(parts)
        
        return {
            'action': 'INSERT',
            'columns': columns,
            'values': values
        }
        
    def _extract_partition(self, window: str) -> List[str]:
        """Extract PARTITION BY clause from window spec."""
        if "PARTITION BY" not in window.upper():
            return []
            
        partition = window.split("PARTITION BY", 1)[1]
        if "ORDER BY" in partition.upper():
            partition = partition.split("ORDER BY")[0]
            
        return [col.strip() for col in partition.split(",")]
        
    def _extract_order(self, window: str) -> List[str]:
        """Extract ORDER BY clause from window spec."""
        if "ORDER BY" not in window.upper():
            return []
            
        order = window.split("ORDER BY", 1)[1]
        if "ROWS" in order.upper() or "RANGE" in order.upper():
            order = order.split(
                "ROWS" if "ROWS" in order.upper() else "RANGE"
            )[0]
            
        return [col.strip() for col in order.split(",")]
        
    def _extract_frame(self, window: str) -> Optional[WindowFrame]:
        """Extract frame clause from window spec."""
        if "ROWS" not in window.upper() and \
           "RANGE" not in window.upper():
            return None
            
        frame_type = WindowFrameType.ROWS \
                    if "ROWS" in window.upper() \
                    else WindowFrameType.RANGE
                    
        frame_spec = window.split(
            "ROWS" if frame_type == WindowFrameType.ROWS else "RANGE"
        )[1].strip()
        
        return self._parse_frame_spec(frame_spec, frame_type)
        
    def _parse_frame_spec(self, spec: str, 
                         frame_type: WindowFrameType) -> WindowFrame:
        """Parse a window frame specification."""
        if "BETWEEN" in spec.upper():
            parts = spec.split("BETWEEN")[1].split("AND")
            start = parts[0].strip()
            end = parts[1].strip()
            
            return WindowFrame(
                frame_type=frame_type,
                start_expr=start,
                end_expr=end
            )
            
        # Single bound spec
        return WindowFrame(
            frame_type=frame_type,
            start_expr=spec.strip()
        )
        
    def _parse_scalar_subquery(self, subquery: str) -> QueryNode:
        """Parse a scalar subquery."""
        expr = subquery.split("SELECT", 1)[1].strip()
        return QueryNode(
            operation='scalar_subquery',
            expression=expr
        )
        
    def _parse_exists_subquery(self, subquery: str) -> QueryNode:
        """Parse an EXISTS subquery."""
        inner_query = subquery.split("EXISTS", 1)[1].strip("()")
        return QueryNode(
            operation='exists',
            children=[self.parse_query(inner_query).root]
        ) 