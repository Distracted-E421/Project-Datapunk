"""
Template cache management utilities for efficient template loading and consistency maintenance.

This module provides two main components:
1. TemplateCacheWarmer: Proactively loads and updates templates in cache to improve performance
2. TemplateCacheConsistencyChecker: Ensures synchronization between filesystem templates and cache

The caching system uses SHA-256 hashing of template content to detect changes and maintain consistency.
Templates are stored in the cache with a 'template:' prefix followed by their content hash.
"""
from typing import Dict, List, Set, Optional, Any, TYPE_CHECKING
import structlog
from datetime import datetime, timedelta
import asyncio
import hashlib
import json
from pathlib import Path

if TYPE_CHECKING:
    from ....cache import CacheClient
    from ....monitoring import MetricsClient

logger = structlog.get_logger()

class TemplateCacheWarmer:
    """
    Manages template preloading and periodic cache updates.
    
    Implements a background process that periodically scans template files and ensures
    they are cached for optimal performance. Uses content-based hashing to detect
    changes and avoid unnecessary cache updates.
    
    NOTE: The warmer runs continuously until explicitly stopped. Consider implementing
    a max retry count for error scenarios in production environments.
    """
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 template_dir: Path,
                 warm_interval: timedelta = timedelta(hours=1)):
        self.cache = cache_client
        self.metrics = metrics
        self.template_dir = template_dir
        self.warm_interval = warm_interval
        self.logger = logger.bind(component="cache_warmer")
        self._warming = False
    
    async def start_warming(self) -> None:
        """Start periodic cache warming."""
        if self._warming:
            return
            
        self._warming = True
        while self._warming:
            try:
                await self.warm_cache()
                await asyncio.sleep(self.warm_interval.total_seconds())
            except Exception as e:
                self.logger.error("cache_warming_failed",
                                error=str(e))
                self.metrics.increment("cache_warming_errors")
                await asyncio.sleep(60)  # Retry after error
    
    async def stop_warming(self) -> None:
        """Stop periodic cache warming."""
        self._warming = False
    
    async def warm_cache(self) -> None:
        """
        Warm the template cache with all templates.
        
        Scans the template directory for .j2 files and caches them if not already present.
        Uses content hashing to determine if templates need updating.
        
        IMPORTANT: This method handles each template independently to ensure partial success
        in case of individual template failures.
        
        Metrics tracked:
        - cache_warming_duration_seconds: Total time taken for warming
        - templates_loaded: Number of new templates cached
        - cache_warming_errors: Count of warming operation failures
        """
        try:
            start_time = datetime.utcnow()
            templates_loaded = 0
            
            # Load all template files
            for template_file in self.template_dir.glob("**/*.j2"):
                try:
                    template_name = template_file.stem
                    template_source = template_file.read_text()
                    
                    # Generate cache key
                    cache_key = self._generate_cache_key(
                        template_name,
                        template_source
                    )
                    
                    # Cache template if not exists
                    if not await self.cache.exists(f"template:{cache_key}"):
                        await self.cache.set(
                            f"template:{cache_key}",
                            {
                                "name": template_name,
                                "source": template_source,
                                "cached_at": datetime.utcnow().isoformat()
                            }
                        )
                        templates_loaded += 1
                        
                except Exception as e:
                    self.logger.error("template_load_failed",
                                    template=str(template_file),
                                    error=str(e))
                    continue
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Update metrics
            self.metrics.gauge(
                "cache_warming_duration_seconds",
                duration
            )
            self.metrics.gauge(
                "templates_loaded",
                templates_loaded
            )
            
            self.logger.info("cache_warming_completed",
                           duration=duration,
                           templates_loaded=templates_loaded)
            
        except Exception as e:
            self.logger.error("cache_warming_failed",
                            error=str(e))
            raise

    def _generate_cache_key(self,
                           template_name: str,
                           template_source: str) -> str:
        """
        Generates a unique cache key using template name and content.
        
        Uses SHA-256 to create a deterministic hash that changes whenever
        template content changes, ensuring cache invalidation on updates.
        
        NOTE: The template name is included in the hash to prevent collisions
        between different templates with identical content.
        """
        content = f"{template_name}:{template_source}"
        return hashlib.sha256(content.encode()).hexdigest()

class TemplateCacheConsistencyChecker:
    """
    Validates and maintains cache-filesystem template consistency.
    
    Performs bidirectional verification:
    1. Ensures all filesystem templates are properly cached
    2. Ensures no orphaned templates exist in cache
    3. Verifies template content matches between cache and filesystem
    
    TODO: Consider adding periodic automatic consistency checks on a schedule
    TODO: Add configuration for maximum allowed inconsistencies before alerting
    """
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 template_dir: Path):
        self.cache = cache_client
        self.metrics = metrics
        self.template_dir = template_dir
        self.logger = logger.bind(component="cache_checker")
    
    async def check_consistency(self) -> Dict[str, Any]:
        """
        Performs comprehensive cache-filesystem consistency verification.
        
        The check identifies three types of inconsistencies:
        1. missing_templates: Templates present in filesystem but not in cache
        2. outdated_templates: Templates with content mismatch between cache and filesystem
        3. orphaned_keys: Cache entries without corresponding filesystem templates
        
        Returns a detailed report of inconsistencies for either manual or automatic resolution.
        
        NOTE: This operation can be resource-intensive for large template sets.
        Consider rate limiting or scheduling during off-peak hours.
        """
        try:
            # Get all cached templates
            pattern = "template:*"
            cached_keys = await self.cache.scan(pattern)
            cached_templates = {}
            
            for key in cached_keys:
                template_data = await self.cache.get(key)
                if template_data:
                    cached_templates[template_data["name"]] = {
                        "key": key,
                        "source": template_data["source"],
                        "cached_at": template_data["cached_at"]
                    }
            
            # Check against filesystem
            missing_templates = []
            outdated_templates = []
            orphaned_keys = []
            
            # Check filesystem templates
            for template_file in self.template_dir.glob("**/*.j2"):
                template_name = template_file.stem
                template_source = template_file.read_text()
                
                if template_name not in cached_templates:
                    missing_templates.append(template_name)
                else:
                    cached = cached_templates[template_name]
                    if cached["source"] != template_source:
                        outdated_templates.append(template_name)
                    del cached_templates[template_name]
            
            # Remaining cached templates are orphaned
            orphaned_keys = [
                data["key"]
                for name, data in cached_templates.items()
            ]
            
            # Update metrics
            self.metrics.gauge("missing_templates", len(missing_templates))
            self.metrics.gauge("outdated_templates", len(outdated_templates))
            self.metrics.gauge("orphaned_templates", len(orphaned_keys))
            
            return {
                "consistent": not any([
                    missing_templates,
                    outdated_templates,
                    orphaned_keys
                ]),
                "missing_templates": missing_templates,
                "outdated_templates": outdated_templates,
                "orphaned_keys": orphaned_keys
            }
            
        except Exception as e:
            self.logger.error("consistency_check_failed",
                            error=str(e))
            self.metrics.increment("consistency_check_errors")
            raise
    
    async def fix_inconsistencies(self,
                                auto_fix: bool = False) -> Dict[str, Any]:
        """
        Resolves cache-filesystem inconsistencies either automatically or reports them.
        
        When auto_fix is enabled:
        - Adds missing templates to cache
        - Updates outdated template content
        - Removes orphaned cache entries
        
        IMPORTANT: This method performs a final consistency check after fixes to verify
        all issues were resolved. In some edge cases (e.g., concurrent template updates),
        inconsistencies might persist.
        
        Returns both initial and final consistency states for verification and auditing.
        """
        try:
            # Check consistency
            check_result = await self.check_consistency()
            actions_taken = []
            
            if auto_fix:
                # Add missing templates
                for template_name in check_result["missing_templates"]:
                    template_file = self.template_dir / f"{template_name}.j2"
                    if template_file.exists():
                        template_source = template_file.read_text()
                        cache_key = self._generate_cache_key(
                            template_name,
                            template_source
                        )
                        await self.cache.set(
                            f"template:{cache_key}",
                            {
                                "name": template_name,
                                "source": template_source,
                                "cached_at": datetime.utcnow().isoformat()
                            }
                        )
                        actions_taken.append(f"Added {template_name}")
                
                # Update outdated templates
                for template_name in check_result["outdated_templates"]:
                    template_file = self.template_dir / f"{template_name}.j2"
                    if template_file.exists():
                        template_source = template_file.read_text()
                        cache_key = self._generate_cache_key(
                            template_name,
                            template_source
                        )
                        await self.cache.set(
                            f"template:{cache_key}",
                            {
                                "name": template_name,
                                "source": template_source,
                                "cached_at": datetime.utcnow().isoformat()
                            }
                        )
                        actions_taken.append(f"Updated {template_name}")
                
                # Remove orphaned keys
                for key in check_result["orphaned_keys"]:
                    await self.cache.delete(key)
                    actions_taken.append(f"Removed {key}")
            
            # Recheck consistency
            final_state = await self.check_consistency()
            
            return {
                "initial_state": check_result,
                "actions_taken": actions_taken,
                "final_state": final_state,
                "fully_consistent": final_state["consistent"]
            }
            
        except Exception as e:
            self.logger.error("fix_inconsistencies_failed",
                            error=str(e))
            self.metrics.increment("fix_inconsistencies_errors")
            raise
    
    def _generate_cache_key(self,
                           template_name: str,
                           template_source: str) -> str:
        """
        Generates a unique cache key using template name and content.
        
        Uses SHA-256 to create a deterministic hash that changes whenever
        template content changes, ensuring cache invalidation on updates.
        
        NOTE: The template name is included in the hash to prevent collisions
        between different templates with identical content.
        """
        content = f"{template_name}:{template_source}"
        return hashlib.sha256(content.encode()).hexdigest() 