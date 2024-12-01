from typing import Dict, List, Optional, Any
import asyncpg
import json
from datetime import datetime
from .core import (
    MetadataStore, SchemaMetadata, StatisticsMetadata,
    LineageMetadata, QualityMetadata, LineageNode, LineageEdge
)

CREATE_SCHEMA_TABLE = """
CREATE TABLE IF NOT EXISTS metadata.schema_metadata (
    table_name TEXT PRIMARY KEY,
    columns JSONB NOT NULL,
    primary_key TEXT[] NOT NULL,
    foreign_keys JSONB NOT NULL,
    indexes JSONB NOT NULL,
    constraints JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    version INTEGER NOT NULL
);
"""

CREATE_STATISTICS_TABLE = """
CREATE TABLE IF NOT EXISTS metadata.statistics_metadata (
    table_name TEXT PRIMARY KEY,
    row_count BIGINT NOT NULL,
    size_bytes BIGINT NOT NULL,
    last_analyzed TIMESTAMP WITH TIME ZONE NOT NULL,
    column_stats JSONB NOT NULL,
    index_stats JSONB NOT NULL,
    sample_size INTEGER,
    is_estimate BOOLEAN NOT NULL
);
"""

CREATE_LINEAGE_TABLE = """
CREATE TABLE IF NOT EXISTS metadata.lineage_metadata (
    node_id TEXT PRIMARY KEY,
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL
);
"""

CREATE_QUALITY_TABLE = """
CREATE TABLE IF NOT EXISTS metadata.quality_metadata (
    table_name TEXT PRIMARY KEY,
    metrics JSONB NOT NULL,
    last_checked TIMESTAMP WITH TIME ZONE NOT NULL,
    overall_score FLOAT NOT NULL
);
"""

class PostgresMetadataStore(MetadataStore):
    """PostgreSQL-based metadata store implementation."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """Initialize the PostgreSQL metadata store."""
        self.connection_config = connection_config
        self.pool = None
    
    async def initialize(self) -> None:
        """Initialize the connection pool and create tables."""
        self.pool = await asyncpg.create_pool(**self.connection_config)
        await self._init_tables()
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def _init_tables(self) -> None:
        """Initialize metadata tables."""
        async with self.pool.acquire() as conn:
            # Create metadata schema
            await conn.execute("CREATE SCHEMA IF NOT EXISTS metadata;")
            
            # Create tables
            await conn.execute(CREATE_SCHEMA_TABLE)
            await conn.execute(CREATE_STATISTICS_TABLE)
            await conn.execute(CREATE_LINEAGE_TABLE)
            await conn.execute(CREATE_QUALITY_TABLE)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_schema_metadata_updated 
                ON metadata.schema_metadata(updated_at);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_statistics_metadata_analyzed 
                ON metadata.statistics_metadata(last_analyzed);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lineage_metadata_updated 
                ON metadata.lineage_metadata(last_updated);
            """)
    
    async def get_schema(self, table_name: str) -> Optional[SchemaMetadata]:
        """Retrieve schema metadata from PostgreSQL."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM metadata.schema_metadata 
                WHERE table_name = $1;
            """, table_name)
            
            if not row:
                return None
                
            return SchemaMetadata(
                name=row['table_name'],
                columns=row['columns'],
                primary_key=row['primary_key'],
                foreign_keys=row['foreign_keys'],
                indexes=row['indexes'],
                constraints=row['constraints'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                version=row['version']
            )
    
    async def update_schema(self, metadata: SchemaMetadata) -> None:
        """Update schema metadata in PostgreSQL."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO metadata.schema_metadata 
                (table_name, columns, primary_key, foreign_keys, indexes, 
                 constraints, created_at, updated_at, version)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (table_name) 
                DO UPDATE SET
                    columns = EXCLUDED.columns,
                    primary_key = EXCLUDED.primary_key,
                    foreign_keys = EXCLUDED.foreign_keys,
                    indexes = EXCLUDED.indexes,
                    constraints = EXCLUDED.constraints,
                    updated_at = EXCLUDED.updated_at,
                    version = EXCLUDED.version;
            """,
            metadata.name,
            json.dumps(metadata.columns),
            metadata.primary_key,
            json.dumps(metadata.foreign_keys),
            json.dumps(metadata.indexes),
            json.dumps(metadata.constraints),
            metadata.created_at,
            metadata.updated_at,
            metadata.version
            )
    
    async def get_statistics(self, table_name: str) -> Optional[StatisticsMetadata]:
        """Retrieve statistical metadata from PostgreSQL."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM metadata.statistics_metadata 
                WHERE table_name = $1;
            """, table_name)
            
            if not row:
                return None
                
            return StatisticsMetadata(
                table_name=row['table_name'],
                row_count=row['row_count'],
                size_bytes=row['size_bytes'],
                last_analyzed=row['last_analyzed'],
                column_stats=row['column_stats'],
                index_stats=row['index_stats'],
                sample_size=row['sample_size'],
                is_estimate=row['is_estimate']
            )
    
    async def update_statistics(self, metadata: StatisticsMetadata) -> None:
        """Update statistical metadata in PostgreSQL."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO metadata.statistics_metadata 
                (table_name, row_count, size_bytes, last_analyzed,
                 column_stats, index_stats, sample_size, is_estimate)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (table_name) 
                DO UPDATE SET
                    row_count = EXCLUDED.row_count,
                    size_bytes = EXCLUDED.size_bytes,
                    last_analyzed = EXCLUDED.last_analyzed,
                    column_stats = EXCLUDED.column_stats,
                    index_stats = EXCLUDED.index_stats,
                    sample_size = EXCLUDED.sample_size,
                    is_estimate = EXCLUDED.is_estimate;
            """,
            metadata.table_name,
            metadata.row_count,
            metadata.size_bytes,
            metadata.last_analyzed,
            json.dumps(metadata.column_stats),
            json.dumps(metadata.index_stats),
            metadata.sample_size,
            metadata.is_estimate
            )
    
    async def get_lineage(self, node_id: str) -> Optional[LineageMetadata]:
        """Retrieve lineage metadata from PostgreSQL."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM metadata.lineage_metadata 
                WHERE node_id = $1;
            """, node_id)
            
            if not row:
                return None
                
            return LineageMetadata(
                nodes=row['nodes'],
                edges=row['edges'],
                last_updated=row['last_updated']
            )
    
    async def update_lineage(self, metadata: LineageMetadata) -> None:
        """Update lineage metadata in PostgreSQL."""
        async with self.pool.acquire() as conn:
            # Convert nodes and edges to JSON
            nodes_json = [node.dict() for node in metadata.nodes]
            edges_json = [edge.dict() for edge in metadata.edges]
            
            # Use the first node's ID as the primary key
            node_id = metadata.nodes[0].id if metadata.nodes else "unknown"
            
            await conn.execute("""
                INSERT INTO metadata.lineage_metadata 
                (node_id, nodes, edges, last_updated)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (node_id) 
                DO UPDATE SET
                    nodes = EXCLUDED.nodes,
                    edges = EXCLUDED.edges,
                    last_updated = EXCLUDED.last_updated;
            """,
            node_id,
            json.dumps(nodes_json),
            json.dumps(edges_json),
            metadata.last_updated
            )
    
    async def get_quality(self, table_name: str) -> Optional[QualityMetadata]:
        """Retrieve quality metadata from PostgreSQL."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM metadata.quality_metadata 
                WHERE table_name = $1;
            """, table_name)
            
            if not row:
                return None
                
            return QualityMetadata(
                table_name=row['table_name'],
                metrics=row['metrics'],
                last_checked=row['last_checked'],
                overall_score=row['overall_score']
            )
    
    async def update_quality(self, metadata: QualityMetadata) -> None:
        """Update quality metadata in PostgreSQL."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO metadata.quality_metadata 
                (table_name, metrics, last_checked, overall_score)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (table_name) 
                DO UPDATE SET
                    metrics = EXCLUDED.metrics,
                    last_checked = EXCLUDED.last_checked,
                    overall_score = EXCLUDED.overall_score;
            """,
            metadata.table_name,
            json.dumps([metric.dict() for metric in metadata.metrics]),
            metadata.last_checked,
            metadata.overall_score
            ) 