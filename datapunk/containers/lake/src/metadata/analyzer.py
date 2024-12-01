from typing import Dict, List, Optional, Any, Tuple
import asyncpg
from datetime import datetime
import logging
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.sql import select, func
import numpy as np
from .core import (
    SchemaMetadata, StatisticsMetadata, QualityMetadata,
    QualityMetric, AccessPatternMetadata, DependencyMetadata,
    PerformanceMetadata, CacheMetadata, ResourceMetadata,
    AccessPattern, Dependency, DependencyType, PerformanceMetric
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
    
    async def _analyze_access_patterns(self, table_name: str) -> AccessPatternMetadata:
        """Analyze and extract access pattern metadata."""
        async with asyncpg.create_pool(**self.connection_config) as pool:
            async with pool.acquire() as conn:
                # Get table access statistics
                stats = await conn.fetchrow("""
                    SELECT 
                        pg_stat_get_tuples_returned($1::regclass) as reads,
                        pg_stat_get_tuples_inserted($1::regclass) as writes,
                        pg_stat_get_tuples_updated($1::regclass) as updates,
                        pg_stat_get_tuples_deleted($1::regclass) as deletes
                """, table_name)
                
                # Get index usage statistics
                index_stats = await conn.fetch("""
                    SELECT 
                        indexrelname as index_name,
                        idx_scan as scan_count,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    WHERE relname = $1
                """, table_name)
                
                # Get sequential vs index scan ratio
                scan_stats = await conn.fetchrow("""
                    SELECT 
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_read
                    FROM pg_stat_user_tables
                    WHERE relname = $1
                """, table_name)
                
                # Calculate hot and cold spots
                column_stats = await conn.fetch("""
                    SELECT 
                        a.attname as column_name,
                        n_distinct,
                        correlation
                    FROM pg_stats s
                    JOIN pg_attribute a ON (a.attname = s.attname)
                    WHERE tablename = $1
                """, table_name)
                
                # Create access patterns
                patterns = []
                
                # Add read pattern
                if scan_stats['seq_scan'] > 0 or scan_stats['idx_scan'] > 0:
                    patterns.append(AccessPattern(
                        pattern_type='read',
                        frequency=scan_stats['seq_scan'] + scan_stats['idx_scan'],
                        avg_latency_ms=0.0,  # Would need pg_stat_statements for this
                        peak_latency_ms=0.0,
                        bytes_accessed=scan_stats['seq_tup_read'] + scan_stats['idx_tup_read'],
                        timestamp=datetime.utcnow(),
                        query_pattern=None,
                        index_used=None
                    ))
                
                # Add index-specific patterns
                for idx in index_stats:
                    if idx['scan_count'] > 0:
                        patterns.append(AccessPattern(
                            pattern_type='seek',
                            frequency=idx['scan_count'],
                            avg_latency_ms=0.0,
                            peak_latency_ms=0.0,
                            bytes_accessed=idx['tuples_read'],
                            timestamp=datetime.utcnow(),
                            query_pattern=None,
                            index_used=idx['index_name']
                        ))
                
                # Calculate hot/cold spots
                hot_spots = {}
                cold_spots = {}
                for col in column_stats:
                    correlation = abs(col['correlation']) if col['correlation'] is not None else 0
                    if correlation > 0.7:
                        hot_spots[col['column_name']] = correlation
                    elif correlation < 0.3:
                        cold_spots[col['column_name']] = correlation
                
                return AccessPatternMetadata(
                    table_name=table_name,
                    patterns=patterns,
                    last_updated=datetime.utcnow(),
                    total_reads=stats['reads'],
                    total_writes=stats['writes'] + stats['updates'] + stats['deletes'],
                    hot_spots=hot_spots,
                    cold_spots=cold_spots
                )
    
    async def _analyze_dependencies(self, table_name: str) -> DependencyMetadata:
        """Analyze and extract dependency metadata."""
        async with asyncpg.create_pool(**self.connection_config) as pool:
            async with pool.acquire() as conn:
                upstream = []
                downstream = []
                validation_errors = []
                
                # Get foreign key dependencies
                fk_deps = await conn.fetch("""
                    SELECT
                        tc.table_name as source_table,
                        ccu.table_name as target_table,
                        kcu.column_name as source_column,
                        ccu.column_name as target_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND (tc.table_name = $1 OR ccu.table_name = $1)
                """, table_name)
                
                # Get view dependencies
                view_deps = await conn.fetch("""
                    SELECT 
                        dependent_ns.nspname as dependent_schema,
                        dependent.relname as dependent_view,
                        source_ns.nspname as source_schema,
                        source.relname as source_table
                    FROM pg_depend 
                    JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid 
                    JOIN pg_class as dependent ON pg_rewrite.ev_class = dependent.oid 
                    JOIN pg_class as source ON pg_depend.refobjid = source.oid 
                    JOIN pg_namespace dependent_ns ON dependent.relnamespace = dependent_ns.oid 
                    JOIN pg_namespace source_ns ON source.relnamespace = source_ns.oid 
                    WHERE source.relname = $1
                        AND source.relkind in ('r', 'v', 'm')
                """, table_name)
                
                # Process foreign key dependencies
                for fk in fk_deps:
                    dep = Dependency(
                        source=fk['source_table'],
                        target=fk['target_table'],
                        dependency_type=DependencyType.FOREIGN_KEY,
                        properties={
                            'source_column': fk['source_column'],
                            'target_column': fk['target_column']
                        },
                        is_blocking=True,
                        impact_level='high',
                        created_at=datetime.utcnow(),
                        validated_at=datetime.utcnow()
                    )
                    
                    if fk['source_table'] == table_name:
                        upstream.append(dep)
                    else:
                        downstream.append(dep)
                
                # Process view dependencies
                for view in view_deps:
                    dep = Dependency(
                        source=view['source_table'],
                        target=view['dependent_view'],
                        dependency_type=DependencyType.VIEW,
                        properties={
                            'schema': view['dependent_schema']
                        },
                        is_blocking=False,
                        impact_level='medium',
                        created_at=datetime.utcnow(),
                        validated_at=datetime.utcnow()
                    )
                    downstream.append(dep)
                
                return DependencyMetadata(
                    table_name=table_name,
                    upstream=upstream,
                    downstream=downstream,
                    last_validated=datetime.utcnow(),
                    is_valid=len(validation_errors) == 0,
                    validation_errors=validation_errors
                )
    
    async def _analyze_performance(self, table_name: str) -> PerformanceMetadata:
        """Analyze and extract performance metadata."""
        async with asyncpg.create_pool(**self.connection_config) as pool:
            async with pool.acquire() as conn:
                metrics = []
                bottlenecks = []
                
                # Get basic performance metrics
                stats = await conn.fetchrow("""
                    SELECT 
                        pg_table_size($1) as table_size,
                        pg_indexes_size($1) as index_size,
                        (SELECT count(*) FROM pg_stat_activity 
                         WHERE query ILIKE '%' || $1 || '%') as active_queries
                """, table_name)
                
                # Get query performance metrics if pg_stat_statements is available
                try:
                    query_stats = await conn.fetch("""
                        SELECT 
                            calls,
                            total_exec_time / calls as avg_exec_time,
                            shared_blks_hit,
                            shared_blks_read,
                            shared_blks_written,
                            temp_blks_read,
                            temp_blks_written
                        FROM pg_stat_statements
                        WHERE query ILIKE '%' || $1 || '%'
                        AND calls > 0
                    """, table_name)
                    
                    for stat in query_stats:
                        metrics.append(PerformanceMetric(
                            operation_type='query',
                            execution_time_ms=stat['avg_exec_time'],
                            cpu_time_ms=0.0,  # Not available in pg_stat_statements
                            io_time_ms=(stat['shared_blks_read'] + stat['temp_blks_read']) * 0.1,
                            memory_mb=(stat['shared_blks_written'] + stat['temp_blks_written']) * 8 / 1024,
                            timestamp=datetime.utcnow()
                        ))
                        
                        # Check for potential bottlenecks
                        if stat['avg_exec_time'] > 1000:  # More than 1 second
                            bottlenecks.append('Slow query execution')
                        if stat['temp_blks_written'] > 1000:
                            bottlenecks.append('High temp space usage')
                            
                except Exception:
                    self.logger.warning("pg_stat_statements not available")
                
                # Calculate averages
                avg_time = sum(m.execution_time_ms for m in metrics) / len(metrics) if metrics else 0
                peak_memory = max(m.memory_mb for m in metrics) if metrics else 0
                
                return PerformanceMetadata(
                    table_name=table_name,
                    metrics=metrics,
                    last_updated=datetime.utcnow(),
                    avg_query_time_ms=avg_time,
                    peak_memory_mb=peak_memory,
                    bottlenecks=list(set(bottlenecks))
                )
    
    async def _analyze_cache(self, table_name: str) -> CacheMetadata:
        """Analyze and extract cache metadata."""
        async with asyncpg.create_pool(**self.connection_config) as pool:
            async with pool.acquire() as conn:
                # Get buffer cache statistics
                stats = await conn.fetchrow("""
                    SELECT 
                        heap_blks_read,
                        heap_blks_hit,
                        idx_blks_read,
                        idx_blks_hit
                    FROM pg_statio_user_tables
                    WHERE relname = $1
                """, table_name)
                
                if not stats:
                    return CacheMetadata(
                        table_name=table_name,
                        hit_rate=0.0,
                        miss_rate=0.0,
                        eviction_rate=0.0,
                        cache_size_mb=0.0,
                        cached_rows=0,
                        last_updated=datetime.utcnow(),
                        access_patterns={}
                    )
                
                total_reads = stats['heap_blks_read'] + stats['idx_blks_read']
                total_hits = stats['heap_blks_hit'] + stats['idx_blks_hit']
                total_accesses = total_reads + total_hits
                
                if total_accesses > 0:
                    hit_rate = total_hits / total_accesses
                    miss_rate = total_reads / total_accesses
                else:
                    hit_rate = miss_rate = 0.0
                
                # Get cached rows estimate
                cached_rows = await conn.fetchval("""
                    SELECT reltuples::bigint * (heap_blks_hit::float / 
                        NULLIF(heap_blks_hit + heap_blks_read, 0))
                    FROM pg_class c
                    JOIN pg_statio_user_tables s ON c.relname = s.relname
                    WHERE c.relname = $1
                """, table_name)
                
                return CacheMetadata(
                    table_name=table_name,
                    hit_rate=hit_rate,
                    miss_rate=miss_rate,
                    eviction_rate=0.0,  # Not directly available from PostgreSQL
                    cache_size_mb=(total_hits * 8) / 1024,  # Assuming 8KB pages
                    cached_rows=int(cached_rows or 0),
                    last_updated=datetime.utcnow(),
                    access_patterns={
                        'heap_reads': stats['heap_blks_read'],
                        'heap_hits': stats['heap_blks_hit'],
                        'index_reads': stats['idx_blks_read'],
                        'index_hits': stats['idx_blks_hit']
                    }
                )
    
    async def _analyze_resource(self, table_name: str) -> ResourceMetadata:
        """Analyze and extract resource usage metadata."""
        async with asyncpg.create_pool(**self.connection_config) as pool:
            async with pool.acquire() as conn:
                # Get basic resource statistics
                stats = await conn.fetchrow("""
                    SELECT 
                        pg_total_relation_size($1) as total_size,
                        pg_table_size($1) as table_size,
                        pg_indexes_size($1) as index_size,
                        age(relfrozenxid) as xid_age
                    FROM pg_class
                    WHERE relname = $1
                """, table_name)
                
                # Get vacuum and analyze statistics
                maint_stats = await conn.fetchrow("""
                    SELECT 
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables
                    WHERE relname = $1
                """, table_name)
                
                # Get bloat estimate
                bloat_stats = await conn.fetchrow("""
                    SELECT 
                        n_dead_tup::float / n_live_tup as dead_tuple_ratio,
                        n_mod_since_analyze
                    FROM pg_stat_user_tables
                    WHERE relname = $1
                """, table_name)
                
                # Get connection statistics
                conn_stats = await conn.fetchrow("""
                    SELECT count(*) as connections
                    FROM pg_stat_activity
                    WHERE query ILIKE '%' || $1 || '%'
                """, table_name)
                
                return ResourceMetadata(
                    table_name=table_name,
                    disk_usage_mb=stats['table_size'] / (1024 * 1024),
                    index_size_mb=stats['index_size'] / (1024 * 1024),
                    temp_space_mb=0.0,  # Would need pg_stat_statements for this
                    peak_connections=conn_stats['connections'],
                    avg_active_time_ms=0.0,  # Would need pg_stat_statements for this
                    last_vacuum=maint_stats['last_vacuum'] or maint_stats['last_autovacuum'],
                    last_analyze=maint_stats['last_analyze'] or maint_stats['last_autoanalyze'],
                    bloat_ratio=bloat_stats['dead_tuple_ratio'] if bloat_stats['dead_tuple_ratio'] is not None else 0.0
                ) 