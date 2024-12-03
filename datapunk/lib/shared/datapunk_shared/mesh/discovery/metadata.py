from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import structlog
from datetime import datetime
from .registry import ServiceRegistration, ServiceMetadata
from ...cache import CacheClient

logger = structlog.get_logger()

@dataclass
class MetadataConfig:
    """
    Configuration for metadata management system.
    
    Features:
    - Cache settings
    - Update policies
    - Validation rules
    - Query optimization
    """
    cache_ttl: int = 300  # 5 minutes
    max_tags: int = 50
    max_tag_length: int = 100
    enable_validation: bool = True
    enable_caching: bool = True

@dataclass
class MetadataIndex:
    """
    Index structure for efficient metadata queries.
    
    Maintains:
    - Tag-based indexes
    - Version mappings
    - Environment groupings
    - Region assignments
    """
    tag_index: Dict[str, Dict[str, Set[str]]] = field(default_factory=dict)
    version_index: Dict[str, Set[str]] = field(default_factory=dict)
    env_index: Dict[str, Set[str]] = field(default_factory=dict)
    region_index: Dict[str, Set[str]] = field(default_factory=dict)
    last_update: datetime = field(default_factory=datetime.utcnow)

class MetadataManager:
    """
    Manages service metadata with efficient querying and caching.
    
    Features:
    - Metadata CRUD operations
    - Query optimization
    - Cache management
    - Validation rules
    - Change tracking
    """
    
    def __init__(
        self,
        config: MetadataConfig,
        cache_client: Optional[CacheClient] = None
    ):
        self.config = config
        self.cache = cache_client
        self.logger = logger.bind(component="metadata_manager")
        self._index = MetadataIndex()
        
    async def update_metadata(
        self,
        service: ServiceRegistration,
        metadata: ServiceMetadata
    ) -> bool:
        """
        Update service metadata with validation.
        
        Process:
        1. Validate metadata
        2. Update indexes
        3. Update caches
        4. Track changes
        """
        try:
            if self.config.enable_validation:
                self._validate_metadata(metadata)
                
            # Update indexes
            self._update_indexes(service.id, metadata)
            
            # Update cache if enabled
            if self.config.enable_caching and self.cache:
                await self._update_cache(service.id, metadata)
                
            self.logger.info("metadata_updated",
                           service_id=service.id,
                           version=metadata.version)
            return True
            
        except Exception as e:
            self.logger.error("metadata_update_failed",
                            service_id=service.id,
                            error=str(e))
            return False
            
    async def query_services(
        self,
        tags: Optional[Dict[str, str]] = None,
        version: Optional[str] = None,
        environment: Optional[str] = None,
        region: Optional[str] = None
    ) -> Set[str]:
        """
        Query services by metadata criteria.
        
        Features:
        - Multi-criteria filtering
        - Index-based lookups
        - Result intersection
        - Cache utilization
        """
        results = None
        
        # Query by tags
        if tags:
            for key, value in tags.items():
                service_ids = self._index.tag_index.get(key, {}).get(value, set())
                if results is None:
                    results = service_ids
                else:
                    results &= service_ids
                    
        # Query by version
        if version and results is not None:
            version_ids = self._index.version_index.get(version, set())
            results &= version_ids
            
        # Query by environment
        if environment and results is not None:
            env_ids = self._index.env_index.get(environment, set())
            results &= env_ids
            
        # Query by region
        if region and results is not None:
            region_ids = self._index.region_index.get(region, set())
            results &= region_ids
            
        return results or set()
        
    def _validate_metadata(self, metadata: ServiceMetadata):
        """
        Validate metadata against configuration rules.
        
        Checks:
        - Tag count limits
        - Tag length limits
        - Required fields
        - Value formats
        """
        if len(metadata.tags) > self.config.max_tags:
            raise ValueError(f"Too many tags: {len(metadata.tags)}")
            
        for key, value in metadata.tags.items():
            if len(key) > self.config.max_tag_length:
                raise ValueError(f"Tag key too long: {key}")
            if len(value) > self.config.max_tag_length:
                raise ValueError(f"Tag value too long: {value}")
                
        if not metadata.version:
            raise ValueError("Version is required")
        if not metadata.environment:
            raise ValueError("Environment is required")
        if not metadata.region:
            raise ValueError("Region is required")
            
    def _update_indexes(self, service_id: str, metadata: ServiceMetadata):
        """
        Update all metadata indexes.
        
        Updates:
        - Tag indexes
        - Version mappings
        - Environment groupings
        - Region assignments
        """
        # Update tag index
        for key, value in metadata.tags.items():
            if key not in self._index.tag_index:
                self._index.tag_index[key] = {}
            if value not in self._index.tag_index[key]:
                self._index.tag_index[key][value] = set()
            self._index.tag_index[key][value].add(service_id)
            
        # Update version index
        if metadata.version not in self._index.version_index:
            self._index.version_index[metadata.version] = set()
        self._index.version_index[metadata.version].add(service_id)
        
        # Update environment index
        if metadata.environment not in self._index.env_index:
            self._index.env_index[metadata.environment] = set()
        self._index.env_index[metadata.environment].add(service_id)
        
        # Update region index
        if metadata.region not in self._index.region_index:
            self._index.region_index[metadata.region] = set()
        self._index.region_index[metadata.region].add(service_id)
        
        self._index.last_update = datetime.utcnow()
        
    async def _update_cache(self, service_id: str, metadata: ServiceMetadata):
        """Update metadata in distributed cache"""
        try:
            key = f"metadata:{service_id}"
            await self.cache.set(key, metadata, ttl=self.config.cache_ttl)
        except Exception as e:
            self.logger.warning("cache_update_failed",
                              service_id=service_id,
                              error=str(e))
            
    async def get_metadata_stats(self) -> Dict[str, Any]:
        """Get metadata management statistics"""
        return {
            "total_services": len(set().union(*self._index.version_index.values())),
            "total_versions": len(self._index.version_index),
            "total_environments": len(self._index.env_index),
            "total_regions": len(self._index.region_index),
            "total_tags": sum(len(v) for v in self._index.tag_index.values()),
            "last_update": self._index.last_update.isoformat()
        } 