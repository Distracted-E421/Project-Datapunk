from typing import Dict, List, Any, Set, Optional, Union
import numpy as np
from sqlalchemy.sql import text
from .postgres import PostgresAdapter
from .base import DataSourceType, QueryError

class PgVectorAdapter(PostgresAdapter):
    """Adapter for PostgreSQL with pgvector extension for vector operations."""
    
    def __init__(self, name: str, connection_string: str):
        super().__init__(name, connection_string)
        self.source_type = DataSourceType.VECTOR
        
    def connect(self) -> None:
        """Establish connection and verify pgvector extension."""
        super().connect()
        
        if "vector" not in self._available_extensions:
            raise QueryError("pgvector extension not available")
            
    def create_vector_table(self, table_name: str, dim: int,
                          extra_columns: Optional[Dict[str, str]] = None) -> None:
        """Create a table with vector column."""
        columns = [f"id SERIAL PRIMARY KEY",
                  f"embedding vector({dim})"]
                  
        if extra_columns:
            for name, type_ in extra_columns.items():
                columns.append(f"{name} {type_}")
                
        sql = f"""
        CREATE TABLE {table_name} (
            {', '.join(columns)}
        );
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def create_vector_index(self, table_name: str, column_name: str = "embedding",
                          index_type: str = "ivfflat", lists: int = 100) -> None:
        """Create a vector similarity search index."""
        if index_type not in ["ivfflat", "hnsw"]:
            raise ValueError("Index type must be 'ivfflat' or 'hnsw'")
            
        index_name = f"{table_name}_{column_name}_idx"
        
        if index_type == "ivfflat":
            sql = f"""
            CREATE INDEX {index_name} ON {table_name}
            USING ivfflat ({column_name} vector_l2_ops)
            WITH (lists = {lists});
            """
        else:  # hnsw
            sql = f"""
            CREATE INDEX {index_name} ON {table_name}
            USING hnsw ({column_name} vector_l2_ops);
            """
            
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def insert_vectors(self, table_name: str, vectors: List[List[float]],
                      extra_data: Optional[List[Dict[str, Any]]] = None) -> None:
        """Insert vectors into the table."""
        if extra_data and len(vectors) != len(extra_data):
            raise ValueError("vectors and extra_data must have same length")
            
        values = []
        for i, vector in enumerate(vectors):
            value = f"(ARRAY{vector}::vector"
            if extra_data:
                extras = extra_data[i]
                value += ", " + ", ".join(str(v) for v in extras.values())
            value += ")"
            values.append(value)
            
        columns = ["embedding"]
        if extra_data:
            columns.extend(extra_data[0].keys())
            
        sql = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES {', '.join(values)};
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def execute_query(self, query: Any) -> List[Dict[str, Any]]:
        """Execute vector query with similarity search."""
        if isinstance(query, dict) and query.get("type") == "vector":
            return self._execute_vector_query(query)
        return super().execute_query(query)
        
    def _execute_vector_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute specialized vector query."""
        table_name = query["table"]
        vector = query["vector"]
        k = query.get("k", 10)  # Number of nearest neighbors
        distance = query.get("distance", "l2")  # l2 or cosine
        filter_conditions = query.get("filter", "")
        
        # Choose distance operator
        if distance == "l2":
            operator = "<->"
        elif distance == "cosine":
            operator = "<=>"
        else:
            raise ValueError("Distance must be 'l2' or 'cosine'")
            
        # Build query
        sql = f"""
        SELECT *,
            embedding {operator} ARRAY{vector}::vector as distance
        FROM {table_name}
        """
        
        if filter_conditions:
            sql += f"\nWHERE {filter_conditions}"
            
        sql += f"\nORDER BY embedding {operator} ARRAY{vector}::vector"
        sql += f"\nLIMIT {k}"
        
        return self._execute_raw_sql(sql)
        
    def bulk_vector_search(self, table_name: str, vectors: List[List[float]],
                          k: int = 10, batch_size: int = 100) -> List[List[Dict[str, Any]]]:
        """Perform bulk nearest neighbor search."""
        results = []
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            batch_results = []
            
            # Build batch query
            value_list = [f"ARRAY{v}::vector" for v in batch]
            sql = f"""
            WITH query_vectors AS (
                SELECT unnest(ARRAY[{', '.join(value_list)}]) as qv
            )
            SELECT t.*, qv as query_vector,
                   t.embedding <-> qv as distance
            FROM {table_name} t
            CROSS JOIN query_vectors qv
            ORDER BY qv, distance
            LIMIT {k * len(batch)};
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                
                # Group results by query vector
                current_results = []
                current_vector = None
                
                for row in result:
                    row_dict = dict(row)
                    vector = row_dict.pop("query_vector")
                    
                    if current_vector is None:
                        current_vector = vector
                        
                    if vector != current_vector:
                        batch_results.append(current_results)
                        current_results = []
                        current_vector = vector
                        
                    current_results.append(row_dict)
                    
                if current_results:
                    batch_results.append(current_results)
                    
            results.extend(batch_results)
            
        return results
        
    def get_capabilities(self) -> Set[str]:
        """Get pgvector capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update({
            "vector_storage",
            "vector_search",
            "nearest_neighbors",
            "similarity_search",
            "ivf_index",
            "hnsw_index"
        })
        return capabilities
        
    def get_vector_stats(self, table_name: str) -> Dict[str, Any]:
        """Get statistics about vector storage."""
        sql = f"""
        SELECT
            (SELECT COUNT(*) FROM {table_name}) as total_vectors,
            (SELECT ARRAY_LENGTH(embedding, 1) FROM {table_name} LIMIT 1) as dimensions,
            pg_size_pretty(pg_total_relation_size('{table_name}')) as total_size,
            (
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE tablename = '{table_name}'
                AND indexdef LIKE '%vector%'
            ) as vector_indexes
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(sql)).fetchone()
            return dict(result) if result else {} 