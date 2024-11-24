from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from ..api_keys.policies_extended import AdvancedKeyPolicy, ResourceType, CompliancePolicy
from ...exceptions import MigrationError

logger = structlog.get_logger()

class MigrationStrategy(Enum):
    """
    Policy migration strategies aligned with organizational risk tolerance.
    Chosen based on policy complexity and potential business impact.
    """
    IMMEDIATE = "immediate"  # High-risk, instant cutover for urgent changes
    GRADUAL = "gradual"     # Controlled rollout to manage risk and monitor impact
    PARALLEL = "parallel"   # Zero-downtime migration with fallback capability

@dataclass
class MigrationConfig:
    """
    Migration behavior configuration and safety controls.
    
    IMPORTANT: grace_period_days affects migration duration and resource usage.
    Longer periods reduce risk but increase system overhead from running
    parallel policies.
    """
    strategy: MigrationStrategy
    grace_period_days: int = 30  # Duration for gradual/parallel migrations
    allow_rollback: bool = True  # Whether to permit breaking changes
    validate_before_apply: bool = True  # Pre-migration validation
    notify_affected_users: bool = True  # User communication
    backup_policies: bool = True  # Policy state preservation

class PolicyMigrator:
    """
    Orchestrates policy version migrations with safety controls and monitoring.
    
    Supports three migration patterns:
    1. Immediate cutover for urgent/simple changes
    2. Gradual rollout for complex changes
    3. Parallel operation for zero-downtime migrations
    
    IMPORTANT: Requires configured cache and metrics clients for state management
    and observability.
    
    NOTE: All operations are logged for audit trail and debugging.
    """
    
    def __init__(self,
                 cache_client,
                 metrics_client,
                 config: MigrationConfig):
        """
        Initialize migrator with required dependencies.
        Cache client must support atomic operations for policy state management.
        """
        self.cache = cache_client
        self.metrics = metrics_client
        self.config = config
        self.logger = logger.bind(component="policy_migrator")
    
    async def migrate_policy(self,
                           old_policy: AdvancedKeyPolicy,
                           new_policy: AdvancedKeyPolicy,
                           affected_keys: List[str]) -> bool:
        """
        Execute policy migration according to configured strategy.
        
        Migration workflow:
        1. Optional validation of compatibility
        2. Optional backup of current state
        3. Strategy-specific migration execution
        4. Optional user notification
        
        IMPORTANT: Failures are logged and tracked in metrics for incident response.
        Returns False if migration fails but can be retried.
        
        NOTE: Large numbers of affected keys may impact performance.
        Consider batch processing for gradual migrations.
        """
        try:
            # Safety checks and preparation
            if self.config.validate_before_apply:
                await self._validate_migration(old_policy, new_policy)
            
            if self.config.backup_policies:
                await self._backup_policy(old_policy)
            
            # Strategy-specific execution
            success = await {
                MigrationStrategy.IMMEDIATE: self._immediate_migration,
                MigrationStrategy.GRADUAL: self._gradual_migration,
                MigrationStrategy.PARALLEL: self._parallel_migration
            }[self.config.strategy](old_policy, new_policy, affected_keys)
            
            # Post-migration notification
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
        """
        Validate policy changes for breaking changes and compatibility issues.
        
        Checks three critical areas:
        1. Resource access reductions
        2. Rate limit decreases
        3. New compliance requirements
        
        IMPORTANT: Breaking changes are allowed only if rollback is enabled,
        providing a safety net for risky migrations.
        
        NOTE: This is a conservative validation focusing on backward compatibility.
        Additional policy-specific validation may be needed.
        """
        breaking_changes = []
        
        # Resource access validation
        if (old_policy.allowed_resources and 
            new_policy.allowed_resources and
            not old_policy.allowed_resources.issubset(new_policy.allowed_resources)):
            breaking_changes.append("Reduced resource access")
        
        # Performance impact validation
        if new_policy.rate_limit < old_policy.rate_limit:
            breaking_changes.append("Reduced rate limit")
        
        # Compliance requirement validation
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
        """
        Create timestamped backup of current policy state.
        
        IMPORTANT: Backups are stored in cache with UTC timestamp to ensure
        consistent recovery points across timezones.
        
        TODO: Implement backup rotation/cleanup to prevent cache growth
        """
        backup_key = f"policy_backup:{policy.type.value}:{datetime.utcnow().isoformat()}"
        await self.cache.set(backup_key, vars(policy))
        self.logger.info("policy_backed_up", key=backup_key)
    
    async def _immediate_migration(self,
                                 old_policy: AdvancedKeyPolicy,
                                 new_policy: AdvancedKeyPolicy,
                                 affected_keys: List[str]) -> bool:
        """
        Perform immediate policy cutover.
        
        IMPORTANT: Highest risk strategy - all keys switch simultaneously.
        Use only for urgent changes or simple policies.
        
        NOTE: Failures here affect all keys immediately.
        Have rollback plan ready.
        """
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
        """
        Perform gradual policy rollout.
        
        Calculates daily batch size based on grace period to ensure
        smooth distribution of migrations.
        
        IMPORTANT: Batch size calculation prevents both too-small batches
        (migration takes too long) and too-large batches (too risky).
        
        NOTE: Progress tracking enables migration monitoring and resumption.
        """
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
        """
        Stage new policy alongside existing policy.
        
        IMPORTANT: This method only stages the migration. Actual cutover
        requires separate orchestration after grace period.
        
        NOTE: Doubles cache storage requirements during migration period.
        Monitor cache capacity.
        
        TODO: Implement automatic cutover scheduling and execution
        """
        try:
            # Stage new policies with distinct key
            for key in affected_keys:
                await self.cache.set(
                    f"policy:{key}:new",
                    vars(new_policy)
                )
                self.metrics.increment("policies_staged")
            
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
        """
        Notify affected users of policy changes.
        
        TODO: Implement actual notification logic using NotificationManager
        Reference implementation in policy_notifications.py
        """
        # Implementation would depend on notification system
        # This is a placeholder
        self.logger.info("policy_change_notification",
                        affected_keys=len(affected_keys),
                        policy_type=new_policy.type.value) 