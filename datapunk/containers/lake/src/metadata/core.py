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
    WORKLOAD = "workload"
    EVOLUTION = "evolution"
    COMPLIANCE = "compliance"
    ENHANCED_QUALITY = "enhanced_quality"
    STORAGE = "storage"

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

class WorkloadType(Enum):
    """Types of workload patterns."""
    OLTP = "oltp"
    OLAP = "olap"
    MIXED = "mixed"
    BATCH = "batch"
    STREAMING = "streaming"
    ETL = "etl"
    ML = "machine_learning"

class QueryPattern(BaseModel):
    """Represents a query pattern in workload."""
    pattern_hash: str
    query_template: str
    frequency: int
    avg_duration_ms: float
    peak_duration_ms: float
    resource_usage: Dict[str, float]
    last_seen: datetime
    parameters: Dict[str, Any]

class WorkloadMetadata(BaseModel):
    """Workload pattern metadata."""
    table_name: str
    workload_type: WorkloadType
    query_patterns: List[QueryPattern]
    peak_qps: float
    avg_qps: float
    busy_periods: List[Dict[str, Any]]
    quiet_periods: List[Dict[str, Any]]
    last_analyzed: datetime

class SchemaChange(BaseModel):
    """Represents a schema change event."""
    change_type: str  # 'add_column', 'drop_column', 'modify_column', etc.
    column_name: Optional[str]
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    timestamp: datetime
    applied_by: str
    change_script: Optional[str]

class DataEvolutionMetadata(BaseModel):
    """Data evolution and change history."""
    table_name: str
    schema_version: int
    schema_changes: List[SchemaChange]
    data_growth_rate: float  # rows per day
    size_growth_rate: float  # bytes per day
    value_distributions: Dict[str, Dict[str, Any]]
    temporal_patterns: Dict[str, Any]
    last_analyzed: datetime

class ComplianceRule(BaseModel):
    """Represents a compliance rule."""
    rule_id: str
    rule_type: str  # 'retention', 'encryption', 'access', 'audit', etc.
    description: str
    parameters: Dict[str, Any]
    validation_query: Optional[str]
    remediation_action: Optional[str]

class ComplianceCheck(BaseModel):
    """Result of a compliance check."""
    rule_id: str
    status: str  # 'passed', 'failed', 'warning'
    details: str
    timestamp: datetime
    affected_rows: Optional[int]

class ComplianceMetadata(BaseModel):
    """Compliance and governance metadata."""
    table_name: str
    classification_level: str
    applicable_rules: List[ComplianceRule]
    compliance_checks: List[ComplianceCheck]
    encryption_status: Dict[str, Any]
    retention_status: Dict[str, Any]
    audit_logs: List[Dict[str, Any]]
    last_validated: datetime

class DataQualityRule(BaseModel):
    """Represents a data quality rule."""
    rule_id: str
    rule_type: str  # 'completeness', 'accuracy', 'consistency', etc.
    column_name: Optional[str]
    condition: str
    threshold: float
    severity: str  # 'critical', 'warning', 'info'

class DataQualityCheck(BaseModel):
    """Result of a data quality check."""
    rule_id: str
    status: str
    value: float
    threshold: float
    sample_size: Optional[int]
    timestamp: datetime

class EnhancedQualityMetadata(BaseModel):
    """Enhanced data quality metadata."""
    table_name: str
    quality_rules: List[DataQualityRule]
    quality_checks: List[DataQualityCheck]
    historical_scores: List[Dict[str, Any]]
    anomaly_detections: List[Dict[str, Any]]
    remediation_history: List[Dict[str, Any]]
    last_checked: datetime

class PartitionInfo(BaseModel):
    """Information about a table partition."""
    partition_key: str
    partition_value: Any
    row_count: int
    size_bytes: int
    last_accessed: datetime
    access_frequency: float
    is_compressed: bool

class StorageMetadata(BaseModel):
    """Enhanced storage metadata."""
    table_name: str
    partitions: List[PartitionInfo]
    compression_ratio: float
    storage_format: str
    block_size: int
    replication_factor: int
    distribution_key: Optional[str]
    storage_policy: Dict[str, Any]
    last_updated: datetime

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
    
    @abstractmethod
    async def get_workload(self, table_name: str) -> Optional[WorkloadMetadata]:
        """Retrieve workload metadata."""
        pass
    
    @abstractmethod
    async def update_workload(self, metadata: WorkloadMetadata) -> None:
        """Update workload metadata."""
        pass
    
    @abstractmethod
    async def get_evolution(self, table_name: str) -> Optional[DataEvolutionMetadata]:
        """Retrieve evolution metadata."""
        pass
    
    @abstractmethod
    async def update_evolution(self, metadata: DataEvolutionMetadata) -> None:
        """Update evolution metadata."""
        pass
    
    @abstractmethod
    async def get_compliance(self, table_name: str) -> Optional[ComplianceMetadata]:
        """Retrieve compliance metadata."""
        pass
    
    @abstractmethod
    async def update_compliance(self, metadata: ComplianceMetadata) -> None:
        """Update compliance metadata."""
        pass
    
    @abstractmethod
    async def get_enhanced_quality(self, table_name: str) -> Optional[EnhancedQualityMetadata]:
        """Retrieve enhanced quality metadata."""
        pass
    
    @abstractmethod
    async def update_enhanced_quality(self, metadata: EnhancedQualityMetadata) -> None:
        """Update enhanced quality metadata."""
        pass
    
    @abstractmethod
    async def get_storage(self, table_name: str) -> Optional[StorageMetadata]:
        """Retrieve storage metadata."""
        pass
    
    @abstractmethod
    async def update_storage(self, metadata: StorageMetadata) -> None:
        """Update storage metadata."""
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
            
            # Update workload metadata
            workload = await self._analyze_workload(table_name)
            await self.store.update_workload(workload)
            
            # Update evolution metadata
            evolution = await self._analyze_evolution(table_name)
            await self.store.update_evolution(evolution)
            
            # Update compliance metadata
            compliance = await self._analyze_compliance(table_name)
            await self.store.update_compliance(compliance)
            
            # Update enhanced quality metadata
            enhanced_quality = await self._analyze_enhanced_quality(table_name)
            await self.store.update_enhanced_quality(enhanced_quality)
            
            # Update storage metadata
            storage = await self._analyze_storage(table_name)
            await self.store.update_storage(storage)
            
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
    
    async def _analyze_workload(self, table_name: str) -> WorkloadMetadata:
        """Analyze and extract workload metadata."""
        # Implementation
        pass
    
    async def _analyze_evolution(self, table_name: str) -> DataEvolutionMetadata:
        """Analyze and extract evolution metadata."""
        # Implementation
        pass
    
    async def _analyze_compliance(self, table_name: str) -> ComplianceMetadata:
        """Analyze and extract compliance metadata."""
        # Implementation
        pass
    
    async def _analyze_enhanced_quality(self, table_name: str) -> EnhancedQualityMetadata:
        """Analyze and extract enhanced quality metadata."""
        # Implementation
        pass
    
    async def _analyze_storage(self, table_name: str) -> StorageMetadata:
        """Analyze and extract storage metadata."""
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
            "resource": await self.store.get_resource_metadata(table_name),
            "workload": await self.store.get_workload(table_name),
            "evolution": await self.store.get_evolution(table_name),
            "compliance": await self.store.get_compliance(table_name),
            "enhanced_quality": await self.store.get_enhanced_quality(table_name),
            "storage": await self.store.get_storage(table_name)
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