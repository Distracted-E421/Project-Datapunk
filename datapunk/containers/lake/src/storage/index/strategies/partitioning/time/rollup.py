from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .strategy import TimePartitionStrategy

class TimeRollup:
    """Manages time-based data rollups and aggregations"""
    
    def __init__(self, time_strategy: TimePartitionStrategy):
        self.time_strategy = time_strategy
        self.rollup_functions: Dict[str, Dict[str, Any]] = {}
        self.cached_rollups: Dict[str, Dict[str, Any]] = {}
        
    def register_rollup(self, name: str,
                       source_granularity: str,
                       target_granularity: str,
                       aggregation_functions: Dict[str, Callable],
                       trigger_threshold: int = 1000) -> None:
        """Register a new rollup configuration"""
        self.rollup_functions[name] = {
            'source_granularity': source_granularity,
            'target_granularity': target_granularity,
            'aggregation_functions': aggregation_functions,
            'trigger_threshold': trigger_threshold,
            'enabled': True
        }
        
    def disable_rollup(self, name: str) -> None:
        """Disable a rollup configuration"""
        if name in self.rollup_functions:
            self.rollup_functions[name]['enabled'] = False
            
    def enable_rollup(self, name: str) -> None:
        """Enable a rollup configuration"""
        if name in self.rollup_functions:
            self.rollup_functions[name]['enabled'] = True
            
    def _apply_aggregations(self, data: List[Dict[str, Any]],
                          aggregation_functions: Dict[str, Callable]) -> Dict[str, Any]:
        """Apply aggregation functions to data"""
        df = pd.DataFrame(data)
        result = {}
        
        for field, func in aggregation_functions.items():
            if field in df.columns:
                try:
                    result[field] = func(df[field])
                except Exception as e:
                    result[field] = None
                    
        return result
    
    def should_trigger_rollup(self, partition_key: str) -> List[str]:
        """Check if any rollups should be triggered for a partition"""
        triggers = []
        partition_stats = self.time_strategy.partition_stats.get(partition_key)
        
        if not partition_stats:
            return triggers
            
        for name, config in self.rollup_functions.items():
            if not config['enabled']:
                continue
                
            if (config['source_granularity'] == 
                self.time_strategy._get_partition_key(
                    partition_stats['end_time'], 
                    config['source_granularity'])):
                    
                if partition_stats['count'] >= config['trigger_threshold']:
                    triggers.append(name)
                    
        return triggers
    
    def execute_rollup(self, rollup_name: str,
                      partition_keys: List[str]) -> Optional[Dict[str, Any]]:
        """Execute a rollup on specified partitions"""
        if rollup_name not in self.rollup_functions:
            return None
            
        config = self.rollup_functions[rollup_name]
        if not config['enabled']:
            return None
            
        # Collect data from all partitions
        all_data = []
        for key in partition_keys:
            if key in self.time_strategy.partitions:
                all_data.extend(self.time_strategy.partitions[key])
                
        if not all_data:
            return None
            
        # Apply aggregations
        result = self._apply_aggregations(all_data, config['aggregation_functions'])
        
        # Store in cache
        cache_key = f"{rollup_name}_{min(partition_keys)}_{max(partition_keys)}"
        self.cached_rollups[cache_key] = {
            'timestamp': datetime.now(),
            'source_partitions': partition_keys,
            'data': result
        }
        
        return result
    
    def get_rollup_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all rollup configurations"""
        status = {}
        
        for name, config in self.rollup_functions.items():
            pending_rollups = 0
            for partition_key in self.time_strategy.partition_stats:
                if name in self.should_trigger_rollup(partition_key):
                    pending_rollups += 1
                    
            status[name] = {
                'enabled': config['enabled'],
                'source_granularity': config['source_granularity'],
                'target_granularity': config['target_granularity'],
                'trigger_threshold': config['trigger_threshold'],
                'pending_rollups': pending_rollups,
                'cached_results': len([k for k in self.cached_rollups if k.startswith(name)])
            }
            
        return status
    
    def get_cached_rollup(self, rollup_name: str,
                         start_time: datetime,
                         end_time: datetime) -> Optional[Dict[str, Any]]:
        """Retrieve cached rollup results for a time range"""
        matching_caches = []
        
        for cache_key, cache_data in self.cached_rollups.items():
            if not cache_key.startswith(rollup_name):
                continue
                
            source_partitions = cache_data['source_partitions']
            partition_start = min(
                self.time_strategy.partition_stats[p]['start_time'] 
                for p in source_partitions
            )
            partition_end = max(
                self.time_strategy.partition_stats[p]['end_time'] 
                for p in source_partitions
            )
            
            if (partition_start <= end_time and 
                partition_end >= start_time):
                matching_caches.append(cache_data)
                
        if not matching_caches:
            return None
            
        # Return most recent cache
        return max(matching_caches, key=lambda x: x['timestamp'])
    
    def cleanup_cache(self, max_age: timedelta = timedelta(hours=24)) -> int:
        """Clean up old cached rollups"""
        current_time = datetime.now()
        expired_keys = [
            key for key, data in self.cached_rollups.items()
            if current_time - data['timestamp'] > max_age
        ]
        
        for key in expired_keys:
            del self.cached_rollups[key]
            
        return len(expired_keys)
    
    def estimate_resource_usage(self) -> Dict[str, Dict[str, Any]]:
        """Estimate resource usage of rollup operations"""
        usage = {}
        
        for name, config in self.rollup_functions.items():
            if not config['enabled']:
                continue
                
            pending_partitions = []
            total_records = 0
            
            for partition_key, stats in self.time_strategy.partition_stats.items():
                if name in self.should_trigger_rollup(partition_key):
                    pending_partitions.append(partition_key)
                    total_records += stats['count']
                    
            # Estimate memory usage (assuming 1KB per record during processing)
            estimated_memory = total_records * 1024
            
            usage[name] = {
                'pending_partitions': len(pending_partitions),
                'total_records': total_records,
                'estimated_memory_bytes': estimated_memory,
                'estimated_processing_time': total_records * 0.001  # Assume 1ms per record
            }
            
        return usage 