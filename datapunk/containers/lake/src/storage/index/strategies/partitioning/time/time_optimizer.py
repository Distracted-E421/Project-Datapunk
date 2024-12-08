from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .time_strategy import TimePartitionStrategy

class TemporalQueryOptimizer:
    def __init__(self, time_strategy: TimePartitionStrategy):
        self.time_strategy = time_strategy
        self.query_cache = {}
        self.pattern_history = []
        
    def optimize_temporal_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a temporal query based on historical patterns and partition layout"""
        time_range = self._extract_time_range(query)
        if not time_range:
            return query
            
        optimized_query = self._apply_temporal_optimizations(query, time_range)
        self._update_pattern_history(query)
        return optimized_query
        
    def _extract_time_range(self, query: Dict[str, Any]) -> Optional[tuple]:
        """Extract time range from query conditions"""
        time_field = self.time_strategy.time_field
        start_time = None
        end_time = None
        
        if 'conditions' in query:
            for condition in query['conditions']:
                if condition.get('field') == time_field:
                    if condition.get('operator') in ['>=', '>']:
                        start_time = condition.get('value')
                    elif condition.get('operator') in ['<=', '<']:
                        end_time = condition.get('value')
                        
        return (start_time, end_time) if start_time or end_time else None
        
    def _apply_temporal_optimizations(self, query: Dict[str, Any], time_range: tuple) -> Dict[str, Any]:
        """Apply temporal-specific optimizations"""
        optimized = query.copy()
        
        # Partition pruning
        relevant_partitions = self.time_strategy.get_partitions_for_range(*time_range)
        optimized['partitions'] = relevant_partitions
        
        # Time-based index selection
        if self._should_use_temporal_index(time_range):
            optimized['index'] = 'temporal'
            
        # Query rewrite for time-series patterns
        if self._has_time_series_pattern(query):
            optimized = self._rewrite_for_time_series(optimized)
            
        # Parallel scan optimization
        if len(relevant_partitions) > 1:
            optimized['parallel_scan'] = True
            optimized['partition_chunks'] = self._calculate_optimal_chunks(relevant_partitions)
            
        return optimized
        
    def _should_use_temporal_index(self, time_range: tuple) -> bool:
        """Determine if temporal index would be beneficial"""
        start_time, end_time = time_range
        if not (start_time and end_time):
            return False
            
        # Calculate range span
        try:
            range_span = pd.Timestamp(end_time) - pd.Timestamp(start_time)
            return range_span <= timedelta(days=30)  # Use temporal index for shorter ranges
        except:
            return False
            
    def _has_time_series_pattern(self, query: Dict[str, Any]) -> bool:
        """Detect if query follows time-series analysis pattern"""
        pattern_indicators = [
            'GROUP BY',
            'ORDER BY',
            'WINDOW',
            'time_bucket',
            'date_trunc'
        ]
        query_str = str(query).lower()
        return any(indicator.lower() in query_str for indicator in pattern_indicators)
        
    def _rewrite_for_time_series(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize query for time-series specific patterns"""
        optimized = query.copy()
        
        # Add time-series specific hints
        optimized['hints'] = optimized.get('hints', []) + ['time_series_scan']
        
        # Adjust chunk size for time-series processing
        if 'chunk_size' not in optimized:
            optimized['chunk_size'] = self._calculate_optimal_chunk_size()
            
        return optimized
        
    def _calculate_optimal_chunks(self, partitions: List[str]) -> List[List[str]]:
        """Calculate optimal partition chunks for parallel processing"""
        num_partitions = len(partitions)
        if num_partitions <= 1:
            return [partitions]
            
        # Determine chunk size based on available resources and partition count
        chunk_size = max(1, num_partitions // 4)  # Assume 4 parallel workers as default
        return [partitions[i:i + chunk_size] for i in range(0, num_partitions, chunk_size)]
        
    def _calculate_optimal_chunk_size(self) -> int:
        """Calculate optimal chunk size for time-series processing"""
        # Default to 10000 rows per chunk, adjust based on memory and CPU
        return 10000
        
    def _update_pattern_history(self, query: Dict[str, Any]):
        """Update query pattern history for future optimization"""
        self.pattern_history.append({
            'timestamp': datetime.now(),
            'pattern': self._extract_query_pattern(query)
        })
        
        # Maintain last 1000 patterns
        if len(self.pattern_history) > 1000:
            self.pattern_history = self.pattern_history[-1000:]
            
    def _extract_query_pattern(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key pattern characteristics from query"""
        return {
            'has_time_range': bool(self._extract_time_range(query)),
            'has_time_series': self._has_time_series_pattern(query),
            'aggregations': bool(query.get('aggregations')),
            'group_by': bool(query.get('group_by'))
        } 