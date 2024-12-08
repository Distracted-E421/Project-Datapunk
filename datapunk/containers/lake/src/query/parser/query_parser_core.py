from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class TokenType(Enum):
    """Token types for query parsing"""
    # Keywords
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    GROUP_BY = auto()
    ORDER_BY = auto()
    HAVING = auto()
    JOIN = auto()
    ON = auto()
    
    # Operators
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER_THAN = auto()
    LESS_THAN = auto()
    GREATER_EQUALS = auto()
    LESS_EQUALS = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    LIKE = auto()
    
    # Literals
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    NULL = auto()
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    DOT = auto()
    SEMICOLON = auto()
    
    # Identifiers
    IDENTIFIER = auto()
    
    # Special
    EOF = auto()
    ERROR = auto()

@dataclass
class Token:
    """Token representation"""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __str__(self) -> str:
        return f"{self.type.name}({self.value}) at line {self.line}, col {self.column}"

class ParserError(Exception):
    """Base class for parser errors"""
    def __init__(self, message: str, token: Optional[Token] = None):
        self.message = message
        self.token = token
        super().__init__(self.format_message())
        
    def format_message(self) -> str:
        if self.token:
            return f"{self.message} at line {self.token.line}, col {self.token.column}"
        return self.message

class SyntaxError(ParserError):
    """Raised for syntax errors during parsing"""
    pass

class ValidationError(ParserError):
    """Raised for semantic validation errors"""
    pass

class Node(ABC):
    """Base class for AST nodes"""
    
    @abstractmethod
    def accept(self, visitor: 'NodeVisitor') -> Any:
        """Accept a visitor for traversal"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        pass

class NodeVisitor(ABC):
    """Base visitor for AST traversal"""
    
    @abstractmethod
    def visit(self, node: Node) -> Any:
        """Visit a node in the AST"""
        method_name = f'visit_{node.__class__.__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node: Node) -> Any:
        """Default visit method"""
        raise NotImplementedError(
            f"No visit method for {node.__class__.__name__}"
        )

class Parser(ABC):
    """Base parser interface"""
    
    @abstractmethod
    def parse(self, query: str) -> Node:
        """Parse a query string into an AST"""
        pass
    
    @abstractmethod
    def validate(self, ast: Node) -> None:
        """Validate the AST"""
        pass

class Lexer(ABC):
    """Base lexer interface"""
    
    @abstractmethod
    def tokenize(self, query: str) -> List[Token]:
        """Tokenize a query string"""
        pass

class QueryContext:
    """Context for query parsing and validation"""
    
    def __init__(self):
        self.errors: List[ParserError] = []
        self.warnings: List[str] = []
        self.metadata: Dict[str, Any] = {}
        
    def add_error(self, error: ParserError):
        """Add an error to the context"""
        self.errors.append(error)
        logger.error(str(error))
        
    def add_warning(self, message: str):
        """Add a warning to the context"""
        self.warnings.append(message)
        logger.warning(message)
        
    def has_errors(self) -> bool:
        """Check if context has errors"""
        return len(self.errors) > 0

class ParserFactory:
    """Factory for creating parsers"""
    
    @staticmethod
    def create_parser(
        dialect: str,
        context: Optional[QueryContext] = None
    ) -> Parser:
        """Create a parser for the specified dialect"""
        context = context or QueryContext()
        
        if dialect.lower() == "sql":
            from .query_parser_sql import SQLParser
            return SQLParser(context)
        elif dialect.lower() == "nosql":
            from .query_parser_nosql import NoSQLParser
            return NoSQLParser(context)
        else:
            raise ValueError(f"Unsupported dialect: {dialect}")

class ParserRegistry:
    """Registry for parser implementations"""
    
    _parsers: Dict[str, type] = {}
    
    @classmethod
    def register(cls, dialect: str, parser_class: type):
        """Register a parser implementation"""
        cls._parsers[dialect.lower()] = parser_class
        
    @classmethod
    def get_parser(
        cls,
        dialect: str,
        context: Optional[QueryContext] = None
    ) -> Parser:
        """Get a parser instance for the dialect"""
        parser_class = cls._parsers.get(dialect.lower())
        if not parser_class:
            raise ValueError(f"No parser registered for dialect: {dialect}")
            
        return parser_class(context or QueryContext())

# Register built-in parsers
from .query_parser_sql import SQLParser
from .query_parser_nosql import NoSQLParser

ParserRegistry.register("sql", SQLParser)
ParserRegistry.register("nosql", NoSQLParser) 