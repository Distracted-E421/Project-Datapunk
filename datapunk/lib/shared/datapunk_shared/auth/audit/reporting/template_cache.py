"""Template caching system for audit reports."""
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
    """Caches compiled Jinja2 templates."""
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 ttl: timedelta = timedelta(hours=1)):
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
        
        Args:
            template_name: Name/identifier of template
            template_source: Source code of template
        
        Returns:
            Compiled Jinja2 template
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
        """Generate cache key based on template content."""
        content = f"{template_name}:{template_source}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _cache_template(self,
                            cache_key: str,
                            template_name: str,
                            template_source: str) -> None:
        """Cache template in distributed cache."""
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
        """Update local template cache."""
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
        
        Args:
            template_name: Specific template to invalidate, or None for all
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
        """Get template cache statistics."""
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