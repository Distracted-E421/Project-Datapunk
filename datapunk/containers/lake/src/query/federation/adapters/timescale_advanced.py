from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from .timescale import TimescaleAdapter

class AdvancedTimescaleAdapter(TimescaleAdapter):
    """Advanced TimescaleDB adapter with specialized operations."""
    
    def create_continuous_aggregate(self, view_name: str, table_name: str,
                                  time_column: str, bucket_width: str,
                                  aggregates: List[Dict[str, str]],
                                  group_by: Optional[List[str]] = None,
                                  with_data: bool = True,
                                  refresh_policy: Optional[str] = None) -> None:
        """Create a continuous aggregate view."""
        # Build aggregate expressions
        agg_exprs = []
        for agg in aggregates:
            func = agg["function"]
            col = agg["column"]
            alias = agg.get("alias", f"{func}_{col}")
            agg_exprs.append(f"{func}({col}) as {alias}")
            
        # Build group by clause
        group_items = [f"time_bucket('{bucket_width}', {time_column}) as bucket"]
        if group_by:
            group_items.extend(group_by)
            
        sql = f"""
        CREATE MATERIALIZED VIEW {view_name}
        WITH (timescaledb.continuous) AS
        SELECT {', '.join(group_items)},
               {', '.join(agg_exprs)}
        FROM {table_name}
        GROUP BY {', '.join(group_items)}
        WITH {'DATA' if with_data else 'NO DATA'};
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
        if refresh_policy:
            self.add_refresh_policy(view_name, refresh_policy)
            
    def add_refresh_policy(self, view_name: str, refresh_interval: str) -> None:
        """Add refresh policy to continuous aggregate."""
        sql = f"""
        SELECT add_continuous_aggregate_policy('{view_name}',
            start_offset => INTERVAL '1 month',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '{refresh_interval}'
        );
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def create_cagg_policy(self, view_name: str, start_offset: str,
                          end_offset: str, schedule_interval: str) -> None:
        """Create a policy for continuous aggregate maintenance."""
        sql = f"""
        SELECT add_continuous_aggregate_policy(
            continuous_aggregate => '{view_name}',
            start_offset => INTERVAL '{start_offset}',
            end_offset => INTERVAL '{end_offset}',
            schedule_interval => INTERVAL '{schedule_interval}'
        );
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def create_job(self, job_name: str, schedule_interval: str,
                   config: Dict[str, Any]) -> None:
        """Create a background job."""
        sql = f"""
        SELECT add_job(
            proc => {config['procedure']},
            schedule_interval => INTERVAL '{schedule_interval}',
            config => '{json.dumps(config)}'::jsonb,
            initial_start => {config.get('initial_start', 'NULL')},
            scheduled => {config.get('scheduled', 'true')}
        );
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            
    def execute_time_bucket_gapfill(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute time bucket query with gap filling."""
        table_name = query["table"]
        time_column = query["time_column"]
        bucket_width = query.get("bucket_width", "1 hour")
        start_time = query["start_time"]
        end_time = query["end_time"]
        aggregates = query.get("aggregates", [])
        group_by = query.get("group_by", [])
        
        # Build select items
        select_items = [
            f"time_bucket_gapfill('{bucket_width}', {time_column}, "
            f"'{start_time}'::timestamp, '{end_time}'::timestamp) as bucket"
        ]
        
        # Add aggregates with locf and interpolation
        for agg in aggregates:
            func = agg["function"]
            col = agg["column"]
            alias = agg.get("alias", f"{func}_{col}")
            fill_type = agg.get("fill", "null")
            
            if fill_type == "locf":
                select_items.append(f"locf({func}({col})) as {alias}")
            elif fill_type == "interpolate":
                select_items.append(f"interpolate({func}({col})) as {alias}")
            else:
                select_items.append(f"{func}({col}) as {alias}")
                
        # Build query
        sql = f"""
        SELECT {', '.join(select_items)}
        FROM {table_name}
        WHERE {time_column} BETWEEN '{start_time}' AND '{end_time}'
        GROUP BY bucket
        ORDER BY bucket;
        """
        
        return self._execute_raw_sql(sql)
        
    def get_chunks_by_time_range(self, table_name: str,
                                start_time: datetime,
                                end_time: datetime) -> List[Dict[str, Any]]:
        """Get chunk information for a specific time range."""
        sql = f"""
        SELECT c.*,
            pg_size_pretty(pg_total_relation_size(
                format('%I.%I', c.schema_name, c.table_name)
            )) as size,
            pg_total_relation_size(
                format('%I.%I', c.schema_name, c.table_name)
            ) as bytes
        FROM timescaledb_information.chunks c
        WHERE c.hypertable_name = '{table_name}'
        AND c.range_start >= '{start_time}'
        AND c.range_end <= '{end_time}'
        ORDER BY c.range_start;
        """
        
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(sql))]
            
    def get_retention_stats(self, table_name: str) -> Dict[str, Any]:
        """Get statistics about data retention."""
        sql = f"""
        SELECT
            h.table_name,
            h.compression_enabled,
            p.schedule_interval as retention_schedule,
            p.drop_after as retention_period,
            (
                SELECT COUNT(*)
                FROM timescaledb_information.chunks c
                WHERE c.hypertable_name = h.table_name
                AND c.is_compressed
            ) as compressed_chunks,
            (
                SELECT COUNT(*)
                FROM timescaledb_information.chunks c
                WHERE c.hypertable_name = h.table_name
                AND NOT c.is_compressed
            ) as uncompressed_chunks,
            (
                SELECT MIN(range_start)
                FROM timescaledb_information.chunks c
                WHERE c.hypertable_name = h.table_name
            ) as oldest_data,
            (
                SELECT MAX(range_end)
                FROM timescaledb_information.chunks c
                WHERE c.hypertable_name = h.table_name
            ) as newest_data
        FROM timescaledb_information.hypertables h
        LEFT JOIN timescaledb_information.jobs j
            ON j.hypertable_name = h.table_name
        LEFT JOIN timescaledb_information.policies p
            ON p.hypertable_name = h.table_name
        WHERE h.table_name = '{table_name}';
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(sql)).fetchone()
            return dict(result) if result else {} 