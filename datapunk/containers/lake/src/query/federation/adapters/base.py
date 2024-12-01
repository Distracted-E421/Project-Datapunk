from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from ..planner import DataSource, DataSourceType

@dataclass
class AdapterMetrics:
    """Metrics collected by data source adapters."""
    query_count: int = 0
    total_execution_time: float = 0.0
    rows_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0

class DataSourceAdapter(ABC):
    """Base class for data source adapters."""
    
    def __init__(self, name: str, source_type: DataSourceType):
        self.name = name
        self.source_type = source_type
        self.metrics = AdapterMetrics()
        
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to data source."""
        pass
        
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to data source."""
        pass
        
    @abstractmethod
    def execute_query(self, query: Any) -> List[Dict[str, Any]]:
        """Execute a query on the data source."""
        pass
        
    @abstractmethod
    def get_capabilities(self) -> Set[str]:
        """Get supported capabilities of this data source."""
        pass
        
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get schema information from the data source."""
        pass
        
    def get_metrics(self) -> AdapterMetrics:
        """Get current adapter metrics."""
        return self.metrics
        
    def reset_metrics(self) -> None:
        """Reset adapter metrics."""
        self.metrics = AdapterMetrics()

class AdapterException(Exception):
    """Base exception for adapter-related errors."""
    pass

class ConnectionError(AdapterException):
    """Error establishing connection to data source."""
    pass

class QueryError(AdapterException):
    """Error executing query on data source."""
    pass

class SchemaError(AdapterException):
    """Error retrieving schema information."""
    pass

def validate_query_result(result: List[Dict[str, Any]]) -> bool:
    """Validate query result format."""
    if not isinstance(result, list):
        return False
    return all(isinstance(row, dict) for row in result)

def standardize_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert source-specific schema to standard format."""
    standardized = {}
    for table_name, table_info in schema.items():
        standardized[table_name] = {
            "columns": {},
            "primary_key": table_info.get("primary_key", []),
            "indexes": table_info.get("indexes", [])
        }
        for col_name, col_info in table_info.get("columns", {}).items():
            standardized[table_name]["columns"][col_name] = {
                "type": _standardize_type(col_info.get("type", "unknown")),
                "nullable": col_info.get("nullable", True),
                "default": col_info.get("default", None)
            }
    return standardized

def _standardize_type(source_type: str) -> str:
    """Convert source-specific types to standard types."""
    type_mapping = {
        # SQL types
        "varchar": "string",
        "char": "string",
        "text": "string",
        "int": "integer",
        "integer": "integer",
        "bigint": "integer",
        "float": "float",
        "double": "float",
        "decimal": "decimal",
        "boolean": "boolean",
        "date": "date",
        "timestamp": "timestamp",
        # NoSQL types
        "string": "string",
        "number": "float",
        "bool": "boolean",
        "array": "array",
        "object": "object",
        # Default
        "unknown": "unknown"
    }
    source_type = source_type.lower()
    return type_mapping.get(source_type, "unknown") 