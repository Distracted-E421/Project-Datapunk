import pytest
from ..src.query.parser.core import (
    Token,
    TokenType,
    QueryContext,
    ParserError,
    SyntaxError,
    ValidationError
)
from ..src.query.parser.sql import SQLParser
from ..src.query.parser.nosql import NoSQLParser

@pytest.fixture
def sql_parser():
    return SQLParser(QueryContext())

@pytest.fixture
def nosql_parser():
    return NoSQLParser(QueryContext())

class TestSQLParser:
    """Test SQL parser implementation"""
    
    def test_simple_select(self, sql_parser):
        """Test simple SELECT query"""
        query = "SELECT id, name FROM users"
        ast = sql_parser.parse(query)
        
        assert ast is not None
        assert len(ast.columns) == 2
        assert ast.columns[0].name == "id"
        assert ast.columns[1].name == "name"
        assert ast.from_table.name == "users"
        
    def test_select_with_where(self, sql_parser):
        """Test SELECT with WHERE clause"""
        query = "SELECT id, name FROM users WHERE age >= 18"
        ast = sql_parser.parse(query)
        
        assert ast is not None
        assert ast.where is not None
        assert ast.where.condition.left.name == "age"
        assert ast.where.condition.operator == ">="
        assert ast.where.condition.right == "18"
        
    def test_select_with_join(self, sql_parser):
        """Test SELECT with JOIN"""
        query = """
            SELECT users.name, orders.id
            FROM users
            JOIN orders ON users.id = orders.user_id
        """
        ast = sql_parser.parse(query)
        
        assert ast is not None
        assert len(ast.from_table.joins) == 1
        join = ast.from_table.joins[0]
        assert join.table.name == "orders"
        assert join.condition.left.name == "id"
        assert join.condition.left.table == "users"
        
    def test_select_with_alias(self, sql_parser):
        """Test SELECT with column aliases"""
        query = "SELECT id AS user_id, name AS full_name FROM users"
        ast = sql_parser.parse(query)
        
        assert ast is not None
        assert ast.columns[0].name == "id"
        assert ast.columns[0].alias == "user_id"
        assert ast.columns[1].name == "name"
        assert ast.columns[1].alias == "full_name"
        
    def test_syntax_error(self, sql_parser):
        """Test syntax error handling"""
        query = "SELECT FROM users"  # Missing columns
        ast = sql_parser.parse(query)
        
        assert ast is None
        assert sql_parser.context.has_errors()
        assert any(
            isinstance(e, SyntaxError)
            for e in sql_parser.context.errors
        )
        
    def test_validation_error(self, sql_parser):
        """Test validation error handling"""
        query = "SELECT FROM users"  # Missing columns
        ast = sql_parser.parse(query)
        sql_parser.validate(ast)
        
        assert sql_parser.context.has_errors()
        assert any(
            isinstance(e, ValidationError)
            for e in sql_parser.context.errors
        )

class TestNoSQLParser:
    """Test NoSQL parser implementation"""
    
    def test_simple_find(self, nosql_parser):
        """Test simple FIND query"""
        query = "FIND IN users"
        ast = nosql_parser.parse(query)
        
        assert ast is not None
        assert ast.collection == "users"
        assert not ast.filters
        assert not ast.projections
        
    def test_find_with_filter(self, nosql_parser):
        """Test FIND with filter"""
        query = "FIND IN users WHERE age >= 18"
        ast = nosql_parser.parse(query)
        
        assert ast is not None
        assert ast.filters is not None
        assert ast.filters.field == "age"
        assert ast.filters.operator == ">="
        assert ast.filters.value == 18
        
    def test_find_with_multiple_filters(self, nosql_parser):
        """Test FIND with multiple filters"""
        query = "FIND IN users WHERE age >= 18 AND status = 'active'"
        ast = nosql_parser.parse(query)
        
        assert ast is not None
        assert ast.filters is not None
        assert ast.filters.logical_op == "AND"
        assert ast.filters.field == "age"
        assert ast.filters.next_filter.field == "status"
        
    def test_find_with_projections(self, nosql_parser):
        """Test FIND with projections"""
        query = "FIND IN users PROJECT id, name, email"
        ast = nosql_parser.parse(query)
        
        assert ast is not None
        assert len(ast.projections) == 3
        assert "id" in ast.projections
        assert "name" in ast.projections
        assert "email" in ast.projections
        
    def test_find_with_sort(self, nosql_parser):
        """Test FIND with sort"""
        query = "FIND IN users SORT name ASC, age DESC"
        ast = nosql_parser.parse(query)
        
        assert ast is not None
        assert len(ast.sort) == 2
        assert ast.sort["name"] == 1  # ASC
        assert ast.sort["age"] == -1  # DESC
        
    def test_find_with_limit_skip(self, nosql_parser):
        """Test FIND with limit and skip"""
        query = "FIND IN users LIMIT 10 SKIP 20"
        ast = nosql_parser.parse(query)
        
        assert ast is not None
        assert ast.limit == 10
        assert ast.skip == 20
        
    def test_find_complex_query(self, nosql_parser):
        """Test complex FIND query"""
        query = """
            FIND IN users
            WHERE age >= 18 AND status = 'active'
            PROJECT id, name, email
            SORT name ASC
            LIMIT 10
            SKIP 20
        """
        ast = nosql_parser.parse(query)
        
        assert ast is not None
        assert ast.collection == "users"
        assert ast.filters is not None
        assert len(ast.projections) == 3
        assert len(ast.sort) == 1
        assert ast.limit == 10
        assert ast.skip == 20
        
    def test_syntax_error(self, nosql_parser):
        """Test syntax error handling"""
        query = "FIND WHERE age >= 18"  # Missing IN clause
        ast = nosql_parser.parse(query)
        
        assert ast is None
        assert nosql_parser.context.has_errors()
        assert any(
            isinstance(e, SyntaxError)
            for e in nosql_parser.context.errors
        )
        
    def test_validation_error(self, nosql_parser):
        """Test validation error handling"""
        query = "FIND IN users LIMIT -1"  # Negative limit
        ast = nosql_parser.parse(query)
        nosql_parser.validate(ast)
        
        assert nosql_parser.context.has_errors()
        assert any(
            isinstance(e, ValidationError)
            for e in nosql_parser.context.errors
        )

def test_parser_factory():
    """Test parser factory"""
    from ..src.query.parser.core import ParserFactory
    
    sql_parser = ParserFactory.create_parser("sql")
    assert isinstance(sql_parser, SQLParser)
    
    nosql_parser = ParserFactory.create_parser("nosql")
    assert isinstance(nosql_parser, NoSQLParser)
    
    with pytest.raises(ValueError):
        ParserFactory.create_parser("invalid")

def test_parser_registry():
    """Test parser registry"""
    from ..src.query.parser.core import ParserRegistry
    
    # Test built-in parsers
    sql_parser = ParserRegistry.get_parser("sql")
    assert isinstance(sql_parser, SQLParser)
    
    nosql_parser = ParserRegistry.get_parser("nosql")
    assert isinstance(nosql_parser, NoSQLParser)
    
    # Test custom parser registration
    class CustomParser(SQLParser):
        pass
        
    ParserRegistry.register("custom", CustomParser)
    custom_parser = ParserRegistry.get_parser("custom")
    assert isinstance(custom_parser, CustomParser)
    
    with pytest.raises(ValueError):
        ParserRegistry.get_parser("invalid") 