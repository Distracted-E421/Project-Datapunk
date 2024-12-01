from typing import Any, Dict, List, Optional, Union
from .core import (
    Parser,
    Lexer,
    Node,
    Token,
    TokenType,
    QueryContext,
    ParserError,
    SyntaxError,
    ValidationError
)

class NoSQLNode(Node):
    """Base class for NoSQL AST nodes"""
    pass

class QueryNode(NoSQLNode):
    """Node representing a NoSQL query"""
    
    def __init__(
        self,
        collection: str,
        filters: Optional['FilterNode'] = None,
        projections: Optional[List[str]] = None,
        sort: Optional[Dict[str, int]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ):
        self.collection = collection
        self.filters = filters
        self.projections = projections or []
        self.sort = sort or {}
        self.limit = limit
        self.skip = skip
        
    def accept(self, visitor: 'NodeVisitor') -> Any:
        return visitor.visit_query(self)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'query',
            'collection': self.collection,
            'filters': self.filters.to_dict() if self.filters else None,
            'projections': self.projections,
            'sort': self.sort,
            'limit': self.limit,
            'skip': self.skip
        }

class FilterNode(NoSQLNode):
    """Node representing a filter condition"""
    
    def __init__(
        self,
        field: str,
        operator: str,
        value: Any,
        logical_op: Optional[str] = None,
        next_filter: Optional['FilterNode'] = None
    ):
        self.field = field
        self.operator = operator
        self.value = value
        self.logical_op = logical_op
        self.next_filter = next_filter
        
    def accept(self, visitor: 'NodeVisitor') -> Any:
        return visitor.visit_filter(self)
        
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'type': 'filter',
            'field': self.field,
            'operator': self.operator,
            'value': self.value
        }
        if self.logical_op:
            result['logical_op'] = self.logical_op
            result['next'] = self.next_filter.to_dict()
        return result

class NoSQLLexer(Lexer):
    """NoSQL lexer implementation"""
    
    KEYWORDS = {
        'FIND': TokenType.SELECT,
        'IN': TokenType.FROM,
        'WHERE': TokenType.WHERE,
        'SORT': TokenType.ORDER_BY,
        'LIMIT': TokenType.IDENTIFIER,
        'SKIP': TokenType.IDENTIFIER,
        'AND': TokenType.AND,
        'OR': TokenType.OR,
        'NOT': TokenType.NOT,
        'NULL': TokenType.NULL,
        'TRUE': TokenType.BOOLEAN,
        'FALSE': TokenType.BOOLEAN
    }
    
    def __init__(self):
        self.query = ""
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        
    def tokenize(self, query: str) -> List[Token]:
        """Tokenize NoSQL query"""
        self.query = query
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
            
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens
        
    def scan_token(self):
        """Scan next token"""
        c = self.advance()
        
        if c.isspace():
            if c == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            return
            
        if c.isalpha() or c == '_':
            self.identifier()
        elif c.isdigit():
            self.number()
        elif c == '"' or c == "'":
            self.string(c)
        elif c == '{':
            self.object()
        elif c == '[':
            self.array()
        else:
            # Handle operators and delimiters
            if c == '=':
                self.add_token(TokenType.EQUALS)
            elif c == '<':
                if self.match('='):
                    self.add_token(TokenType.LESS_EQUALS)
                else:
                    self.add_token(TokenType.LESS_THAN)
            elif c == '>':
                if self.match('='):
                    self.add_token(TokenType.GREATER_EQUALS)
                else:
                    self.add_token(TokenType.GREATER_THAN)
            elif c == '!':
                if self.match('='):
                    self.add_token(TokenType.NOT_EQUALS)
                else:
                    self.add_token(TokenType.ERROR)
            elif c == '(':
                self.add_token(TokenType.LPAREN)
            elif c == ')':
                self.add_token(TokenType.RPAREN)
            elif c == ',':
                self.add_token(TokenType.COMMA)
            elif c == '.':
                self.add_token(TokenType.DOT)
            elif c == ';':
                self.add_token(TokenType.SEMICOLON)
            else:
                self.add_token(TokenType.ERROR)
                
    def object(self):
        """Handle object literals"""
        depth = 1
        while not self.is_at_end() and depth > 0:
            c = self.advance()
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                
        if depth > 0:
            self.add_token(TokenType.ERROR)
        else:
            self.add_token(TokenType.IDENTIFIER)
            
    def array(self):
        """Handle array literals"""
        depth = 1
        while not self.is_at_end() and depth > 0:
            c = self.advance()
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                
        if depth > 0:
            self.add_token(TokenType.ERROR)
        else:
            self.add_token(TokenType.IDENTIFIER)
            
    # ... rest of lexer methods from SQLLexer ...

class NoSQLParser(Parser):
    """NoSQL parser implementation"""
    
    def __init__(self, context: QueryContext):
        self.context = context
        self.lexer = NoSQLLexer()
        self.tokens: List[Token] = []
        self.current = 0
        
    def parse(self, query: str) -> Node:
        """Parse NoSQL query"""
        self.tokens = self.lexer.tokenize(query)
        self.current = 0
        
        try:
            return self.parse_query()
        except ParserError as e:
            self.context.add_error(e)
            return None
            
    def validate(self, ast: Node) -> None:
        """Validate NoSQL AST"""
        if not ast:
            return
            
        try:
            self.validate_query(ast)
        except ValidationError as e:
            self.context.add_error(e)
            
    def parse_query(self) -> QueryNode:
        """Parse NoSQL query"""
        self.consume(TokenType.SELECT, "Expected 'FIND'")
        self.consume(TokenType.FROM, "Expected 'IN'")
        
        collection = self.consume(
            TokenType.IDENTIFIER,
            "Expected collection name"
        ).value
        
        filters = None
        projections = []
        sort = {}
        limit = None
        skip = None
        
        while not self.is_at_end():
            if self.match(TokenType.WHERE):
                filters = self.parse_filters()
            elif self.match_keyword("PROJECT"):
                projections = self.parse_projections()
            elif self.match(TokenType.ORDER_BY):
                sort = self.parse_sort()
            elif self.match_keyword("LIMIT"):
                limit = self.parse_number()
            elif self.match_keyword("SKIP"):
                skip = self.parse_number()
            else:
                break
                
        return QueryNode(
            collection,
            filters,
            projections,
            sort,
            limit,
            skip
        )
        
    def parse_filters(self) -> FilterNode:
        """Parse filter conditions"""
        field = self.consume(
            TokenType.IDENTIFIER,
            "Expected field name"
        ).value
        
        operator = self.advance().value
        value = self.parse_value()
        
        filter_node = FilterNode(field, operator, value)
        
        # Handle chained filters
        if self.match(TokenType.AND) or self.match(TokenType.OR):
            logical_op = self.previous().type.name
            next_filter = self.parse_filters()
            filter_node.logical_op = logical_op
            filter_node.next_filter = next_filter
            
        return filter_node
        
    def parse_projections(self) -> List[str]:
        """Parse projection fields"""
        fields = []
        
        while True:
            field = self.consume(
                TokenType.IDENTIFIER,
                "Expected field name"
            ).value
            fields.append(field)
            
            if not self.match(TokenType.COMMA):
                break
                
        return fields
        
    def parse_sort(self) -> Dict[str, int]:
        """Parse sort specification"""
        sort = {}
        
        while True:
            field = self.consume(
                TokenType.IDENTIFIER,
                "Expected field name"
            ).value
            
            direction = 1  # Default ascending
            if self.match_keyword("DESC"):
                direction = -1
                
            sort[field] = direction
            
            if not self.match(TokenType.COMMA):
                break
                
        return sort
        
    def parse_value(self) -> Any:
        """Parse value literal"""
        token = self.advance()
        
        if token.type == TokenType.NUMBER:
            return float(token.value)
        elif token.type == TokenType.STRING:
            return token.value[1:-1]  # Remove quotes
        elif token.type == TokenType.BOOLEAN:
            return token.value.upper() == "TRUE"
        elif token.type == TokenType.NULL:
            return None
        else:
            return token.value
            
    def parse_number(self) -> int:
        """Parse numeric literal"""
        token = self.consume(TokenType.NUMBER, "Expected number")
        return int(token.value)
        
    # ... rest of parser methods from SQLParser ...
    
    def validate_query(self, node: QueryNode):
        """Validate NoSQL query"""
        # Validate collection
        if not node.collection:
            raise ValidationError("Query must specify a collection")
            
        # Validate filters
        if node.filters:
            self.validate_filters(node.filters)
            
        # Validate limit/skip
        if node.limit is not None and node.limit < 0:
            raise ValidationError("Limit must be non-negative")
            
        if node.skip is not None and node.skip < 0:
            raise ValidationError("Skip must be non-negative")
            
    def validate_filters(self, node: FilterNode):
        """Validate filter conditions"""
        # Add filter validation logic here
        pass 