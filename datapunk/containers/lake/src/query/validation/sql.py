from typing import Dict, List, Set, Any, Optional
from sqlparse import parse as sql_parse
from sqlparse.sql import TokenList, Token, Identifier, Function
import sqlparse
from .core import (
    ValidationRule,
    ValidationResult,
    ValidationLevel,
    ValidationCategory,
    TableExistsRule,
    ColumnExistsRule,
    TypeCompatibilityRule,
    ResourceLimitRule,
    SecurityRule
)

class SQLTableExistsRule(TableExistsRule):
    """SQL-specific table existence validation."""
    
    def _extract_tables(self, query: str) -> Set[str]:
        """Extract table names from SQL query."""
        try:
            tables = set()
            parsed = sql_parse(query)[0]
            
            def extract_from_token(token):
                if isinstance(token, Identifier):
                    # Handle table names in FROM clause
                    tables.add(token.get_real_name())
                elif isinstance(token, TokenList):
                    for t in token.tokens:
                        extract_from_token(t)
            
            extract_from_token(parsed)
            return tables
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            return set()

class SQLColumnExistsRule(ColumnExistsRule):
    """SQL-specific column existence validation."""
    
    def _extract_columns(self, query: str) -> Dict[str, Set[str]]:
        """Extract column references by table from SQL query."""
        try:
            columns = {}
            parsed = sql_parse(query)[0]
            
            def extract_from_token(token):
                if isinstance(token, Identifier):
                    # Handle column references
                    parts = token.get_parent_name().split('.')
                    if len(parts) == 2:
                        table, col = parts
                        if table not in columns:
                            columns[table] = set()
                        columns[table].add(col)
                elif isinstance(token, TokenList):
                    for t in token.tokens:
                        extract_from_token(t)
            
            extract_from_token(parsed)
            return columns
        except Exception as e:
            self.logger.error(f"Error extracting columns: {e}")
            return {}

class SQLTypeCompatibilityRule(TypeCompatibilityRule):
    """SQL-specific type compatibility validation."""
    
    def _extract_operations(self, query: str) -> List[Dict[str, Any]]:
        """Extract operations from SQL query."""
        try:
            operations = []
            parsed = sql_parse(query)[0]
            
            def extract_from_token(token):
                if isinstance(token, Function):
                    # Handle function calls
                    operations.append({
                        'type': 'function',
                        'name': token.get_name(),
                        'arguments': [
                            str(arg) for arg in token.get_parameters()
                        ]
                    })
                elif isinstance(token, TokenList):
                    # Handle operators
                    if token.is_group():
                        ops = [
                            t for t in token.tokens
                            if t.ttype in sqlparse.tokens.Operator
                        ]
                        if ops:
                            operations.append({
                                'type': 'operator',
                                'operator': str(ops[0]),
                                'operands': [
                                    str(t) for t in token.tokens
                                    if t.ttype not in sqlparse.tokens.Operator
                                ]
                            })
                    
                    for t in token.tokens:
                        extract_from_token(t)
            
            extract_from_token(parsed)
            return operations
        except Exception as e:
            self.logger.error(f"Error extracting operations: {e}")
            return []
    
    def _check_compatibility(self,
                           operation: Dict[str, Any],
                           schema: Dict[str, Any]) -> bool:
        """Check type compatibility of SQL operation."""
        try:
            if operation['type'] == 'function':
                # Check function argument types
                return self._check_function_compatibility(
                    operation['name'],
                    operation['arguments'],
                    schema
                )
            elif operation['type'] == 'operator':
                # Check operator operand types
                return self._check_operator_compatibility(
                    operation['operator'],
                    operation['operands'],
                    schema
                )
            return True
        except Exception as e:
            self.logger.error(f"Error checking compatibility: {e}")
            return False
    
    def _check_function_compatibility(self,
                                    func_name: str,
                                    arguments: List[str],
                                    schema: Dict[str, Any]) -> bool:
        """Check function argument type compatibility."""
        # Implementation depends on supported functions
        return True
    
    def _check_operator_compatibility(self,
                                    operator: str,
                                    operands: List[str],
                                    schema: Dict[str, Any]) -> bool:
        """Check operator operand type compatibility."""
        # Implementation depends on supported operators
        return True

class SQLResourceLimitRule(ResourceLimitRule):
    """SQL-specific resource limit validation."""
    
    def _analyze_query(self, query: str) -> Dict[str, int]:
        """Analyze SQL query for resource metrics."""
        try:
            metrics = {
                'tables': 0,
                'joins': 0,
                'subqueries': 0
            }
            
            parsed = sql_parse(query)[0]
            
            def analyze_token(token):
                if isinstance(token, TokenList):
                    # Count tables in FROM clause
                    if token.is_group() and 'FROM' in str(token).upper():
                        metrics['tables'] += len([
                            t for t in token.tokens
                            if isinstance(t, Identifier)
                        ])
                    
                    # Count JOIN clauses
                    if 'JOIN' in str(token).upper():
                        metrics['joins'] += 1
                    
                    # Count subqueries
                    if token.is_group() and '(' in str(token):
                        if 'SELECT' in str(token).upper():
                            metrics['subqueries'] += 1
                    
                    for t in token.tokens:
                        analyze_token(t)
            
            analyze_token(parsed)
            return metrics
        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            return {'tables': 0, 'joins': 0, 'subqueries': 0}

class SQLSecurityRule(SecurityRule):
    """SQL-specific security validation."""
    
    def _extract_required_permissions(self, query: str) -> Set[str]:
        """Extract required permissions from SQL query."""
        try:
            permissions = set()
            parsed = sql_parse(query)[0]
            
            def extract_from_token(token):
                if isinstance(token, TokenList):
                    # Check for SELECT permission
                    if token.is_group() and 'SELECT' in str(token).upper():
                        permissions.add('SELECT')
                    
                    # Check for INSERT permission
                    if token.is_group() and 'INSERT' in str(token).upper():
                        permissions.add('INSERT')
                    
                    # Check for UPDATE permission
                    if token.is_group() and 'UPDATE' in str(token).upper():
                        permissions.add('UPDATE')
                    
                    # Check for DELETE permission
                    if token.is_group() and 'DELETE' in str(token).upper():
                        permissions.add('DELETE')
                    
                    for t in token.tokens:
                        extract_from_token(t)
            
            extract_from_token(parsed)
            return permissions
        except Exception as e:
            self.logger.error(f"Error extracting permissions: {e}")
            return set()

class SQLSyntaxRule(ValidationRule):
    """Validates SQL syntax."""
    
    def __init__(self):
        super().__init__(
            name="sql_syntax",
            level=ValidationLevel.ERROR,
            category=ValidationCategory.SYNTAX
        )
    
    def validate(self,
                query: str,
                context: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate SQL syntax."""
        try:
            # Try parsing the query
            parsed = sql_parse(query)
            
            # Check for basic syntax issues
            if not parsed or not str(parsed[0]).strip():
                return ValidationResult(
                    level=self.level,
                    category=self.category,
                    message="Invalid SQL syntax",
                    context={'query': query},
                    suggestion="Check SQL syntax"
                )
            
            # Additional syntax checks
            issues = self._check_syntax_issues(parsed[0])
            if issues:
                return ValidationResult(
                    level=self.level,
                    category=self.category,
                    message="SQL syntax issues detected",
                    context={'issues': issues},
                    suggestion="Review and fix syntax issues"
                )
            
            return None
        except Exception as e:
            self.logger.error(f"Error in syntax validation: {e}")
            return ValidationResult(
                level=self.level,
                category=self.category,
                message=f"Syntax error: {str(e)}",
                context={'error': str(e)},
                suggestion="Fix SQL syntax error"
            )
    
    def _check_syntax_issues(self, parsed: TokenList) -> List[str]:
        """Check for common syntax issues."""
        issues = []
        
        def check_token(token):
            if isinstance(token, TokenList):
                # Check for unclosed parentheses
                if token.is_group() and not token.is_group():
                    issues.append("Unclosed parentheses")
                
                # Check for missing FROM clause in SELECT
                if 'SELECT' in str(token).upper() and 'FROM' not in str(token).upper():
                    issues.append("Missing FROM clause in SELECT")
                
                # Check for invalid JOIN syntax
                if 'JOIN' in str(token).upper() and 'ON' not in str(token).upper():
                    issues.append("Missing ON clause in JOIN")
                
                for t in token.tokens:
                    check_token(t)
        
        check_token(parsed)
        return issues 