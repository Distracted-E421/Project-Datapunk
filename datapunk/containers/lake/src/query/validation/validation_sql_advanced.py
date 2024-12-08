from typing import Dict, List, Set, Any, Optional
from sqlparse import parse as sql_parse
from sqlparse.sql import TokenList, Token, Identifier, Function
import sqlparse
from .query_validation_core import (
    ValidationRule,
    ValidationResult,
    ValidationLevel,
    ValidationCategory
)

class SQLComplexityRule(ValidationRule):
    """Validates SQL query complexity."""
    
    def __init__(self,
                 max_depth: int = 3,
                 max_conditions: int = 10,
                 max_unions: int = 2):
        super().__init__(
            name="sql_complexity",
            level=ValidationLevel.WARNING,
            category=ValidationCategory.PERFORMANCE
        )
        self.max_depth = max_depth
        self.max_conditions = max_conditions
        self.max_unions = max_unions
    
    def validate(self,
                query: str,
                context: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate SQL query complexity."""
        try:
            parsed = sql_parse(query)[0]
            metrics = self._analyze_complexity(parsed)
            
            issues = []
            if metrics['depth'] > self.max_depth:
                issues.append(
                    f"Query depth ({metrics['depth']}) exceeds limit ({self.max_depth})"
                )
            
            if metrics['conditions'] > self.max_conditions:
                issues.append(
                    f"Number of conditions ({metrics['conditions']}) exceeds limit ({self.max_conditions})"
                )
            
            if metrics['unions'] > self.max_unions:
                issues.append(
                    f"Number of unions ({metrics['unions']}) exceeds limit ({self.max_unions})"
                )
            
            if issues:
                return ValidationResult(
                    level=self.level,
                    category=self.category,
                    message="Query is too complex",
                    context={'issues': issues, 'metrics': metrics},
                    suggestion="Consider simplifying the query"
                )
            
            return None
        except Exception as e:
            self.logger.error(f"Error in complexity validation: {e}")
            return None
    
    def _analyze_complexity(self, parsed: TokenList) -> Dict[str, int]:
        """Analyze query complexity metrics."""
        metrics = {
            'depth': 0,
            'conditions': 0,
            'unions': 0
        }
        
        def analyze_token(token, depth=0):
            if isinstance(token, TokenList):
                # Update max depth
                metrics['depth'] = max(metrics['depth'], depth)
                
                # Count conditions
                if token.is_group() and any(
                    t.value.upper() in ['AND', 'OR']
                    for t in token.tokens
                ):
                    metrics['conditions'] += 1
                
                # Count unions
                if token.is_group() and any(
                    t.value.upper() == 'UNION'
                    for t in token.tokens
                ):
                    metrics['unions'] += 1
                
                # Analyze nested tokens
                for t in token.tokens:
                    analyze_token(t, depth + 1)
        
        analyze_token(parsed)
        return metrics

class SQLPerformanceRule(ValidationRule):
    """Validates SQL query performance characteristics."""
    
    def __init__(self):
        super().__init__(
            name="sql_performance",
            level=ValidationLevel.WARNING,
            category=ValidationCategory.PERFORMANCE
        )
    
    def validate(self,
                query: str,
                context: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate SQL query performance."""
        try:
            parsed = sql_parse(query)[0]
            issues = self._analyze_performance(parsed)
            
            if issues:
                return ValidationResult(
                    level=self.level,
                    category=self.category,
                    message="Query may have performance issues",
                    context={'issues': issues},
                    suggestion="Review query for performance optimizations"
                )
            
            return None
        except Exception as e:
            self.logger.error(f"Error in performance validation: {e}")
            return None
    
    def _analyze_performance(self, parsed: TokenList) -> List[str]:
        """Analyze query for performance issues."""
        issues = []
        
        def analyze_token(token):
            if isinstance(token, TokenList):
                # Check for SELECT *
                if token.is_group() and 'SELECT' in str(token).upper():
                    if '*' in str(token):
                        issues.append(
                            "Using SELECT * can impact performance"
                        )
                
                # Check for DISTINCT
                if 'DISTINCT' in str(token).upper():
                    issues.append(
                        "DISTINCT operation can be expensive"
                    )
                
                # Check for multiple IN clauses
                if str(token).upper().count(' IN ') > 1:
                    issues.append(
                        "Multiple IN clauses can impact performance"
                    )
                
                # Check for OR conditions
                if ' OR ' in str(token).upper():
                    issues.append(
                        "OR conditions may prevent index usage"
                    )
                
                # Check for functions in WHERE clause
                if token.is_group() and 'WHERE' in str(token).upper():
                    if any(isinstance(t, Function) for t in token.tokens):
                        issues.append(
                            "Functions in WHERE clause can prevent index usage"
                        )
                
                # Analyze nested tokens
                for t in token.tokens:
                    analyze_token(t)
        
        analyze_token(parsed)
        return issues

class SQLIndexUsageRule(ValidationRule):
    """Validates potential index usage in SQL queries."""
    
    def __init__(self):
        super().__init__(
            name="sql_index_usage",
            level=ValidationLevel.WARNING,
            category=ValidationCategory.PERFORMANCE
        )
    
    def validate(self,
                query: str,
                context: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate SQL query index usage."""
        try:
            parsed = sql_parse(query)[0]
            schema = context.get('schema', {})
            indexes = context.get('indexes', {})
            
            issues = self._analyze_index_usage(parsed, schema, indexes)
            
            if issues:
                return ValidationResult(
                    level=self.level,
                    category=self.category,
                    message="Query may not use indexes effectively",
                    context={'issues': issues},
                    suggestion="Consider adding or using appropriate indexes"
                )
            
            return None
        except Exception as e:
            self.logger.error(f"Error in index usage validation: {e}")
            return None
    
    def _analyze_index_usage(self,
                           parsed: TokenList,
                           schema: Dict[str, Any],
                           indexes: Dict[str, Any]) -> List[str]:
        """Analyze query for index usage issues."""
        issues = []
        
        def analyze_token(token):
            if isinstance(token, TokenList):
                # Check WHERE clause
                if token.is_group() and 'WHERE' in str(token).upper():
                    where_issues = self._analyze_where_clause(
                        token,
                        schema,
                        indexes
                    )
                    issues.extend(where_issues)
                
                # Check JOIN conditions
                if token.is_group() and 'JOIN' in str(token).upper():
                    join_issues = self._analyze_join_clause(
                        token,
                        schema,
                        indexes
                    )
                    issues.extend(join_issues)
                
                # Check ORDER BY clause
                if token.is_group() and 'ORDER BY' in str(token).upper():
                    order_issues = self._analyze_order_clause(
                        token,
                        schema,
                        indexes
                    )
                    issues.extend(order_issues)
                
                # Analyze nested tokens
                for t in token.tokens:
                    analyze_token(t)
        
        analyze_token(parsed)
        return issues
    
    def _analyze_where_clause(self,
                            token: TokenList,
                            schema: Dict[str, Any],
                            indexes: Dict[str, Any]) -> List[str]:
        """Analyze WHERE clause for index usage."""
        issues = []
        
        # Extract conditions
        conditions = self._extract_conditions(token)
        
        for condition in conditions:
            table = condition.get('table')
            column = condition.get('column')
            operator = condition.get('operator')
            
            if table and column:
                # Check if column has an index
                table_indexes = indexes.get(table, {})
                if not any(
                    column in idx['columns']
                    for idx in table_indexes.values()
                ):
                    issues.append(
                        f"No index found for {table}.{column}"
                    )
                
                # Check operator compatibility with indexes
                if operator in ['LIKE', 'NOT LIKE'] and column in str(token):
                    if str(token).count('%') > 0:
                        issues.append(
                            f"Leading wildcard in LIKE on {table}.{column} prevents index usage"
                        )
        
        return issues
    
    def _analyze_join_clause(self,
                           token: TokenList,
                           schema: Dict[str, Any],
                           indexes: Dict[str, Any]) -> List[str]:
        """Analyze JOIN clause for index usage."""
        issues = []
        
        # Extract join conditions
        conditions = self._extract_join_conditions(token)
        
        for condition in conditions:
            left_table = condition.get('left_table')
            left_column = condition.get('left_column')
            right_table = condition.get('right_table')
            right_column = condition.get('right_column')
            
            # Check indexes on both sides
            if left_table and left_column:
                left_indexes = indexes.get(left_table, {})
                if not any(
                    left_column in idx['columns']
                    for idx in left_indexes.values()
                ):
                    issues.append(
                        f"No index found for join column {left_table}.{left_column}"
                    )
            
            if right_table and right_column:
                right_indexes = indexes.get(right_table, {})
                if not any(
                    right_column in idx['columns']
                    for idx in right_indexes.values()
                ):
                    issues.append(
                        f"No index found for join column {right_table}.{right_column}"
                    )
        
        return issues
    
    def _analyze_order_clause(self,
                            token: TokenList,
                            schema: Dict[str, Any],
                            indexes: Dict[str, Any]) -> List[str]:
        """Analyze ORDER BY clause for index usage."""
        issues = []
        
        # Extract order columns
        columns = self._extract_order_columns(token)
        
        for column_info in columns:
            table = column_info.get('table')
            column = column_info.get('column')
            
            if table and column:
                table_indexes = indexes.get(table, {})
                if not any(
                    column in idx['columns']
                    for idx in table_indexes.values()
                ):
                    issues.append(
                        f"No index found for ORDER BY column {table}.{column}"
                    )
        
        return issues
    
    def _extract_conditions(self, token: TokenList) -> List[Dict[str, str]]:
        """Extract conditions from WHERE clause."""
        conditions = []
        
        def extract_condition(t):
            if isinstance(t, Identifier):
                parts = str(t).split('.')
                if len(parts) == 2:
                    return {
                        'table': parts[0],
                        'column': parts[1]
                    }
            return None
        
        current_condition = {}
        for t in token.tokens:
            if isinstance(t, Identifier):
                condition = extract_condition(t)
                if condition:
                    current_condition.update(condition)
            elif t.ttype in sqlparse.tokens.Comparison:
                current_condition['operator'] = str(t).strip()
                conditions.append(current_condition)
                current_condition = {}
        
        return conditions
    
    def _extract_join_conditions(self, token: TokenList) -> List[Dict[str, str]]:
        """Extract conditions from JOIN clause."""
        conditions = []
        
        def extract_table_column(t):
            if isinstance(t, Identifier):
                parts = str(t).split('.')
                if len(parts) == 2:
                    return parts[0], parts[1]
            return None, None
        
        for t in token.tokens:
            if isinstance(t, TokenList) and 'ON' in str(t).upper():
                left = right = None
                for sub_token in t.tokens:
                    if isinstance(sub_token, Identifier):
                        if not left:
                            left_table, left_column = extract_table_column(sub_token)
                            left = True
                        else:
                            right_table, right_column = extract_table_column(sub_token)
                            conditions.append({
                                'left_table': left_table,
                                'left_column': left_column,
                                'right_table': right_table,
                                'right_column': right_column
                            })
        
        return conditions
    
    def _extract_order_columns(self, token: TokenList) -> List[Dict[str, str]]:
        """Extract columns from ORDER BY clause."""
        columns = []
        
        for t in token.tokens:
            if isinstance(t, Identifier):
                parts = str(t).split('.')
                if len(parts) == 2:
                    columns.append({
                        'table': parts[0],
                        'column': parts[1]
                    })
        
        return columns 