"""Utilities for template cache warming and consistency checks."""
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
    """Handles template cache warming and preloading."""
    
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
        """Warm the template cache with all templates."""
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
        """Generate cache key based on template content."""
        content = f"{template_name}:{template_source}"
        return hashlib.sha256(content.encode()).hexdigest()

class TemplateCacheConsistencyChecker:
    """Checks template cache consistency."""
    
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
        Check cache consistency with filesystem templates.
        
        Returns:
            Dict containing:
            - consistent: bool
            - missing_templates: List[str]
            - outdated_templates: List[str]
            - orphaned_keys: List[str]
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
        Fix cache inconsistencies.
        
        Args:
            auto_fix: If True, automatically fix issues
        
        Returns:
            Dict containing actions taken and remaining issues
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
        """Generate cache key based on template content."""
        content = f"{template_name}:{template_source}"
        return hashlib.sha256(content.encode()).hexdigest() 