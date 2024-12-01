from typing import Dict, List, Optional, Any, Tuple
import asyncpg
from datetime import datetime
import logging
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.sql import select, func
import numpy as np
from .core import (
    SchemaMetadata, StatisticsMetadata, QualityMetadata,
    QualityMetric, ColumnStats
)

logger = logging.getLogger(__name__)

class MetadataAnalyzer:
    """Analyzes and collects metadata from data sources."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """Initialize the analyzer with database connection."""
        self.connection_config = connection_config
        self.engine = create_engine(
            f"postgresql://{connection_config['user']}:{connection_config['password']}"
            f"@{connection_config['host']}:{connection_config['port']}"
            f"/{connection_config['database']}"
        )
        self.metadata = MetaData()
    
    async def analyze_schema(self, table_name: str) -> SchemaMetadata:
        """Analyze and extract schema metadata."""
        inspector = inspect(self.engine)
        
        # Get table information
        columns = {}
        for col in inspector.get_columns(table_name):
            columns[col['name']] = {
                'type': str(col['type']),
                'nullable': col.get('nullable', True),
                'default': str(col.get('default', None)),
                'primary_key': col['name'] in inspector.get_pk_constraint(table_name)['constrained_columns'],
                'comment': col.get('comment', None)
            }
        
        # Get primary key
        pk_info = inspector.get_pk_constraint(table_name)
        primary_key = pk_info['constrained_columns'] if pk_info else []
        
        # Get foreign keys
        foreign_keys = []
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys.append({
                'constrained_columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns']
            })
        
        # Get indexes
        indexes = []
        for idx in inspector.get_indexes(table_name):
            indexes.append({
                'name': idx['name'],
                'columns': idx['column_names'],
                'unique': idx['unique']
            })
        
        # Get constraints
        constraints = []
        for const in inspector.get_check_constraints(table_name):
            constraints.append({
                'name': const['name'],
                'sqltext': str(const['sqltext'])
            })
        
        return SchemaMetadata(
            name=table_name,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            indexes=indexes,
            constraints=constraints,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1
        )
    
    async def analyze_statistics(self, table_name: str, 
                               sample_size: Optional[int] = None) -> StatisticsMetadata:
        """Analyze and extract statistical metadata."""
        table = Table(table_name, self.metadata, autoload_with=self.engine)
        
        async with asyncpg.create_pool(**self.connection_config) as pool:
            async with pool.acquire() as conn:
                # Get basic table statistics
                stats = await conn.fetchrow(f"""
                    SELECT 
                        pg_total_relation_size($1) as total_bytes,
                        (SELECT reltuples::bigint FROM pg_class WHERE relname = $1) as estimated_rows
                """, table_name)
                
                # Get column statistics
                column_stats = {}
                for column in table.columns:
                    col_stats = await self._analyze_column(conn, table_name, column.name, sample_size)
                    column_stats[column.name] = col_stats
                
                # Get index statistics
                index_stats = await self._analyze_indexes(conn, table_name)
                
                return StatisticsMetadata(
                    table_name=table_name,
                    row_count=stats['estimated_rows'],
                    size_bytes=stats['total_bytes'],
                    last_analyzed=datetime.utcnow(),
                    column_stats=column_stats,
                    index_stats=index_stats,
                    sample_size=sample_size,
                    is_estimate=sample_size is not None
                )
    
    async def _analyze_column(self, conn: asyncpg.Connection, 
                            table_name: str, column_name: str,
                            sample_size: Optional[int]) -> Dict[str, Any]:
        """Analyze statistics for a single column."""
        # Base query for statistics
        stats_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(DISTINCT {column_name}) as distinct_count,
                COUNT(*) FILTER (WHERE {column_name} IS NULL) as null_count
        """
        
        # Add numeric statistics if applicable
        numeric_stats = """
            , MIN({col}) as min_value
            , MAX({col}) as max_value
            , AVG({col}::numeric) as avg_value
            , PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {col}::numeric) as median
            , STDDEV({col}::numeric) as stddev
        """
        
        # Add string statistics if applicable
        string_stats = """
            , MIN(LENGTH({col})) as min_length
            , MAX(LENGTH({col})) as max_length
            , AVG(LENGTH({col})) as avg_length
        """
        
        # Get column type
        type_info = await conn.fetchval("""
            SELECT data_type 
            FROM information_schema.columns
            WHERE table_name = $1 AND column_name = $2
        """, table_name, column_name)
        
        # Build full query based on type
        query = stats_query
        if type_info.lower() in ('integer', 'numeric', 'real', 'double precision'):
            query += numeric_stats.format(col=column_name)
        elif type_info.lower() in ('character varying', 'text'):
            query += string_stats.format(col=column_name)
        
        # Add FROM clause and sampling if needed
        query += f" FROM {table_name}"
        if sample_size:
            query += f" TABLESAMPLE SYSTEM({sample_size})"
        
        # Execute query and get results
        stats = await conn.fetchrow(query)
        
        # Convert to dictionary and add type information
        result = dict(stats)
        result['data_type'] = type_info
        
        return result
    
    async def _analyze_indexes(self, conn: asyncpg.Connection, 
                             table_name: str) -> Dict[str, Any]:
        """Analyze index statistics."""
        stats = await conn.fetch("""
            SELECT
                i.indexname as index_name,
                i.indexdef as definition,
                pg_relation_size(quote_ident(i.indexname)::text) as size_bytes,
                s.idx_scan as scan_count,
                s.idx_tup_read as tuples_read,
                s.idx_tup_fetch as tuples_fetched
            FROM pg_indexes i
            LEFT JOIN pg_stat_user_indexes s 
                ON i.indexname = s.indexrelname
            WHERE i.tablename = $1
        """, table_name)
        
        return {row['index_name']: dict(row) for row in stats}
    
    async def analyze_quality(self, table_name: str) -> QualityMetadata:
        """Analyze and extract data quality metrics."""
        metrics = []
        overall_score = 0.0
        total_weight = 0.0
        
        async with asyncpg.create_pool(**self.connection_config) as pool:
            async with pool.acquire() as conn:
                # Completeness check
                null_metrics = await self._check_null_ratios(conn, table_name)
                metrics.extend(null_metrics)
                
                # Uniqueness check
                unique_metrics = await self._check_uniqueness(conn, table_name)
                metrics.extend(unique_metrics)
                
                # Consistency check
                consistency_metrics = await self._check_consistency(conn, table_name)
                metrics.extend(consistency_metrics)
                
                # Calculate overall score
                for metric in metrics:
                    weight = 1.0  # Can be adjusted based on importance
                    overall_score += metric.metric_value * weight
                    total_weight += weight
                
                if total_weight > 0:
                    overall_score /= total_weight
        
        return QualityMetadata(
            table_name=table_name,
            metrics=metrics,
            last_checked=datetime.utcnow(),
            overall_score=overall_score
        )
    
    async def _check_null_ratios(self, conn: asyncpg.Connection, 
                                table_name: str) -> List[QualityMetric]:
        """Check null ratios for all columns."""
        columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = $1
        """, table_name)
        
        metrics = []
        for col in columns:
            null_ratio = await conn.fetchval(f"""
                SELECT COALESCE(
                    (COUNT(*) FILTER (WHERE {col['column_name']} IS NULL))::float / 
                    NULLIF(COUNT(*), 0),
                    0
                )
                FROM {table_name}
            """)
            
            completeness = 1.0 - null_ratio
            metrics.append(QualityMetric(
                metric_name=f"completeness_{col['column_name']}",
                metric_value=completeness,
                threshold=0.95,
                status="passed" if completeness >= 0.95 else "warning",
                timestamp=datetime.utcnow()
            ))
        
        return metrics
    
    async def _check_uniqueness(self, conn: asyncpg.Connection, 
                               table_name: str) -> List[QualityMetric]:
        """Check uniqueness for columns that should be unique."""
        metrics = []
        
        # Get unique constraints and indexes
        unique_cols = await conn.fetch("""
            SELECT a.attname as column_name
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid 
                AND a.attnum = ANY(i.indkey)
            WHERE i.indisunique AND i.indrelid = $1::regclass
        """, table_name)
        
        for col in unique_cols:
            duplicate_count = await conn.fetchval(f"""
                SELECT COUNT(*) - COUNT(DISTINCT {col['column_name']})
                FROM {table_name}
                WHERE {col['column_name']} IS NOT NULL
            """)
            
            uniqueness = 1.0 if duplicate_count == 0 else 0.0
            metrics.append(QualityMetric(
                metric_name=f"uniqueness_{col['column_name']}",
                metric_value=uniqueness,
                threshold=1.0,
                status="passed" if uniqueness == 1.0 else "failed",
                timestamp=datetime.utcnow()
            ))
        
        return metrics
    
    async def _check_consistency(self, conn: asyncpg.Connection, 
                                table_name: str) -> List[QualityMetric]:
        """Check data consistency rules."""
        metrics = []
        
        # Get foreign key constraints
        fk_constraints = await conn.fetch("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = $1
        """, table_name)
        
        for fk in fk_constraints:
            # Check referential integrity
            orphaned_count = await conn.fetchval(f"""
                SELECT COUNT(*)
                FROM {table_name} t
                LEFT JOIN {fk['foreign_table_name']} f
                    ON t.{fk['column_name']} = f.{fk['foreign_column_name']}
                WHERE t.{fk['column_name']} IS NOT NULL
                    AND f.{fk['foreign_column_name']} IS NULL
            """)
            
            consistency = 1.0 if orphaned_count == 0 else 1.0 - (orphaned_count / await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}"))
            metrics.append(QualityMetric(
                metric_name=f"referential_integrity_{fk['column_name']}",
                metric_value=consistency,
                threshold=1.0,
                status="passed" if consistency == 1.0 else "failed",
                timestamp=datetime.utcnow()
            ))
        
        return metrics 