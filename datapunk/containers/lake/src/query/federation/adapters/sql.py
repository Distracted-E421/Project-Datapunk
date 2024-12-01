import time
from typing import Dict, List, Any, Set, Optional
import sqlalchemy as sa
from sqlalchemy.sql import text
from .base import (
    DataSourceAdapter,
    DataSourceType,
    AdapterMetrics,
    ConnectionError,
    QueryError,
    SchemaError,
    standardize_schema
)

class SQLAdapter(DataSourceAdapter):
    """Adapter for SQL databases."""
    
    def __init__(self, name: str, connection_string: str):
        super().__init__(name, DataSourceType.RELATIONAL)
        self.connection_string = connection_string
        self.engine: Optional[sa.Engine] = None
        self.metadata: Optional[sa.MetaData] = None
        
    def connect(self) -> None:
        """Establish connection to SQL database."""
        try:
            self.engine = sa.create_engine(self.connection_string)
            self.metadata = sa.MetaData()
            self.metadata.reflect(bind=self.engine)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SQL database: {str(e)}")
            
    def disconnect(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            
    def execute_query(self, query: Any) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        if not self.engine:
            raise ConnectionError("Not connected to database")
            
        try:
            start_time = time.time()
            
            # Handle different query types
            if isinstance(query, str):
                result = self._execute_raw_sql(query)
            elif isinstance(query, sa.sql.Select):
                result = self._execute_sqlalchemy(query)
            else:
                raise QueryError(f"Unsupported query type: {type(query)}")
                
            # Update metrics
            execution_time = time.time() - start_time
            self.metrics.query_count += 1
            self.metrics.total_execution_time += execution_time
            self.metrics.rows_processed += len(result)
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            raise QueryError(f"Query execution failed: {str(e)}")
            
    def _execute_raw_sql(self, query: str) -> List[Dict[str, Any]]:
        """Execute raw SQL query."""
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return [dict(row) for row in result]
            
    def _execute_sqlalchemy(self, query: sa.sql.Select) -> List[Dict[str, Any]]:
        """Execute SQLAlchemy query."""
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row) for row in result]
            
    def get_capabilities(self) -> Set[str]:
        """Get SQL database capabilities."""
        capabilities = {
            "select", "insert", "update", "delete",
            "join", "group", "order", "having",
            "aggregate", "subquery", "transaction"
        }
        
        # Add dialect-specific capabilities
        if self.engine:
            dialect = self.engine.dialect.name
            if dialect == "postgresql":
                capabilities.update({
                    "array", "json", "window", "materialized_view",
                    "full_text_search", "geospatial"
                })
            elif dialect == "mysql":
                capabilities.update({
                    "full_text_search", "spatial"
                })
                
        return capabilities
        
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information."""
        if not self.metadata:
            raise SchemaError("Not connected to database")
            
        try:
            schema = {}
            for table_name, table in self.metadata.tables.items():
                schema[table_name] = {
                    "columns": self._get_column_info(table),
                    "primary_key": [col.name for col in table.primary_key],
                    "indexes": self._get_index_info(table),
                    "foreign_keys": self._get_foreign_key_info(table)
                }
                
            return standardize_schema(schema)
            
        except Exception as e:
            raise SchemaError(f"Failed to retrieve schema: {str(e)}")
            
    def _get_column_info(self, table: sa.Table) -> Dict[str, Dict[str, Any]]:
        """Get column information for a table."""
        columns = {}
        for column in table.columns:
            columns[column.name] = {
                "type": str(column.type),
                "nullable": column.nullable,
                "default": str(column.default) if column.default else None,
                "primary_key": column.primary_key,
                "autoincrement": column.autoincrement
            }
        return columns
        
    def _get_index_info(self, table: sa.Table) -> List[Dict[str, Any]]:
        """Get index information for a table."""
        indexes = []
        for index in table.indexes:
            indexes.append({
                "name": index.name,
                "columns": [col.name for col in index.columns],
                "unique": index.unique
            })
        return indexes
        
    def _get_foreign_key_info(self, table: sa.Table) -> List[Dict[str, Any]]:
        """Get foreign key information for a table."""
        foreign_keys = []
        for fk in table.foreign_keys:
            foreign_keys.append({
                "column": fk.parent.name,
                "referred_table": fk.column.table.name,
                "referred_column": fk.column.name
            })
        return foreign_keys 