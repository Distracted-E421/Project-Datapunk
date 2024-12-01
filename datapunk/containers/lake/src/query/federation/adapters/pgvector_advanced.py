from typing import Dict, List, Any, Optional, Union
import numpy as np
from sqlalchemy.sql import text
from .pgvector import PgVectorAdapter

class AdvancedPgVectorAdapter(PgVectorAdapter):
    """Advanced pgvector adapter with specialized operations."""
    
    def create_ann_index(self, table_name: str, column_name: str = "embedding",
                        index_type: str = "ivfflat", params: Dict[str, Any] = None) -> None:
        """Create an approximate nearest neighbor index with advanced parameters."""
        if index_type not in ["ivfflat", "hnsw"]:
            raise ValueError("Index type must be 'ivfflat' or 'hnsw'")
            
        index_name = f"{table_name}_{column_name}_ann_idx"
        
        if index_type == "ivfflat":
            lists = params.get("lists", 100)
            sql = f"""
            CREATE INDEX {index_name} ON {table_name}
            USING ivfflat ({column_name} vector_l2_ops)
            WITH (lists = {lists});
            """
        else:  # hnsw
            m = params.get("m", 16)  # Max number of connections
            ef_construction = params.get("ef_construction", 64)
            sql = f"""
            CREATE INDEX {index_name} ON {table_name}
            USING hnsw ({column_name} vector_l2_ops)
            WITH (m = {m}, ef_construction = {ef_construction});
            """
            
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def create_hybrid_index(self, table_name: str, vector_column: str,
                           filter_columns: List[str]) -> None:
        """Create hybrid index combining vector and scalar columns."""
        index_name = f"{table_name}_hybrid_idx"
        
        # Create composite index
        columns = [f"{vector_column} vector_l2_ops"]
        columns.extend(filter_columns)
        
        sql = f"""
        CREATE INDEX {index_name} ON {table_name}
        USING ivfflat ({', '.join(columns)});
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def execute_hybrid_search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute hybrid search combining vector similarity and scalar filters."""
        table_name = query["table"]
        vector = query["vector"]
        k = query.get("k", 10)
        filters = query.get("filters", {})
        rerank = query.get("rerank", False)
        
        # Build filter conditions
        where_clauses = []
        for col, value in filters.items():
            if isinstance(value, (list, tuple)):
                where_clauses.append(f"{col} BETWEEN {value[0]} AND {value[1]}")
            else:
                where_clauses.append(f"{col} = {value}")
                
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        if rerank:
            # Two-phase search: broad ANN search followed by exact reranking
            sql = f"""
            WITH candidates AS (
                SELECT *,
                    embedding <-> ARRAY{vector}::vector as approx_distance
                FROM {table_name}
                {where_sql}
                ORDER BY embedding <-> ARRAY{vector}::vector
                LIMIT {k * 4}
            )
            SELECT *,
                embedding <-> ARRAY{vector}::vector as exact_distance
            FROM candidates
            ORDER BY exact_distance
            LIMIT {k};
            """
        else:
            sql = f"""
            SELECT *,
                embedding <-> ARRAY{vector}::vector as distance
            FROM {table_name}
            {where_sql}
            ORDER BY embedding <-> ARRAY{vector}::vector
            LIMIT {k};
            """
            
        return self._execute_raw_sql(sql)
        
    def execute_batch_upsert(self, table_name: str,
                            vectors: List[List[float]],
                            metadata: List[Dict[str, Any]],
                            key_columns: List[str]) -> None:
        """Perform batch upsert of vectors with metadata."""
        if len(vectors) != len(metadata):
            raise ValueError("vectors and metadata must have same length")
            
        # Prepare column names
        vector_col = "embedding"
        meta_cols = list(metadata[0].keys())
        all_cols = [vector_col] + meta_cols
        
        # Prepare values
        values = []
        for i, vector in enumerate(vectors):
            meta = metadata[i]
            value_items = [f"ARRAY{vector}::vector"]
            value_items.extend(str(meta[col]) for col in meta_cols)
            values.append(f"({', '.join(value_items)})")
            
        # Build upsert query
        sql = f"""
        INSERT INTO {table_name} ({', '.join(all_cols)})
        VALUES {', '.join(values)}
        ON CONFLICT ({', '.join(key_columns)})
        DO UPDATE SET
        {', '.join(f"{col} = EXCLUDED.{col}"
                   for col in all_cols if col not in key_columns)};
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def compute_centroid(self, table_name: str,
                        group_column: str) -> Dict[str, List[float]]:
        """Compute vector centroids for groups."""
        sql = f"""
        SELECT {group_column},
               (array_agg(embedding))[1:10] as sample_vectors,
               avg(embedding)::vector as centroid
        FROM {table_name}
        GROUP BY {group_column};
        """
        
        with self.engine.connect() as conn:
            results = conn.execute(text(sql))
            return {row[group_column]: list(row["centroid"]) for row in results}
            
    def find_outliers(self, table_name: str, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Find vector outliers using distance-based method."""
        sql = f"""
        WITH stats AS (
            SELECT avg(embedding) as centroid,
                   percentile_cont(0.75) WITHIN GROUP (
                       ORDER BY embedding <-> avg(embedding) OVER ()
                   ) as q3,
                   percentile_cont(0.25) WITHIN GROUP (
                       ORDER BY embedding <-> avg(embedding) OVER ()
                   ) as q1
            FROM {table_name}
        )
        SELECT t.*,
               embedding <-> stats.centroid as distance,
               (stats.q3 - stats.q1) * {threshold} as threshold
        FROM {table_name} t, stats
        WHERE embedding <-> stats.centroid > (stats.q3 - stats.q1) * {threshold}
        ORDER BY embedding <-> stats.centroid DESC;
        """
        
        return self._execute_raw_sql(sql)
        
    def get_index_stats(self, table_name: str) -> Dict[str, Any]:
        """Get detailed statistics about vector indexes."""
        sql = f"""
        SELECT
            i.indexname,
            i.indexdef,
            pg_size_pretty(pg_relation_size(i.indexname::regclass)) as size,
            (SELECT COUNT(*) FROM {table_name}) as total_vectors,
            (
                SELECT COUNT(DISTINCT substring(vector_dims 
                FROM 'vector\\((\\d+)\\)' FOR 1)::integer)
                FROM pg_attribute a
                JOIN pg_type t ON a.atttypid = t.oid
                WHERE a.attrelid = '{table_name}'::regclass
                AND t.typname = 'vector'
            ) as dimensions,
            (
                SELECT amname
                FROM pg_index x
                JOIN pg_class c ON c.oid = x.indexrelid
                JOIN pg_am am ON am.oid = c.relam
                WHERE c.relname = i.indexname
            ) as index_method
        FROM pg_indexes i
        WHERE i.tablename = '{table_name}'
        AND i.indexdef LIKE '%vector%';
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(sql)).fetchone()
            return dict(result) if result else {} 