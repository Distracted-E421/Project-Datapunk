from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from ..api_keys.policies_extended import AdvancedKeyPolicy, ResourceType, CompliancePolicy
from ...exceptions import MigrationError

logger = structlog.get_logger()

class MigrationStrategy(Enum):
    """Strategy for policy migration."""
    IMMEDIATE = "immediate"  # Apply changes immediately
    GRADUAL = "gradual"     # Phase in changes
    PARALLEL = "parallel"   # Run old and new simultaneously

@dataclass
class MigrationConfig:
    """Configuration for policy migration."""
    strategy: MigrationStrategy
    grace_period_days: int = 30
    allow_rollback: bool = True
    validate_before_apply: bool = True
    notify_affected_users: bool = True
    backup_policies: bool = True

class PolicyMigrator:
    """Handles policy version migrations."""
    
    def __init__(self,
                 cache_client,
                 metrics_client,
                 config: MigrationConfig):
        self.cache = cache_client
        self.metrics = metrics_client
        self.config = config
        self.logger = logger.bind(component="policy_migrator")
    
    async def migrate_policy(self,
                           old_policy: AdvancedKeyPolicy,
                           new_policy: AdvancedKeyPolicy,
                           affected_keys: List[str]) -> bool:
        """Migrate from old policy to new policy."""
        try:
            # Validate new policy
            if self.config.validate_before_apply:
                await self._validate_migration(old_policy, new_policy)
            
            # Backup existing policy
            if self.config.backup_policies:
                await self._backup_policy(old_policy)
            
            # Apply migration based on strategy
            if self.config.strategy == MigrationStrategy.IMMEDIATE:
                success = await self._immediate_migration(
                    old_policy,
                    new_policy,
                    affected_keys
                )
            elif self.config.strategy == MigrationStrategy.GRADUAL:
                success = await self._gradual_migration(
                    old_policy,
                    new_policy,
                    affected_keys
                )
            else:  # PARALLEL
                success = await self._parallel_migration(
                    old_policy,
                    new_policy,
                    affected_keys
                )
            
            # Notify affected users
            if success and self.config.notify_affected_users:
                await self._notify_users(affected_keys, new_policy)
            
            return success
            
        except Exception as e:
            self.logger.error("policy_migration_failed",
                            error=str(e))
            self.metrics.increment("policy_migration_failures")
            raise MigrationError(f"Policy migration failed: {str(e)}")
    
    async def _validate_migration(self,
                                old_policy: AdvancedKeyPolicy,
                                new_policy: AdvancedKeyPolicy) -> None:
        """Validate policy migration for compatibility."""
        # Check for breaking changes
        breaking_changes = []
        
        # Check resource access changes
        if (old_policy.allowed_resources and 
            new_policy.allowed_resources and
            not old_policy.allowed_resources.issubset(new_policy.allowed_resources)):
            breaking_changes.append("Reduced resource access")
        
        # Check rate limit reductions
        if new_policy.rate_limit < old_policy.rate_limit:
            breaking_changes.append("Reduced rate limit")
        
        # Check compliance requirements
        if (not old_policy.compliance and new_policy.compliance) or \
           (old_policy.compliance and new_policy.compliance and 
            new_policy.compliance.encryption_required and 
            not old_policy.compliance.encryption_required):
            breaking_changes.append("Added compliance requirements")
        
        if breaking_changes:
            self.logger.warning("breaking_changes_detected",
                              changes=breaking_changes)
            if not self.config.allow_rollback:
                raise MigrationError(f"Breaking changes detected: {breaking_changes}")
    
    async def _backup_policy(self, policy: AdvancedKeyPolicy) -> None:
        """Backup existing policy before migration."""
        backup_key = f"policy_backup:{policy.type.value}:{datetime.utcnow().isoformat()}"
        await self.cache.set(backup_key, vars(policy))
        self.logger.info("policy_backed_up", key=backup_key)
    
    async def _immediate_migration(self,
                                 old_policy: AdvancedKeyPolicy,
                                 new_policy: AdvancedKeyPolicy,
                                 affected_keys: List[str]) -> bool:
        """Perform immediate policy migration."""
        try:
            for key in affected_keys:
                await self.cache.set(f"policy:{key}", vars(new_policy))
                self.metrics.increment("policies_migrated")
            
            self.logger.info("immediate_migration_complete",
                           affected_keys=len(affected_keys))
            return True
            
        except Exception as e:
            self.logger.error("immediate_migration_failed",
                            error=str(e))
            return False
    
    async def _gradual_migration(self,
                               old_policy: AdvancedKeyPolicy,
                               new_policy: AdvancedKeyPolicy,
                               affected_keys: List[str]) -> bool:
        """Perform gradual policy migration."""
        try:
            batch_size = max(1, len(affected_keys) // self.config.grace_period_days)
            
            for i in range(0, len(affected_keys), batch_size):
                batch = affected_keys[i:i + batch_size]
                
                for key in batch:
                    await self.cache.set(f"policy:{key}", vars(new_policy))
                    self.metrics.increment("policies_migrated")
                
                self.logger.info("gradual_migration_progress",
                               migrated=i + len(batch),
                               total=len(affected_keys))
            
            return True
            
        except Exception as e:
            self.logger.error("gradual_migration_failed",
                            error=str(e))
            return False
    
    async def _parallel_migration(self,
                                old_policy: AdvancedKeyPolicy,
                                new_policy: AdvancedKeyPolicy,
                                affected_keys: List[str]) -> bool:
        """Run old and new policies in parallel."""
        try:
            # Store new policy alongside old
            for key in affected_keys:
                await self.cache.set(
                    f"policy:{key}:new",
                    vars(new_policy)
                )
                self.metrics.increment("policies_staged")
            
            # After grace period, switch to new policy
            # This would be triggered by a separate process
            self.logger.info("parallel_migration_staged",
                           affected_keys=len(affected_keys))
            return True
            
        except Exception as e:
            self.logger.error("parallel_migration_failed",
                            error=str(e))
            return False
    
    async def _notify_users(self,
                           affected_keys: List[str],
                           new_policy: AdvancedKeyPolicy) -> None:
        """Notify affected users of policy changes."""
        # Implementation would depend on notification system
        # This is a placeholder
        self.logger.info("policy_change_notification",
                        affected_keys=len(affected_keys),
                        policy_type=new_policy.type.value) 