from typing import Dict, List, Any, Set, Optional, Union
import sqlalchemy as sa
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from .postgres import PostgresAdapter
from .base import DataSourceType, QueryError

class TimescaleAdapter(PostgresAdapter):
    """Adapter for TimescaleDB with time series optimizations."""
    
    def __init__(self, name: str, connection_string: str):
        super().__init__(name, connection_string)
        self.source_type = DataSourceType.TIME_SERIES
        
    def connect(self) -> None:
        """Establish connection and verify TimescaleDB extension."""
        super().connect()
        
        if "timescaledb" not in self._available_extensions:
            raise QueryError("TimescaleDB extension not available")
            
    def create_hypertable(self, table_name: str, time_column: str,
                         chunk_interval: Union[str, timedelta] = "1 day",
                         partitioning_column: Optional[str] = None,
                         number_partitions: Optional[int] = None) -> None:
        """Convert a regular table to a TimescaleDB hypertable."""
        if isinstance(chunk_interval, timedelta):
            interval = f"{chunk_interval.total_seconds()} seconds"
        else:
            interval = chunk_interval
            
        sql = f"""
        SELECT create_hypertable(
            '{table_name}', '{time_column}',
            chunk_time_interval => interval '{interval}'
        """
        
        if partitioning_column and number_partitions:
            sql += f", partitioning_column => '{partitioning_column}', "
            sql += f"number_partitions => {number_partitions}"
            
        sql += ");"
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def add_compression_policy(self, table_name: str,
                             compress_after: Union[str, timedelta] = "7 days",
                             segment_by: Optional[List[str]] = None,
                             orderby: Optional[List[str]] = None) -> None:
        """Add automatic compression policy to a hypertable."""
        if isinstance(compress_after, timedelta):
            interval = f"{compress_after.total_seconds()} seconds"
        else:
            interval = compress_after
            
        sql = f"""
        ALTER TABLE {table_name} SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = '{",".join(segment_by) if segment_by else ""}',
            timescaledb.compress_orderby = '{",".join(orderby) if orderby else ""}'
        );
        
        SELECT add_compression_policy(
            '{table_name}', 
            INTERVAL '{interval}'
        );
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def add_retention_policy(self, table_name: str,
                           older_than: Union[str, timedelta]) -> None:
        """Add data retention policy to a hypertable."""
        if isinstance(older_than, timedelta):
            interval = f"{older_than.total_seconds()} seconds"
        else:
            interval = older_than
            
        sql = f"""
        SELECT add_retention_policy(
            '{table_name}',
            INTERVAL '{interval}'
        );
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def execute_query(self, query: Any) -> List[Dict[str, Any]]:
        """Execute TimescaleDB query with time series optimizations."""
        if isinstance(query, dict) and query.get("type") == "time_series":
            return self._execute_time_series_query(query)
        return super().execute_query(query)
        
    def _execute_time_series_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute specialized time series query."""
        table_name = query["table"]
        time_column = query["time_column"]
        aggregates = query.get("aggregates", [])
        group_by = query.get("group_by", [])
        bucket_width = query.get("bucket_width", "1 hour")
        
        # Build time bucket query
        select_items = [
            f"time_bucket('{bucket_width}', {time_column}) as bucket"
        ]
        
        for agg in aggregates:
            func = agg["function"]
            col = agg["column"]
            alias = agg.get("alias", f"{func}_{col}")
            select_items.append(f"{func}({col}) as {alias}")
            
        if group_by:
            select_items.extend(group_by)
            
        sql = f"""
        SELECT {', '.join(select_items)}
        FROM {table_name}
        """
        
        # Add time range conditions
        if "start_time" in query:
            sql += f"\nWHERE {time_column} >= '{query['start_time']}'"
            if "end_time" in query:
                sql += f"\nAND {time_column} < '{query['end_time']}'"
                
        # Add grouping
        group_items = ["bucket"]
        if group_by:
            group_items.extend(group_by)
        sql += f"\nGROUP BY {', '.join(group_items)}"
        
        # Add ordering
        sql += "\nORDER BY bucket"
        
        return self._execute_raw_sql(sql)
        
    def get_capabilities(self) -> Set[str]:
        """Get TimescaleDB capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update({
            "time_series",
            "continuous_aggregates",
            "data_retention",
            "compression",
            "automated_chunking",
            "time_buckets",
            "gap_filling",
            "interpolation"
        })
        return capabilities
        
    def get_hypertable_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a hypertable."""
        sql = f"""
        SELECT h.*, (
            SELECT COUNT(*)
            FROM timescaledb_information.chunks c
            WHERE c.hypertable_name = '{table_name}'
        ) as chunk_count,
        COALESCE((
            SELECT SUM(pg_total_relation_size(format('%I.%I', c.schema_name, c.table_name)))
            FROM timescaledb_information.chunks c
            WHERE c.hypertable_name = '{table_name}'
        ), 0) as total_bytes
        FROM timescaledb_information.hypertables h
        WHERE h.hypertable_name = '{table_name}';
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(sql)).fetchone()
            if not result:
                raise QueryError(f"Table {table_name} is not a hypertable")
            return dict(result)
            
    def get_chunk_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get information about chunks in a hypertable."""
        sql = f"""
        SELECT c.*,
            pg_total_relation_size(format('%I.%I', c.schema_name, c.table_name)) as bytes,
            pg_size_pretty(pg_total_relation_size(format('%I.%I', c.schema_name, c.table_name))) as size
        FROM timescaledb_information.chunks c
        WHERE c.hypertable_name = '{table_name}'
        ORDER BY c.range_start;
        """
        
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(sql))]
            
    def get_compression_stats(self, table_name: str) -> Dict[str, Any]:
        """Get compression statistics for a hypertable."""
        sql = f"""
        SELECT
            h.table_name,
            h.compression_enabled,
            COUNT(c.*) as total_chunks,
            COUNT(c.*) FILTER (WHERE c.is_compressed) as compressed_chunks,
            SUM(CASE WHEN c.is_compressed 
                THEN c.compressed_total_bytes 
                ELSE c.uncompressed_total_bytes 
            END) as total_bytes,
            SUM(c.uncompressed_total_bytes) as uncompressed_bytes,
            CASE WHEN SUM(c.uncompressed_total_bytes) > 0
                THEN (1 - (SUM(CASE WHEN c.is_compressed 
                    THEN c.compressed_total_bytes 
                    ELSE c.uncompressed_total_bytes 
                END)::float / 
                SUM(c.uncompressed_total_bytes))) * 100
                ELSE 0
            END as compression_ratio
        FROM timescaledb_information.hypertables h
        LEFT JOIN timescaledb_information.chunks c ON h.table_name = c.hypertable_name
        WHERE h.table_name = '{table_name}'
        GROUP BY h.table_name, h.compression_enabled;
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(sql)).fetchone()
            return dict(result) if result else {} 