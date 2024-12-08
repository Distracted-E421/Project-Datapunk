from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass
from datetime import datetime
import time
import cProfile
import pstats
import io
import threading
import logging
import json
import tracemalloc
from contextlib import contextmanager

@dataclass
class OperationProfile:
    """Detailed profile of an operation."""
    operation_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    cpu_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    io_operations: int = 0
    context: Dict[str, Any] = None
    children: List['OperationProfile'] = None

class ProfileCollector:
    """Collects and manages operation profiles."""
    
    def __init__(self):
        self.profiles: Dict[str, List[OperationProfile]] = {}
        self.current_operations: Dict[str, List[OperationProfile]] = {}
        self.lock = threading.Lock()
        
    def start_operation(
        self,
        query_id: str,
        operation_type: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Start profiling an operation."""
        operation = OperationProfile(
            operation_id=f"{query_id}_{operation_type}_{time.time_ns()}",
            operation_type=operation_type,
            start_time=datetime.now(),
            context=context or {},
            children=[]
        )
        
        with self.lock:
            if query_id not in self.current_operations:
                self.current_operations[query_id] = []
            self.current_operations[query_id].append(operation)
            
        return operation.operation_id
        
    def end_operation(
        self,
        query_id: str,
        operation_id: str,
        metrics: Dict[str, Any] = None
    ) -> None:
        """End profiling an operation."""
        with self.lock:
            if query_id in self.current_operations:
                for op in self.current_operations[query_id]:
                    if op.operation_id == operation_id:
                        op.end_time = datetime.now()
                        if metrics:
                            op.cpu_time_ms = metrics.get('cpu_time_ms', 0)
                            op.memory_usage_mb = metrics.get('memory_usage_mb', 0)
                            op.io_operations = metrics.get('io_operations', 0)
                        break
                        
    def get_profile(self, query_id: str) -> List[OperationProfile]:
        """Get profile for a query."""
        with self.lock:
            return self.profiles.get(query_id, [])

class DetailedProfiler:
    """Advanced profiling with CPU, memory, and IO tracking."""
    
    def __init__(self):
        self.collector = ProfileCollector()
        self.logger = logging.getLogger(__name__)
        
    @contextmanager
    def profile_operation(
        self,
        query_id: str,
        operation_type: str,
        context: Dict[str, Any] = None
    ):
        """Profile an operation with detailed metrics."""
        # Start profiling
        pr = cProfile.Profile()
        tracemalloc.start()
        pr.enable()
        
        # Start operation
        operation_id = self.collector.start_operation(
            query_id,
            operation_type,
            context
        )
        
        try:
            yield
        finally:
            # Stop profiling
            pr.disable()
            snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
            
            # Process metrics
            metrics = self._process_profile(pr, snapshot)
            
            # End operation
            self.collector.end_operation(query_id, operation_id, metrics)
            
    def _process_profile(
        self,
        pr: cProfile.Profile,
        snapshot: tracemalloc.Snapshot
    ) -> Dict[str, Any]:
        """Process profiling data."""
        # Process CPU profile
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        cpu_stats = s.getvalue()
        
        # Process memory snapshot
        top_stats = snapshot.statistics('lineno')
        memory_stats = sum(stat.size for stat in top_stats)
        
        return {
            'cpu_time_ms': float(ps.total_tt * 1000),
            'memory_usage_mb': memory_stats / (1024 * 1024),
            'cpu_stats': cpu_stats,
            'memory_stats': [
                {
                    'file': stat.traceback[0].filename,
                    'line': stat.traceback[0].lineno,
                    'size': stat.size
                }
                for stat in top_stats[:10]
            ]
        }

class QueryAnalyzer:
    """Analyzes query execution patterns."""
    
    def __init__(self):
        self.profiles: Dict[str, List[Dict[str, Any]]] = {}
        self.lock = threading.Lock()
        
    def add_profile(self, query_id: str, profile: List[OperationProfile]):
        """Add a query profile for analysis."""
        with self.lock:
            if query_id not in self.profiles:
                self.profiles[query_id] = []
            self.profiles[query_id].append(self._convert_profile(profile))
            
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze execution patterns across queries."""
        with self.lock:
            return {
                'operation_stats': self._analyze_operations(),
                'bottlenecks': self._identify_bottlenecks(),
                'recommendations': self._generate_recommendations()
            }
            
    def _convert_profile(
        self,
        profile: List[OperationProfile]
    ) -> Dict[str, Any]:
        """Convert profile to analyzable format."""
        return {
            'operations': [
                {
                    'type': op.operation_type,
                    'duration_ms': (
                        op.end_time - op.start_time
                    ).total_seconds() * 1000 if op.end_time else 0,
                    'cpu_time_ms': op.cpu_time_ms,
                    'memory_mb': op.memory_usage_mb,
                    'io_ops': op.io_operations
                }
                for op in profile
            ]
        }
        
    def _analyze_operations(self) -> Dict[str, Dict[str, float]]:
        """Analyze operation statistics."""
        stats = {}
        
        for profiles in self.profiles.values():
            for profile in profiles:
                for op in profile['operations']:
                    if op['type'] not in stats:
                        stats[op['type']] = {
                            'count': 0,
                            'avg_duration': 0.0,
                            'avg_cpu': 0.0,
                            'avg_memory': 0.0
                        }
                        
                    stats[op['type']]['count'] += 1
                    stats[op['type']]['avg_duration'] += op['duration_ms']
                    stats[op['type']]['avg_cpu'] += op['cpu_time_ms']
                    stats[op['type']]['avg_memory'] += op['memory_mb']
                    
        # Calculate averages
        for op_stats in stats.values():
            count = op_stats['count']
            if count > 0:
                op_stats['avg_duration'] /= count
                op_stats['avg_cpu'] /= count
                op_stats['avg_memory'] /= count
                
        return stats
        
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        stats = self._analyze_operations()
        
        # Check for slow operations
        for op_type, op_stats in stats.items():
            if op_stats['avg_duration'] > 1000:  # > 1s
                bottlenecks.append({
                    'type': 'slow_operation',
                    'operation': op_type,
                    'avg_duration': op_stats['avg_duration'],
                    'impact': 'high'
                })
                
            if op_stats['avg_memory'] > 500:  # > 500MB
                bottlenecks.append({
                    'type': 'high_memory',
                    'operation': op_type,
                    'avg_memory': op_stats['avg_memory'],
                    'impact': 'medium'
                })
                
        return bottlenecks
        
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate optimization recommendations."""
        recommendations = []
        bottlenecks = self._identify_bottlenecks()
        
        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'slow_operation':
                recommendations.append({
                    'target': bottleneck['operation'],
                    'issue': 'High execution time',
                    'recommendation': 'Consider adding indexes or optimizing query plan'
                })
                
            elif bottleneck['type'] == 'high_memory':
                recommendations.append({
                    'target': bottleneck['operation'],
                    'issue': 'High memory usage',
                    'recommendation': 'Consider streaming processing or pagination'
                })
                
        return recommendations

class PerformancePredictor:
    """Predicts query performance based on historical data."""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
    def add_execution(
        self,
        query_type: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Add query execution data."""
        with self.lock:
            self.history.append({
                'type': query_type,
                'metrics': metrics,
                'timestamp': datetime.now()
            })
            
    def predict_performance(
        self,
        query_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Predict query performance metrics."""
        with self.lock:
            # Find similar queries
            similar = [
                h for h in self.history
                if h['type'] == query_type
            ]
            
            if not similar:
                return {}
                
            # Calculate averages
            return {
                'expected_duration_ms': sum(
                    h['metrics'].get('execution_time_ms', 0)
                    for h in similar
                ) / len(similar),
                'expected_memory_mb': sum(
                    h['metrics'].get('memory_usage_mb', 0)
                    for h in similar
                ) / len(similar)
            } 