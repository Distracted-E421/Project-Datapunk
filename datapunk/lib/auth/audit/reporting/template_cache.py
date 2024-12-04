"""
Template caching system for audit reports.

This module implements a two-level caching strategy for Jinja2 templates:
1. An in-memory LRU cache for frequently accessed templates
2. A distributed cache for longer-term storage and cross-service sharing

The system helps optimize template rendering performance while maintaining 
consistency across distributed services.
"""
from typing import Dict, Optional, Any, TYPE_CHECKING
import structlog
from datetime import datetime, timedelta
from jinja2 import Template
import hashlib
import json

if TYPE_CHECKING:
    from ....cache import CacheClient
    from ....monitoring import MetricsClient

logger = structlog.get_logger()

class TemplateCache:
    """
    Caches compiled Jinja2 templates using a two-tier caching strategy.
    
    The cache implements:
    - Local LRU cache (up to 100 templates) for high-performance access
    - Distributed cache with TTL for consistency across services
    - Automatic template compilation and cache population
    - Cache invalidation capabilities (single template or full cache)
    
    NOTE: The local cache size limit (100) is hardcoded but could be made configurable
    if memory constraints become an issue in production.
    """
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 ttl: timedelta = timedelta(hours=1)):
        """
        Initialize the template cache system.
        
        IMPORTANT: The default 1-hour TTL assumes templates don't change frequently.
        Adjust this value based on your template update patterns and consistency requirements.
        """
        self.cache = cache_client
        self.metrics = metrics
        self.ttl = ttl
        self.logger = logger.bind(component="template_cache")
        
        # In-memory cache for frequently used templates
        self._local_cache: Dict[str, Template] = {}
    
    async def get_template(self,
                          template_name: str,
                          template_source: str) -> Template:
        """
        Get compiled template from cache or compile and cache it.
        
        Implements cache lookup strategy:
        1. Check local memory cache (fastest)
        2. Check distributed cache
        3. Compile template if not found
        
        NOTE: Template compilation errors are logged and re-raised to allow
        proper error handling by the caller.
        
        IMPORTANT: Cache hits/misses are tracked via metrics to help optimize
        cache effectiveness and identify potential performance issues.
        """
        try:
            # Check local cache first
            if template_name in self._local_cache:
                self.metrics.increment(
                    "template_cache_hits",
                    {"cache": "local"}
                )
                return self._local_cache[template_name]
            
            # Generate cache key
            cache_key = self._generate_cache_key(template_name, template_source)
            
            # Try distributed cache
            cached = await self.cache.get(f"template:{cache_key}")
            if cached:
                self.metrics.increment(
                    "template_cache_hits",
                    {"cache": "distributed"}
                )
                template = Template(cached["source"])
                self._update_local_cache(template_name, template)
                return template
            
            # Compile template
            template = Template(template_source)
            
            # Cache template
            await self._cache_template(
                cache_key,
                template_name,
                template_source
            )
            
            # Update local cache
            self._update_local_cache(template_name, template)
            
            self.metrics.increment(
                "template_cache_misses",
                {"template": template_name}
            )
            
            return template
            
        except Exception as e:
            self.logger.error("template_cache_error",
                            template=template_name,
                            error=str(e))
            raise
    
    def _generate_cache_key(self,
                           template_name: str,
                           template_source: str) -> str:
        """
        Generate cache key based on template content.
        
        Uses SHA256 to create a unique identifier based on both name and content.
        This ensures cache invalidation when template content changes, even if
        the name remains the same.
        """
        content = f"{template_name}:{template_source}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _cache_template(self,
                            cache_key: str,
                            template_name: str,
                            template_source: str) -> None:
        """
        Cache template in distributed cache.
        
        Stores additional metadata (cached_at timestamp) to help with
        debugging and cache analysis.
        
        TODO: Consider adding version tracking for template changes
        """
        await self.cache.set(
            f"template:{cache_key}",
            {
                "name": template_name,
                "source": template_source,
                "cached_at": datetime.utcnow().isoformat()
            },
            ttl=int(self.ttl.total_seconds())
        )
    
    def _update_local_cache(self,
                           template_name: str,
                           template: Template) -> None:
        """
        Update local template cache with LRU eviction policy.
        
        FIXME: Current implementation uses a simple "oldest first" eviction strategy.
        Could be improved with a proper LRU implementation if access patterns show
        it's necessary.
        
        NOTE: The 100-template limit is a conservative choice to prevent memory bloat.
        Monitor metrics in production to adjust this value.
        """
        self._local_cache[template_name] = template
        
        # Limit local cache size
        if len(self._local_cache) > 100:  # Configurable limit
            # Remove least recently used template
            oldest = min(self._local_cache.keys())
            del self._local_cache[oldest]
    
    async def invalidate(self,
                        template_name: Optional[str] = None) -> None:
        """
        Invalidate cached templates.
        
        Supports two invalidation modes:
        1. Single template invalidation (when template_name is provided)
        2. Full cache invalidation (when template_name is None)
        
        IMPORTANT: This operation affects both local and distributed caches
        to maintain consistency. Consider the performance impact of frequent
        full cache invalidations.
        """
        try:
            if template_name:
                # Remove from local cache
                if template_name in self._local_cache:
                    del self._local_cache[template_name]
                
                # Remove from distributed cache
                pattern = f"template:*:{template_name}"
                keys = await self.cache.scan(pattern)
                for key in keys:
                    await self.cache.delete(key)
                
                self.logger.info("template_invalidated",
                               template=template_name)
            else:
                # Clear all templates
                self._local_cache.clear()
                
                pattern = "template:*"
                keys = await self.cache.scan(pattern)
                for key in keys:
                    await self.cache.delete(key)
                
                self.logger.info("all_templates_invalidated")
            
            self.metrics.increment(
                "template_cache_invalidations",
                {"template": template_name or "all"}
            )
            
        except Exception as e:
            self.logger.error("template_invalidation_failed",
                            template=template_name,
                            error=str(e))
            raise
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get template cache statistics for monitoring and debugging.
        
        Returns metrics about both local and distributed cache usage.
        Useful for:
        - Monitoring cache effectiveness
        - Debugging cache-related issues
        - Optimizing cache parameters
        
        NOTE: Returns empty dict on errors to prevent monitoring failures
        from affecting the main application flow.
        """
        try:
            pattern = "template:*"
            cached_keys = await self.cache.scan(pattern)
            
            return {
                "local_cache_size": len(self._local_cache),
                "distributed_cache_size": len(cached_keys),
                "local_templates": list(self._local_cache.keys()),
                "ttl_seconds": int(self.ttl.total_seconds())
            }
            
        except Exception as e:
            self.logger.error("cache_stats_failed",
                            error=str(e))
            return {} 