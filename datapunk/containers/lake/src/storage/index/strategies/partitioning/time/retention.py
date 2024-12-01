from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
from .strategy import TimePartitionStrategy

class RetentionPolicy:
    """Manages data retention policies for time-based partitions"""
    
    def __init__(self, time_strategy: TimePartitionStrategy):
        self.time_strategy = time_strategy
        self.policies: Dict[str, Dict[str, Any]] = {}
        
    def add_policy(self, name: str,
                  retention_period: timedelta,
                  granularity: str = None,
                  archive_location: Optional[str] = None,
                  compression: bool = True) -> None:
        """Add a new retention policy"""
        self.policies[name] = {
            'retention_period': retention_period,
            'granularity': granularity or self.time_strategy.default_granularity,
            'archive_location': archive_location,
            'compression': compression,
            'enabled': True
        }
        
    def disable_policy(self, name: str) -> None:
        """Disable a retention policy"""
        if name in self.policies:
            self.policies[name]['enabled'] = False
            
    def enable_policy(self, name: str) -> None:
        """Enable a retention policy"""
        if name in self.policies:
            self.policies[name]['enabled'] = True
            
    def get_expired_partitions(self, policy_name: str) -> List[str]:
        """Get list of partitions that have expired under a policy"""
        if policy_name not in self.policies or not self.policies[policy_name]['enabled']:
            return []
            
        policy = self.policies[policy_name]
        now = datetime.now(pytz.UTC)
        cutoff_time = now - policy['retention_period']
        
        expired_partitions = []
        for partition_key, stats in self.time_strategy.partition_stats.items():
            partition_end = self.time_strategy._normalize_timestamp(stats['end_time'])
            if partition_end < cutoff_time:
                expired_partitions.append(partition_key)
                
        return expired_partitions
    
    def should_archive_partition(self, partition_key: str) -> Dict[str, Any]:
        """Check if a partition should be archived under any policy"""
        results = {}
        
        for policy_name, policy in self.policies.items():
            if not policy['enabled'] or not policy['archive_location']:
                continue
                
            # Get partition end time
            stats = self.time_strategy.partition_stats.get(partition_key)
            if not stats:
                continue
                
            partition_end = self.time_strategy._normalize_timestamp(stats['end_time'])
            cutoff_time = datetime.now(pytz.UTC) - policy['retention_period']
            
            if partition_end < cutoff_time:
                results[policy_name] = {
                    'archive_location': policy['archive_location'],
                    'compression': policy['compression']
                }
                
        return results
    
    def get_policy_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all retention policies"""
        status = {}
        
        for policy_name, policy in self.policies.items():
            expired = self.get_expired_partitions(policy_name)
            status[policy_name] = {
                'enabled': policy['enabled'],
                'retention_period': str(policy['retention_period']),
                'granularity': policy['granularity'],
                'has_archive': bool(policy['archive_location']),
                'expired_partitions': len(expired),
                'next_expiration': None
            }
            
            # Find next partition to expire
            if policy['enabled']:
                now = datetime.now(pytz.UTC)
                cutoff_time = now - policy['retention_period']
                
                next_expiration = None
                for partition_key, stats in self.time_strategy.partition_stats.items():
                    partition_end = self.time_strategy._normalize_timestamp(stats['end_time'])
                    if partition_end >= cutoff_time:
                        if next_expiration is None or partition_end < next_expiration:
                            next_expiration = partition_end
                            
                if next_expiration:
                    status[policy_name]['next_expiration'] = next_expiration.isoformat()
                    
        return status
    
    def estimate_storage_impact(self) -> Dict[str, Dict[str, Any]]:
        """Estimate storage impact of retention policies"""
        impact = {}
        
        for policy_name, policy in self.policies.items():
            if not policy['enabled']:
                continue
                
            expired = self.get_expired_partitions(policy_name)
            total_records = 0
            total_size = 0
            
            for partition_key in expired:
                stats = self.time_strategy.partition_stats.get(partition_key)
                if stats:
                    total_records += stats['count']
                    # Estimate size based on record count (assuming average record size)
                    total_size += stats['count'] * 100  # Assume 100 bytes per record
                    
            impact[policy_name] = {
                'expired_partitions': len(expired),
                'total_records': total_records,
                'estimated_size_bytes': total_size,
                'requires_archival': bool(policy['archive_location']),
                'compression_enabled': policy['compression']
            }
            
        return impact 