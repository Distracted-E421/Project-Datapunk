from typing import Dict, List, Optional, Set, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class MetadataType(Enum):
    """Types of metadata managed by the system."""
    SCHEMA = "schema"
    STATISTICS = "statistics"
    LINEAGE = "lineage"
    SECURITY = "security"
    QUALITY = "quality"
    GOVERNANCE = "governance"
    ACCESS_PATTERN = "access_pattern"
    DEPENDENCY = "dependency"
    PERFORMANCE = "performance"
    CACHE = "cache"
    RESOURCE = "resource"

class SchemaMetadata(BaseModel):
    """Schema metadata for a table or collection."""
    name: str
    columns: Dict[str, Dict[str, Any]]
    primary_key: List[str]
    foreign_keys: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    version: int

class StatisticsMetadata(BaseModel):
    """Statistical metadata for a table or collection."""
    table_name: str
    row_count: int
    size_bytes: int
    last_analyzed: datetime
    column_stats: Dict[str, Dict[str, Any]]
    index_stats: Dict[str, Dict[str, Any]]
    sample_size: Optional[int]
    is_estimate: bool

class LineageNode(BaseModel):
    """Node in the data lineage graph."""
    id: str
    type: str  # 'source', 'transformation', 'target'
    name: str
    properties: Dict[str, Any]

class LineageEdge(BaseModel):
    """Edge in the data lineage graph."""
    source_id: str
    target_id: str
    operation: str
    timestamp: datetime
    properties: Dict[str, Any]

class LineageMetadata(BaseModel):
    """Data lineage metadata."""
    nodes: List[LineageNode]
    edges: List[LineageEdge]
    last_updated: datetime

class QualityMetric(BaseModel):
    """Data quality metric."""
    metric_name: str
    metric_value: float
    threshold: Optional[float]
    status: str  # 'passed', 'warning', 'failed'
    timestamp: datetime

class QualityMetadata(BaseModel):
    """Data quality metadata."""
    table_name: str
    metrics: List[QualityMetric]
    last_checked: datetime
    overall_score: float

class SecurityMetadata(BaseModel):
    """Security and access control metadata."""
    table_name: str
    classification: str  # e.g., 'public', 'confidential', 'restricted'
    column_classifications: Dict[str, str]
    access_controls: Dict[str, List[str]]
    encryption_info: Optional[Dict[str, Any]]
    last_updated: datetime

class GovernanceMetadata(BaseModel):
    """Data governance metadata."""
    table_name: str
    owner: str
    steward: Optional[str]
    retention_policy: Dict[str, Any]
    compliance_rules: List[Dict[str, Any]]
    tags: List[str]
    documentation: Optional[str]

class AccessPattern(BaseModel):
    """Represents a data access pattern."""
    pattern_type: str  # 'read', 'write', 'scan', 'seek'
    frequency: int
    avg_latency_ms: float
    peak_latency_ms: float
    bytes_accessed: int
    timestamp: datetime
    query_pattern: Optional[str]
    index_used: Optional[str]

class AccessPatternMetadata(BaseModel):
    """Access pattern metadata for a table."""
    table_name: str
    patterns: List[AccessPattern]
    last_updated: datetime
    total_reads: int
    total_writes: int
    hot_spots: Dict[str, float]  # column -> access frequency
    cold_spots: Dict[str, float]

class DependencyType(Enum):
    """Types of dependencies between data objects."""
    FOREIGN_KEY = "foreign_key"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"
    TRIGGER = "trigger"
    FUNCTION = "function"
    ETL = "etl"
    APPLICATION = "application"

class Dependency(BaseModel):
    """Represents a dependency between data objects."""
    source: str
    target: str
    dependency_type: DependencyType
    properties: Dict[str, Any]
    is_blocking: bool
    impact_level: str  # 'high', 'medium', 'low'
    created_at: datetime
    validated_at: datetime

class DependencyMetadata(BaseModel):
    """Dependency metadata for a table."""
    table_name: str
    upstream: List[Dependency]
    downstream: List[Dependency]
    last_validated: datetime
    is_valid: bool
    validation_errors: List[str]

class PerformanceMetric(BaseModel):
    """Performance metric for operations."""
    operation_type: str
    execution_time_ms: float
    cpu_time_ms: float
    io_time_ms: float
    memory_mb: float
    timestamp: datetime

class PerformanceMetadata(BaseModel):
    """Performance metadata for a table."""
    table_name: str
    metrics: List[PerformanceMetric]
    last_updated: datetime
    avg_query_time_ms: float
    peak_memory_mb: float
    bottlenecks: List[str]

class CacheMetadata(BaseModel):
    """Cache behavior metadata."""
    table_name: str
    hit_rate: float
    miss_rate: float
    eviction_rate: float
    cache_size_mb: float
    cached_rows: int
    last_updated: datetime
    access_patterns: Dict[str, float]

class ResourceMetadata(BaseModel):
    """Resource usage metadata."""
    table_name: str
    disk_usage_mb: float
    index_size_mb: float
    temp_space_mb: float
    peak_connections: int
    avg_active_time_ms: float
    last_vacuum: datetime
    last_analyze: datetime
    bloat_ratio: float

class MetadataStore(ABC):
    """Abstract base class for metadata storage."""
    
    @abstractmethod
    async def get_schema(self, table_name: str) -> Optional[SchemaMetadata]:
        """Retrieve schema metadata."""
        pass
    
    @abstractmethod
    async def update_schema(self, metadata: SchemaMetadata) -> None:
        """Update schema metadata."""
        pass
    
    @abstractmethod
    async def get_statistics(self, table_name: str) -> Optional[StatisticsMetadata]:
        """Retrieve statistical metadata."""
        pass
    
    @abstractmethod
    async def update_statistics(self, metadata: StatisticsMetadata) -> None:
        """Update statistical metadata."""
        pass
    
    @abstractmethod
    async def get_lineage(self, node_id: str) -> Optional[LineageMetadata]:
        """Retrieve lineage metadata."""
        pass
    
    @abstractmethod
    async def update_lineage(self, metadata: LineageMetadata) -> None:
        """Update lineage metadata."""
        pass
    
    @abstractmethod
    async def get_quality(self, table_name: str) -> Optional[QualityMetadata]:
        """Retrieve quality metadata."""
        pass
    
    @abstractmethod
    async def update_quality(self, metadata: QualityMetadata) -> None:
        """Update quality metadata."""
        pass
    
    @abstractmethod
    async def get_access_patterns(self, table_name: str) -> Optional[AccessPatternMetadata]:
        """Retrieve access pattern metadata."""
        pass
    
    @abstractmethod
    async def update_access_patterns(self, metadata: AccessPatternMetadata) -> None:
        """Update access pattern metadata."""
        pass
    
    @abstractmethod
    async def get_dependencies(self, table_name: str) -> Optional[DependencyMetadata]:
        """Retrieve dependency metadata."""
        pass
    
    @abstractmethod
    async def update_dependencies(self, metadata: DependencyMetadata) -> None:
        """Update dependency metadata."""
        pass
    
    @abstractmethod
    async def get_performance(self, table_name: str) -> Optional[PerformanceMetadata]:
        """Retrieve performance metadata."""
        pass
    
    @abstractmethod
    async def update_performance(self, metadata: PerformanceMetadata) -> None:
        """Update performance metadata."""
        pass
    
    @abstractmethod
    async def get_cache_metadata(self, table_name: str) -> Optional[CacheMetadata]:
        """Retrieve cache metadata."""
        pass
    
    @abstractmethod
    async def update_cache_metadata(self, metadata: CacheMetadata) -> None:
        """Update cache metadata."""
        pass
    
    @abstractmethod
    async def get_resource_metadata(self, table_name: str) -> Optional[ResourceMetadata]:
        """Retrieve resource usage metadata."""
        pass
    
    @abstractmethod
    async def update_resource_metadata(self, metadata: ResourceMetadata) -> None:
        """Update resource usage metadata."""
        pass

class PostgresMetadataStore(MetadataStore):
    """PostgreSQL-based metadata store implementation."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.connection_config = connection_config
        self._init_tables()
    
    def _init_tables(self) -> None:
        """Initialize metadata tables."""
        # Implementation for creating necessary tables
        pass
    
    async def get_schema(self, table_name: str) -> Optional[SchemaMetadata]:
        """Retrieve schema metadata from PostgreSQL."""
        # Implementation
        pass
    
    async def update_schema(self, metadata: SchemaMetadata) -> None:
        """Update schema metadata in PostgreSQL."""
        # Implementation
        pass
    
    # Similar implementations for other metadata types...

class MetadataManager:
    """Central manager for all metadata operations."""
    
    def __init__(self, store: MetadataStore):
        self.store = store
        self.logger = logging.getLogger(__name__)
    
    async def analyze_table(self, table_name: str) -> None:
        """Analyze a table and update all metadata."""
        try:
            # Update schema metadata
            schema = await self._analyze_schema(table_name)
            await self.store.update_schema(schema)
            
            # Update statistics
            stats = await self._analyze_statistics(table_name)
            await self.store.update_statistics(stats)
            
            # Update quality metrics
            quality = await self._analyze_quality(table_name)
            await self.store.update_quality(quality)
            
            # Update access patterns
            access_patterns = await self._analyze_access_patterns(table_name)
            await self.store.update_access_patterns(access_patterns)
            
            # Update dependencies
            dependencies = await self._analyze_dependencies(table_name)
            await self.store.update_dependencies(dependencies)
            
            # Update performance metrics
            performance = await self._analyze_performance(table_name)
            await self.store.update_performance(performance)
            
            # Update cache metadata
            cache = await self._analyze_cache(table_name)
            await self.store.update_cache_metadata(cache)
            
            # Update resource usage metadata
            resource = await self._analyze_resource(table_name)
            await self.store.update_resource_metadata(resource)
            
            self.logger.info(f"Successfully analyzed table: {table_name}")
            
        except Exception as e:
            self.logger.error(f"Error analyzing table {table_name}: {str(e)}")
            raise
    
    async def _analyze_schema(self, table_name: str) -> SchemaMetadata:
        """Analyze and extract schema metadata."""
        # Implementation
        pass
    
    async def _analyze_statistics(self, table_name: str) -> StatisticsMetadata:
        """Analyze and extract statistical metadata."""
        # Implementation
        pass
    
    async def _analyze_quality(self, table_name: str) -> QualityMetadata:
        """Analyze and extract quality metadata."""
        # Implementation
        pass
    
    async def _analyze_access_patterns(self, table_name: str) -> AccessPatternMetadata:
        """Analyze and extract access pattern metadata."""
        # Implementation
        pass
    
    async def _analyze_dependencies(self, table_name: str) -> DependencyMetadata:
        """Analyze and extract dependency metadata."""
        # Implementation
        pass
    
    async def _analyze_performance(self, table_name: str) -> PerformanceMetadata:
        """Analyze and extract performance metadata."""
        # Implementation
        pass
    
    async def _analyze_cache(self, table_name: str) -> CacheMetadata:
        """Analyze and extract cache metadata."""
        # Implementation
        pass
    
    async def _analyze_resource(self, table_name: str) -> ResourceMetadata:
        """Analyze and extract resource usage metadata."""
        # Implementation
        pass
    
    async def track_lineage(self, source: str, target: str, 
                          operation: str, properties: Dict[str, Any]) -> None:
        """Track data lineage for an operation."""
        try:
            # Create lineage nodes and edges
            source_node = LineageNode(
                id=source,
                type="source",
                name=source,
                properties={}
            )
            
            target_node = LineageNode(
                id=target,
                type="target",
                name=target,
                properties={}
            )
            
            edge = LineageEdge(
                source_id=source,
                target_id=target,
                operation=operation,
                timestamp=datetime.utcnow(),
                properties=properties
            )
            
            lineage = LineageMetadata(
                nodes=[source_node, target_node],
                edges=[edge],
                last_updated=datetime.utcnow()
            )
            
            await self.store.update_lineage(lineage)
            
        except Exception as e:
            self.logger.error(f"Error tracking lineage: {str(e)}")
            raise
    
    async def get_table_metadata(self, table_name: str) -> Dict[str, Any]:
        """Get all metadata for a table."""
        return {
            "schema": await self.store.get_schema(table_name),
            "statistics": await self.store.get_statistics(table_name),
            "quality": await self.store.get_quality(table_name),
            "lineage": await self.store.get_lineage(table_name),
            "access_patterns": await self.store.get_access_patterns(table_name),
            "dependencies": await self.store.get_dependencies(table_name),
            "performance": await self.store.get_performance(table_name),
            "cache": await self.store.get_cache_metadata(table_name),
            "resource": await self.store.get_resource_metadata(table_name)
        }
    
    async def refresh_statistics(self, table_name: str) -> None:
        """Refresh statistical metadata for a table."""
        try:
            stats = await self._analyze_statistics(table_name)
            await self.store.update_statistics(stats)
            self.logger.info(f"Successfully refreshed statistics for table: {table_name}")
        except Exception as e:
            self.logger.error(f"Error refreshing statistics for {table_name}: {str(e)}")
            raise 