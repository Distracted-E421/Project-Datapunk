import time
from typing import Dict, List, Any, Set, Optional
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
from psycopg2.extras import Json, DictCursor
from .base import (
    DataSourceAdapter,
    DataSourceType,
    AdapterMetrics,
    ConnectionError,
    QueryError,
    SchemaError,
    standardize_schema
)

class PostgresAdapter(DataSourceAdapter):
    """Adapter for PostgreSQL with advanced features support."""
    
    def __init__(self, name: str, connection_string: str):
        super().__init__(name, DataSourceType.RELATIONAL)
        self.connection_string = connection_string
        self.engine: Optional[sa.Engine] = None
        self.metadata: Optional[sa.MetaData] = None
        
    def connect(self) -> None:
        """Establish connection to PostgreSQL."""
        try:
            self.engine = sa.create_engine(
                self.connection_string,
                json_serializer=lambda obj: Json(obj),
                connect_args={'cursor_factory': DictCursor}
            )
            self.metadata = sa.MetaData()
            self.metadata.reflect(bind=self.engine)
            
            # Test connection and check extensions
            with self.engine.connect() as conn:
                extensions = conn.execute(text(
                    "SELECT extname FROM pg_extension"
                )).fetchall()
                self._available_extensions = {ext[0] for ext in extensions}
                
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {str(e)}")
            
    def disconnect(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            
    def execute_query(self, query: Any) -> List[Dict[str, Any]]:
        """Execute PostgreSQL query."""
        if not self.engine:
            raise ConnectionError("Not connected to database")
            
        try:
            start_time = time.time()
            
            # Handle different query types
            if isinstance(query, str):
                result = self._execute_raw_sql(query)
            elif isinstance(query, sa.sql.Select):
                result = self._execute_sqlalchemy(query)
            elif isinstance(query, dict):
                result = self._execute_json_query(query)
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
            
    def _execute_json_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute JSON/JSONB query."""
        table_name = query.get("table")
        conditions = query.get("conditions", {})
        
        # Build JSON/JSONB query
        table = self.metadata.tables[table_name]
        stmt = sa.select(table)
        
        for field, value in conditions.items():
            if isinstance(value, dict):
                # Handle JSON path operations
                path = value.get("path", [])
                operator = value.get("operator", "=")
                compare_value = value.get("value")
                
                if operator == "contains":
                    stmt = stmt.where(
                        table.c[field].contains(compare_value)
                    )
                elif operator == "contained_by":
                    stmt = stmt.where(
                        table.c[field].contained_by(compare_value)
                    )
                elif operator == "has_key":
                    stmt = stmt.where(
                        table.c[field].has_key(compare_value)
                    )
                elif path:
                    # JSON path query
                    path_expr = f"$.{'.'.join(path)}"
                    stmt = stmt.where(
                        table.c[field][path_expr].astext == str(compare_value)
                    )
            else:
                stmt = stmt.where(table.c[field] == value)
                
        return self._execute_sqlalchemy(stmt)
        
    def get_capabilities(self) -> Set[str]:
        """Get PostgreSQL capabilities."""
        capabilities = {
            "select", "insert", "update", "delete",
            "join", "group", "order", "having",
            "aggregate", "subquery", "transaction",
            "json", "jsonb", "array", "hstore",
            "full_text_search", "window_functions"
        }
        
        # Add extension-specific capabilities
        if "postgis" in self._available_extensions:
            capabilities.add("geospatial")
        if "pg_trgm" in self._available_extensions:
            capabilities.add("fuzzy_search")
            
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
                    "foreign_keys": self._get_foreign_key_info(table),
                    "constraints": self._get_constraint_info(table)
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
                "autoincrement": column.autoincrement,
                "is_json": isinstance(column.type, (postgresql.JSON, postgresql.JSONB))
            }
        return columns
        
    def _get_index_info(self, table: sa.Table) -> List[Dict[str, Any]]:
        """Get index information for a table."""
        indexes = []
        for index in table.indexes:
            indexes.append({
                "name": index.name,
                "columns": [col.name for col in index.columns],
                "unique": index.unique,
                "type": index.kwargs.get("postgresql_using", "btree")
            })
        return indexes
        
    def _get_foreign_key_info(self, table: sa.Table) -> List[Dict[str, Any]]:
        """Get foreign key information for a table."""
        foreign_keys = []
        for fk in table.foreign_keys:
            foreign_keys.append({
                "column": fk.parent.name,
                "referred_table": fk.column.table.name,
                "referred_column": fk.column.name,
                "on_delete": fk.ondelete,
                "on_update": fk.onupdate
            })
        return foreign_keys
        
    def _get_constraint_info(self, table: sa.Table) -> List[Dict[str, Any]]:
        """Get constraint information for a table."""
        constraints = []
        for const in table.constraints:
            if not isinstance(const, sa.PrimaryKeyConstraint):
                constraints.append({
                    "name": const.name,
                    "type": type(const).__name__,
                    "columns": [col.name for col in const.columns]
                    if hasattr(const, "columns") else []
                })
        return constraints 