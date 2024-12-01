from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
import numpy as np
from .core import QueryPlan

@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    io_reads: int = 0
    io_writes: int = 0
    network_bytes_sent: int = 0
    network_bytes_received: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0
    source_metrics: Dict[str, Dict[str, float]] = None

@dataclass
class SourceMetrics:
    """Metrics for a data source."""
    source_id: str
    avg_response_time_ms: float
    error_rate: float
    throughput_qps: float
    active_connections: int
    cache_hit_ratio: float
    resource_usage: Dict[str, float]

class FederationMonitor:
    """Monitors federated query execution."""
    
    def __init__(self):
        self.active_queries: Dict[str, QueryMetrics] = {}
        self.source_metrics: Dict[str, SourceMetrics] = {}
        self.history: List[QueryMetrics] = []
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    async def start_query(self, query_id: str, query: QueryPlan) -> None:
        """Start monitoring a query execution."""
        try:
            async with self._lock:
                self.active_queries[query_id] = QueryMetrics(
                    query_id=query_id,
                    start_time=datetime.utcnow(),
                    source_metrics={}
                )
                self.logger.info(f"Started monitoring query {query_id}")
        except Exception as e:
            self.logger.error(f"Error starting query monitoring: {e}")
    
    async def end_query(self, query_id: str) -> None:
        """End monitoring a query execution."""
        try:
            async with self._lock:
                if query_id in self.active_queries:
                    metrics = self.active_queries[query_id]
                    metrics.end_time = datetime.utcnow()
                    metrics.execution_time_ms = (
                        metrics.end_time - metrics.start_time
                    ).total_seconds() * 1000
                    
                    # Move to history
                    self.history.append(metrics)
                    del self.active_queries[query_id]
                    
                    # Trim history if needed
                    self._trim_history()
                    
                    self.logger.info(
                        f"Ended monitoring query {query_id} "
                        f"(execution time: {metrics.execution_time_ms:.2f}ms)"
                    )
        except Exception as e:
            self.logger.error(f"Error ending query monitoring: {e}")
    
    async def update_query_metrics(self,
                                 query_id: str,
                                 metrics: Dict[str, Any]) -> None:
        """Update metrics for an active query."""
        try:
            async with self._lock:
                if query_id in self.active_queries:
                    query_metrics = self.active_queries[query_id]
                    
                    # Update basic metrics
                    query_metrics.cpu_usage_percent = metrics.get(
                        'cpu_usage',
                        query_metrics.cpu_usage_percent
                    )
                    query_metrics.memory_usage_mb = metrics.get(
                        'memory_usage',
                        query_metrics.memory_usage_mb
                    )
                    query_metrics.io_reads += metrics.get('io_reads', 0)
                    query_metrics.io_writes += metrics.get('io_writes', 0)
                    query_metrics.network_bytes_sent += metrics.get(
                        'network_sent',
                        0
                    )
                    query_metrics.network_bytes_received += metrics.get(
                        'network_received',
                        0
                    )
                    query_metrics.cache_hits += metrics.get('cache_hits', 0)
                    query_metrics.cache_misses += metrics.get('cache_misses', 0)
                    query_metrics.error_count += metrics.get('errors', 0)
                    
                    # Update source-specific metrics
                    source_metrics = metrics.get('source_metrics', {})
                    for source_id, source_data in source_metrics.items():
                        if source_id not in query_metrics.source_metrics:
                            query_metrics.source_metrics[source_id] = {}
                        query_metrics.source_metrics[source_id].update(source_data)
        except Exception as e:
            self.logger.error(f"Error updating query metrics: {e}")
    
    async def update_source_metrics(self,
                                  source_id: str,
                                  metrics: Dict[str, Any]) -> None:
        """Update metrics for a data source."""
        try:
            async with self._lock:
                self.source_metrics[source_id] = SourceMetrics(
                    source_id=source_id,
                    avg_response_time_ms=metrics.get('avg_response_time', 0.0),
                    error_rate=metrics.get('error_rate', 0.0),
                    throughput_qps=metrics.get('throughput', 0.0),
                    active_connections=metrics.get('active_connections', 0),
                    cache_hit_ratio=metrics.get('cache_hit_ratio', 0.0),
                    resource_usage=metrics.get('resource_usage', {})
                )
        except Exception as e:
            self.logger.error(f"Error updating source metrics: {e}")
    
    def get_query_metrics(self, query_id: str) -> Optional[QueryMetrics]:
        """Get metrics for a specific query."""
        return self.active_queries.get(query_id)
    
    def get_source_metrics(self, source_id: str) -> Optional[SourceMetrics]:
        """Get metrics for a specific source."""
        return self.source_metrics.get(source_id)
    
    def get_active_queries(self) -> List[QueryMetrics]:
        """Get metrics for all active queries."""
        return list(self.active_queries.values())
    
    def get_historical_metrics(self,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> List[QueryMetrics]:
        """Get historical query metrics within a time range."""
        if not start_time:
            start_time = datetime.min
        if not end_time:
            end_time = datetime.max
        
        return [
            metrics for metrics in self.history
            if start_time <= metrics.start_time <= end_time
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        try:
            # Calculate summary statistics
            recent_queries = self.get_historical_metrics(
                start_time=datetime.utcnow() - timedelta(hours=1)
            )
            
            if not recent_queries:
                return {
                    'avg_execution_time_ms': 0.0,
                    'error_rate': 0.0,
                    'cache_hit_ratio': 0.0,
                    'qps': 0.0,
                    'source_stats': {}
                }
            
            # Calculate metrics
            execution_times = [
                q.execution_time_ms for q in recent_queries
                if q.execution_time_ms is not None
            ]
            
            total_errors = sum(q.error_count for q in recent_queries)
            total_cache_hits = sum(q.cache_hits for q in recent_queries)
            total_cache_attempts = sum(
                q.cache_hits + q.cache_misses
                for q in recent_queries
            )
            
            # Calculate source statistics
            source_stats = {}
            for source_id, metrics in self.source_metrics.items():
                source_stats[source_id] = {
                    'avg_response_time_ms': metrics.avg_response_time_ms,
                    'error_rate': metrics.error_rate,
                    'throughput_qps': metrics.throughput_qps
                }
            
            return {
                'avg_execution_time_ms': np.mean(execution_times) if execution_times else 0.0,
                'error_rate': total_errors / len(recent_queries),
                'cache_hit_ratio': total_cache_hits / total_cache_attempts if total_cache_attempts > 0 else 0.0,
                'qps': len(recent_queries) / 3600.0,  # Queries per second over last hour
                'source_stats': source_stats
            }
        except Exception as e:
            self.logger.error(f"Error generating performance summary: {e}")
            return {}
    
    def get_source_health(self) -> Dict[str, str]:
        """Get health status for all sources."""
        try:
            health = {}
            for source_id, metrics in self.source_metrics.items():
                # Determine health based on metrics
                if metrics.error_rate > 0.1:  # More than 10% errors
                    status = 'unhealthy'
                elif metrics.error_rate > 0.01:  # More than 1% errors
                    status = 'degraded'
                elif metrics.avg_response_time_ms > 1000:  # More than 1s avg response
                    status = 'degraded'
                else:
                    status = 'healthy'
                
                health[source_id] = status
            
            return health
        except Exception as e:
            self.logger.error(f"Error checking source health: {e}")
            return {}
    
    def _trim_history(self) -> None:
        """Trim historical metrics to prevent memory growth."""
        try:
            # Keep last 24 hours of data
            cutoff = datetime.utcnow() - timedelta(hours=24)
            self.history = [
                metrics for metrics in self.history
                if metrics.start_time >= cutoff
            ]
        except Exception as e:
            self.logger.error(f"Error trimming history: {e}")

class QueryProfiler:
    """Profiles query execution for performance analysis."""
    
    def __init__(self):
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def start_profiling(self, query_id: str, query: QueryPlan) -> None:
        """Start profiling a query execution."""
        try:
            self.profiles[query_id] = {
                'query': query,
                'start_time': datetime.utcnow(),
                'stages': [],
                'current_stage': None
            }
        except Exception as e:
            self.logger.error(f"Error starting profiling: {e}")
    
    async def end_profiling(self, query_id: str) -> None:
        """End profiling a query execution."""
        try:
            if query_id in self.profiles:
                profile = self.profiles[query_id]
                profile['end_time'] = datetime.utcnow()
                profile['total_time_ms'] = (
                    profile['end_time'] - profile['start_time']
                ).total_seconds() * 1000
                
                # Calculate stage percentages
                total_stage_time = sum(
                    stage['duration_ms']
                    for stage in profile['stages']
                )
                if total_stage_time > 0:
                    for stage in profile['stages']:
                        stage['percentage'] = (
                            stage['duration_ms'] / total_stage_time * 100
                        )
        except Exception as e:
            self.logger.error(f"Error ending profiling: {e}")
    
    async def start_stage(self,
                         query_id: str,
                         stage_name: str,
                         stage_type: str) -> None:
        """Start profiling a query execution stage."""
        try:
            if query_id in self.profiles:
                profile = self.profiles[query_id]
                
                # End previous stage if exists
                if profile['current_stage']:
                    await self.end_stage(query_id)
                
                # Start new stage
                profile['current_stage'] = {
                    'name': stage_name,
                    'type': stage_type,
                    'start_time': datetime.utcnow(),
                    'metrics': {}
                }
        except Exception as e:
            self.logger.error(f"Error starting stage profiling: {e}")
    
    async def end_stage(self, query_id: str) -> None:
        """End profiling current query execution stage."""
        try:
            if query_id in self.profiles:
                profile = self.profiles[query_id]
                if profile['current_stage']:
                    stage = profile['current_stage']
                    stage['end_time'] = datetime.utcnow()
                    stage['duration_ms'] = (
                        stage['end_time'] - stage['start_time']
                    ).total_seconds() * 1000
                    
                    profile['stages'].append(stage)
                    profile['current_stage'] = None
        except Exception as e:
            self.logger.error(f"Error ending stage profiling: {e}")
    
    async def update_stage_metrics(self,
                                 query_id: str,
                                 metrics: Dict[str, Any]) -> None:
        """Update metrics for current execution stage."""
        try:
            if query_id in self.profiles:
                profile = self.profiles[query_id]
                if profile['current_stage']:
                    profile['current_stage']['metrics'].update(metrics)
        except Exception as e:
            self.logger.error(f"Error updating stage metrics: {e}")
    
    def get_profile(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get complete profile for a query."""
        return self.profiles.get(query_id)
    
    def get_bottlenecks(self, query_id: str) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks in query execution."""
        try:
            bottlenecks = []
            profile = self.profiles.get(query_id)
            
            if profile and profile.get('stages'):
                # Find stages taking more than 20% of total time
                total_time = profile.get('total_time_ms', 0)
                if total_time > 0:
                    for stage in profile['stages']:
                        stage_time = stage.get('duration_ms', 0)
                        if stage_time / total_time > 0.2:
                            bottlenecks.append({
                                'stage_name': stage['name'],
                                'stage_type': stage['type'],
                                'duration_ms': stage_time,
                                'percentage': stage_time / total_time * 100,
                                'metrics': stage.get('metrics', {})
                            })
            
            return bottlenecks
        except Exception as e:
            self.logger.error(f"Error identifying bottlenecks: {e}")
            return []
    
    def get_optimization_suggestions(self,
                                  query_id: str) -> List[Dict[str, Any]]:
        """Get optimization suggestions based on profile."""
        try:
            suggestions = []
            bottlenecks = self.get_bottlenecks(query_id)
            
            for bottleneck in bottlenecks:
                stage_type = bottleneck['stage_type']
                metrics = bottleneck['metrics']
                
                if stage_type == 'join':
                    if metrics.get('rows_processed', 0) > 1000000:
                        suggestions.append({
                            'stage': bottleneck['stage_name'],
                            'issue': 'Large join operation',
                            'suggestion': 'Consider adding indexes or partitioning data'
                        })
                
                elif stage_type == 'network':
                    if metrics.get('bytes_transferred', 0) > 10 * 1024 * 1024:
                        suggestions.append({
                            'stage': bottleneck['stage_name'],
                            'issue': 'High network transfer',
                            'suggestion': 'Consider data locality or compression'
                        })
                
                elif stage_type == 'aggregate':
                    if metrics.get('memory_usage_mb', 0) > 1000:
                        suggestions.append({
                            'stage': bottleneck['stage_name'],
                            'issue': 'High memory usage in aggregation',
                            'suggestion': 'Consider streaming aggregation'
                        })
            
            return suggestions
        except Exception as e:
            self.logger.error(f"Error generating optimization suggestions: {e}")
            return []