import pytest
from typing import Dict, Any
from ..src.query.validation.query_validation_core import (
    ValidationLevel,
    ValidationCategory,
    ValidationResult,
    QueryValidator
)
from ..src.query.validation.validation_sql import (
    SQLTableExistsRule,
    SQLColumnExistsRule,
    SQLTypeCompatibilityRule,
    SQLResourceLimitRule,
    SQLSecurityRule,
    SQLSyntaxRule
)

@pytest.fixture
def validator():
    return QueryValidator()

@pytest.fixture
def sample_schema():
    return {
        'users': {
            'id': 'integer',
            'name': 'string',
            'age': 'integer',
            'email': 'string'
        },
        'orders': {
            'id': 'integer',
            'user_id': 'integer',
            'amount': 'decimal',
            'status': 'string'
        }
    }

@pytest.fixture
def sample_permissions():
    return {
        'SELECT',
        'INSERT',
        'UPDATE'
    }

def test_table_exists_rule(validator, sample_schema):
    """Test table existence validation."""
    rule = SQLTableExistsRule()
    validator.add_rule(rule)
    
    # Valid query
    valid_query = "SELECT * FROM users"
    results = validator.validate(valid_query, {'schema': sample_schema})
    assert not results
    
    # Invalid query with non-existent table
    invalid_query = "SELECT * FROM nonexistent_table"
    results = validator.validate(invalid_query, {'schema': sample_schema})
    assert results
    assert results[0].level == ValidationLevel.ERROR
    assert results[0].category == ValidationCategory.SEMANTIC
    assert "nonexistent_table" in results[0].message

def test_column_exists_rule(validator, sample_schema):
    """Test column existence validation."""
    rule = SQLColumnExistsRule()
    validator.add_rule(rule)
    
    # Valid query
    valid_query = "SELECT name, age FROM users"
    results = validator.validate(valid_query, {'schema': sample_schema})
    assert not results
    
    # Invalid query with non-existent column
    invalid_query = "SELECT nonexistent_column FROM users"
    results = validator.validate(invalid_query, {'schema': sample_schema})
    assert results
    assert results[0].level == ValidationLevel.ERROR
    assert results[0].category == ValidationCategory.SEMANTIC
    assert "columns do not exist" in results[0].message

def test_type_compatibility_rule(validator, sample_schema):
    """Test type compatibility validation."""
    rule = SQLTypeCompatibilityRule()
    validator.add_rule(rule)
    
    # Valid query with compatible types
    valid_query = "SELECT * FROM users WHERE age > 18"
    results = validator.validate(valid_query, {'schema': sample_schema})
    assert not results
    
    # Invalid query with incompatible types
    invalid_query = "SELECT * FROM users WHERE name > 18"
    results = validator.validate(invalid_query, {'schema': sample_schema})
    assert results
    assert results[0].level == ValidationLevel.ERROR
    assert results[0].category == ValidationCategory.SEMANTIC
    assert "incompatibility" in results[0].message

def test_resource_limit_rule(validator):
    """Test resource limit validation."""
    rule = SQLResourceLimitRule(
        max_tables=2,
        max_joins=1,
        max_subqueries=1
    )
    validator.add_rule(rule)
    
    # Valid query within limits
    valid_query = """
        SELECT u.name, o.amount
        FROM users u
        JOIN orders o ON u.id = o.user_id
    """
    results = validator.validate(valid_query, {})
    assert not results
    
    # Invalid query exceeding limits
    invalid_query = """
        SELECT *
        FROM users u
        JOIN orders o ON u.id = o.user_id
        JOIN products p ON o.product_id = p.id
        WHERE o.id IN (SELECT id FROM orders WHERE amount > 100)
    """
    results = validator.validate(invalid_query, {})
    assert results
    assert results[0].level == ValidationLevel.WARNING
    assert results[0].category == ValidationCategory.RESOURCE
    assert "exceeds resource limits" in results[0].message

def test_security_rule(validator, sample_permissions):
    """Test security validation."""
    rule = SQLSecurityRule()
    validator.add_rule(rule)
    
    # Valid query with sufficient permissions
    valid_query = "SELECT * FROM users"
    results = validator.validate(
        valid_query,
        {'permissions': sample_permissions}
    )
    assert not results
    
    # Invalid query without required permissions
    invalid_query = "DELETE FROM users"
    results = validator.validate(
        invalid_query,
        {'permissions': sample_permissions}
    )
    assert results
    assert results[0].level == ValidationLevel.ERROR
    assert results[0].category == ValidationCategory.SECURITY
    assert "Insufficient permissions" in results[0].message

def test_syntax_rule(validator):
    """Test syntax validation."""
    rule = SQLSyntaxRule()
    validator.add_rule(rule)
    
    # Valid query with correct syntax
    valid_query = "SELECT * FROM users WHERE age > 18"
    results = validator.validate(valid_query, {})
    assert not results
    
    # Invalid query with syntax error
    invalid_query = "SELECT * FORM users WEHRE age > 18"
    results = validator.validate(invalid_query, {})
    assert results
    assert results[0].level == ValidationLevel.ERROR
    assert results[0].category == ValidationCategory.SYNTAX
    assert "syntax" in results[0].message.lower()

def test_multiple_rules(validator, sample_schema, sample_permissions):
    """Test multiple validation rules together."""
    # Add all rules
    validator.add_rule(SQLTableExistsRule())
    validator.add_rule(SQLColumnExistsRule())
    validator.add_rule(SQLTypeCompatibilityRule())
    validator.add_rule(SQLResourceLimitRule())
    validator.add_rule(SQLSecurityRule())
    validator.add_rule(SQLSyntaxRule())
    
    # Valid query that passes all rules
    valid_query = """
        SELECT u.name, o.amount
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE u.age > 18
    """
    context = {
        'schema': sample_schema,
        'permissions': sample_permissions
    }
    results = validator.validate(valid_query, context)
    assert not results
    
    # Invalid query that fails multiple rules
    invalid_query = """
        DELETE FROM nonexistent_table
        WHERE invalid_column > 'string'
        AND id IN (
            SELECT id FROM another_table
            JOIN yet_another_table
        )
    """
    results = validator.validate(invalid_query, context)
    assert results
    assert len(results) > 1  # Multiple validation failures
    
    # Verify different types of failures
    failure_categories = {r.category for r in results}
    assert ValidationCategory.SEMANTIC in failure_categories
    assert ValidationCategory.SECURITY in failure_categories

def test_error_handling(validator):
    """Test validation error handling."""
    # Add rule that raises exception
    class BrokenRule(SQLTableExistsRule):
        def _extract_tables(self, query):
            raise Exception("Simulated error")
    
    validator.add_rule(BrokenRule())
    
    # Validation should continue despite rule error
    results = validator.validate("SELECT * FROM users", {})
    assert not results  # Should return empty list, not raise exception

def test_validation_context(validator, sample_schema):
    """Test validation with different contexts."""
    rule = SQLTableExistsRule()
    validator.add_rule(rule)
    
    query = "SELECT * FROM users"
    
    # Test with schema
    results1 = validator.validate(query, {'schema': sample_schema})
    assert not results1
    
    # Test without schema
    results2 = validator.validate(query, {})
    assert not results2  # Should handle missing context gracefully
    
    # Test with empty schema
    results3 = validator.validate(query, {'schema': {}})
    assert results3  # Should detect missing table

def test_validation_suggestions(validator):
    """Test validation suggestions."""
    rule = SQLSyntaxRule()
    validator.add_rule(rule)
    
    # Query with syntax error
    query = "SELECT * FORM users"
    results = validator.validate(query, {})
    
    assert results
    assert results[0].suggestion is not None
    assert isinstance(results[0].suggestion, str)
    assert len(results[0].suggestion) > 0 