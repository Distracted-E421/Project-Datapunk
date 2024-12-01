from typing import Any, Dict, List, Optional, Set
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

class SQLNode(Node):
    """Base class for SQL AST nodes"""
    pass

class SelectNode(SQLNode):
    """Node representing a SELECT statement"""
    
    def __init__(
        self,
        columns: List['ColumnNode'],
        from_table: Optional['TableNode'],
        where: Optional['WhereNode'] = None,
        group_by: Optional['GroupByNode'] = None,
        having: Optional['HavingNode'] = None,
        order_by: Optional['OrderByNode'] = None
    ):
        self.columns = columns
        self.from_table = from_table
        self.where = where
        self.group_by = group_by
        self.having = having
        self.order_by = order_by
        
    def accept(self, visitor: 'NodeVisitor') -> Any:
        return visitor.visit_select(self)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'select',
            'columns': [col.to_dict() for col in self.columns],
            'from': self.from_table.to_dict() if self.from_table else None,
            'where': self.where.to_dict() if self.where else None,
            'group_by': self.group_by.to_dict() if self.group_by else None,
            'having': self.having.to_dict() if self.having else None,
            'order_by': self.order_by.to_dict() if self.order_by else None
        }

class ColumnNode(SQLNode):
    """Node representing a column reference"""
    
    def __init__(
        self,
        name: str,
        alias: Optional[str] = None,
        table: Optional[str] = None
    ):
        self.name = name
        self.alias = alias
        self.table = table
        
    def accept(self, visitor: 'NodeVisitor') -> Any:
        return visitor.visit_column(self)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'column',
            'name': self.name,
            'alias': self.alias,
            'table': self.table
        }

class TableNode(SQLNode):
    """Node representing a table reference"""
    
    def __init__(
        self,
        name: str,
        alias: Optional[str] = None,
        joins: Optional[List['JoinNode']] = None
    ):
        self.name = name
        self.alias = alias
        self.joins = joins or []
        
    def accept(self, visitor: 'NodeVisitor') -> Any:
        return visitor.visit_table(self)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'table',
            'name': self.name,
            'alias': self.alias,
            'joins': [join.to_dict() for join in self.joins]
        }

class JoinNode(SQLNode):
    """Node representing a JOIN clause"""
    
    def __init__(
        self,
        table: TableNode,
        condition: 'ConditionNode',
        join_type: str = 'INNER'
    ):
        self.table = table
        self.condition = condition
        self.join_type = join_type
        
    def accept(self, visitor: 'NodeVisitor') -> Any:
        return visitor.visit_join(self)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'join',
            'join_type': self.join_type,
            'table': self.table.to_dict(),
            'condition': self.condition.to_dict()
        }

class WhereNode(SQLNode):
    """Node representing a WHERE clause"""
    
    def __init__(self, condition: 'ConditionNode'):
        self.condition = condition
        
    def accept(self, visitor: 'NodeVisitor') -> Any:
        return visitor.visit_where(self)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'where',
            'condition': self.condition.to_dict()
        }

class ConditionNode(SQLNode):
    """Node representing a condition"""
    
    def __init__(
        self,
        left: SQLNode,
        operator: str,
        right: SQLNode
    ):
        self.left = left
        self.operator = operator
        self.right = right
        
    def accept(self, visitor: 'NodeVisitor') -> Any:
        return visitor.visit_condition(self)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'condition',
            'left': self.left.to_dict(),
            'operator': self.operator,
            'right': self.right.to_dict()
        }

class SQLLexer(Lexer):
    """SQL lexer implementation"""
    
    KEYWORDS = {
        'SELECT': TokenType.SELECT,
        'FROM': TokenType.FROM,
        'WHERE': TokenType.WHERE,
        'GROUP': TokenType.GROUP_BY,
        'ORDER': TokenType.ORDER_BY,
        'HAVING': TokenType.HAVING,
        'JOIN': TokenType.JOIN,
        'ON': TokenType.ON,
        'AND': TokenType.AND,
        'OR': TokenType.OR,
        'NOT': TokenType.NOT,
        'IN': TokenType.IN,
        'LIKE': TokenType.LIKE,
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
        """Tokenize SQL query"""
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
                
    def identifier(self):
        """Handle identifiers and keywords"""
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
            
        text = self.query[self.start:self.current].upper()
        token_type = self.KEYWORDS.get(text, TokenType.IDENTIFIER)
        self.add_token(token_type)
        
    def number(self):
        """Handle numeric literals"""
        while self.peek().isdigit():
            self.advance()
            
        # Handle decimal numbers
        if self.peek() == '.' and self.peek_next().isdigit():
            self.advance()  # Consume the dot
            while self.peek().isdigit():
                self.advance()
                
        self.add_token(TokenType.NUMBER)
        
    def string(self, quote: str):
        """Handle string literals"""
        while self.peek() != quote and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            self.advance()
            
        if self.is_at_end():
            self.add_token(TokenType.ERROR)
            return
            
        self.advance()  # Closing quote
        self.add_token(TokenType.STRING)
        
    def add_token(self, type: TokenType):
        """Add token to list"""
        text = self.query[self.start:self.current]
        self.tokens.append(Token(type, text, self.line, self.column))
        self.column += self.current - self.start
        
    def advance(self) -> str:
        """Advance current position"""
        self.current += 1
        return self.query[self.current - 1]
        
    def match(self, expected: str) -> bool:
        """Match current character"""
        if self.is_at_end() or self.query[self.current] != expected:
            return False
            
        self.current += 1
        return True
        
    def peek(self) -> str:
        """Look at current character"""
        if self.is_at_end():
            return '\0'
        return self.query[self.current]
        
    def peek_next(self) -> str:
        """Look at next character"""
        if self.current + 1 >= len(self.query):
            return '\0'
        return self.query[self.current + 1]
        
    def is_at_end(self) -> bool:
        """Check if at end of input"""
        return self.current >= len(self.query)

class SQLParser(Parser):
    """SQL parser implementation"""
    
    def __init__(self, context: QueryContext):
        self.context = context
        self.lexer = SQLLexer()
        self.tokens: List[Token] = []
        self.current = 0
        
    def parse(self, query: str) -> Node:
        """Parse SQL query"""
        self.tokens = self.lexer.tokenize(query)
        self.current = 0
        
        try:
            return self.parse_select()
        except ParserError as e:
            self.context.add_error(e)
            return None
            
    def validate(self, ast: Node) -> None:
        """Validate SQL AST"""
        if not ast:
            return
            
        try:
            self.validate_select(ast)
        except ValidationError as e:
            self.context.add_error(e)
            
    def parse_select(self) -> SelectNode:
        """Parse SELECT statement"""
        self.consume(TokenType.SELECT, "Expected 'SELECT'")
        
        # Parse columns
        columns = self.parse_columns()
        
        # Parse FROM clause
        from_table = None
        if self.match(TokenType.FROM):
            from_table = self.parse_table()
            
        # Parse optional clauses
        where = self.parse_where() if self.match(TokenType.WHERE) else None
        group_by = self.parse_group_by() if self.check(TokenType.GROUP_BY) else None
        having = self.parse_having() if self.check(TokenType.HAVING) else None
        order_by = self.parse_order_by() if self.check(TokenType.ORDER_BY) else None
        
        return SelectNode(
            columns,
            from_table,
            where,
            group_by,
            having,
            order_by
        )
        
    def parse_columns(self) -> List[ColumnNode]:
        """Parse column list"""
        columns = []
        
        while True:
            column = self.parse_column()
            columns.append(column)
            
            if not self.match(TokenType.COMMA):
                break
                
        return columns
        
    def parse_column(self) -> ColumnNode:
        """Parse column reference"""
        if self.check(TokenType.IDENTIFIER):
            name = self.advance().value
            table = None
            
            if self.match(TokenType.DOT):
                table = name
                name = self.consume(
                    TokenType.IDENTIFIER,
                    "Expected column name"
                ).value
                
            alias = None
            if self.match_keyword("AS"):
                alias = self.consume(
                    TokenType.IDENTIFIER,
                    "Expected column alias"
                ).value
                
            return ColumnNode(name, alias, table)
        else:
            raise SyntaxError(
                "Expected column name",
                self.peek()
            )
            
    def parse_table(self) -> TableNode:
        """Parse table reference"""
        name = self.consume(TokenType.IDENTIFIER, "Expected table name").value
        alias = None
        
        if self.match_keyword("AS"):
            alias = self.consume(
                TokenType.IDENTIFIER,
                "Expected table alias"
            ).value
            
        joins = []
        while self.match(TokenType.JOIN):
            joins.append(self.parse_join())
            
        return TableNode(name, alias, joins)
        
    def parse_join(self) -> JoinNode:
        """Parse JOIN clause"""
        table = self.parse_table()
        self.consume(TokenType.ON, "Expected 'ON' after JOIN")
        condition = self.parse_condition()
        
        return JoinNode(table, condition)
        
    def parse_condition(self) -> ConditionNode:
        """Parse condition"""
        left = self.parse_expression()
        operator = self.advance().value
        right = self.parse_expression()
        
        return ConditionNode(left, operator, right)
        
    def parse_expression(self) -> SQLNode:
        """Parse expression"""
        # Simplified for now - just handle column references
        if self.check(TokenType.IDENTIFIER):
            return self.parse_column()
        else:
            raise SyntaxError(
                "Expected expression",
                self.peek()
            )
            
    def consume(self, type: TokenType, message: str) -> Token:
        """Consume token of expected type"""
        if self.check(type):
            return self.advance()
            
        raise SyntaxError(message, self.peek())
        
    def match(self, type: TokenType) -> bool:
        """Match token type"""
        if self.check(type):
            self.advance()
            return True
        return False
        
    def match_keyword(self, keyword: str) -> bool:
        """Match keyword"""
        if (
            self.check(TokenType.IDENTIFIER) and
            self.peek().value.upper() == keyword.upper()
        ):
            self.advance()
            return True
        return False
        
    def check(self, type: TokenType) -> bool:
        """Check token type"""
        if self.is_at_end():
            return False
        return self.peek().type == type
        
    def advance(self) -> Token:
        """Advance current position"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()
        
    def peek(self) -> Token:
        """Look at current token"""
        return self.tokens[self.current]
        
    def previous(self) -> Token:
        """Get previous token"""
        return self.tokens[self.current - 1]
        
    def is_at_end(self) -> bool:
        """Check if at end of tokens"""
        return self.peek().type == TokenType.EOF
        
    def validate_select(self, node: SelectNode):
        """Validate SELECT statement"""
        # Validate columns
        if not node.columns:
            raise ValidationError("SELECT must have at least one column")
            
        # Validate table references
        if node.from_table:
            self.validate_table(node.from_table)
            
        # Validate other clauses
        if node.where:
            self.validate_condition(node.where.condition)
            
    def validate_table(self, node: TableNode):
        """Validate table reference"""
        # Add table validation logic here
        pass
        
    def validate_condition(self, node: ConditionNode):
        """Validate condition"""
        # Add condition validation logic here
        pass 