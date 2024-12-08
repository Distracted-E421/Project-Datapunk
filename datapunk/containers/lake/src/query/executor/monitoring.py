from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
from abc import ABC, abstractmethod
import time
import psutil
import logging
from datetime import datetime, timedelta
from .query_exec_core import ExecutionOperator, ExecutionContext
from ..parser.query_parser_core import QueryNode, QueryPlan

class PerformanceMetrics:
    """Container for performance metrics."""
    
    def __init__(self):
        self.execution_time: float = 0.0
        self.cpu_usage: float = 0.0
        self.memory_usage: int = 0
        self.rows_processed: int = 0
        self.rows_per_second: float = 0.0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.operator_metrics: Dict[str, Dict[str, Any]] = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'execution_time': self.execution_time,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'rows_processed': self.rows_processed,
            'rows_per_second': self.rows_per_second,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'operator_metrics': self.operator_metrics
        }

class PerformanceMonitor:
    """Monitors query execution performance."""
    
    def __init__(self, logging_interval: timedelta = timedelta(seconds=5)):
        self.metrics = PerformanceMetrics()
        self.start_time = None
        self.logging_interval = logging_interval
        self.last_log_time = None
        self.logger = logging.getLogger(__name__)
        
    def start_monitoring(self) -> None:
        """Start monitoring performance."""
        self.start_time = time.time()
        self.last_log_time = self.start_time
        self.metrics = PerformanceMetrics()
        
    def update_metrics(self, operator_id: str, 
                      metric_name: str, value: Any) -> None:
        """Update operator-specific metrics."""
        if operator_id not in self.metrics.operator_metrics:
            self.metrics.operator_metrics[operator_id] = {}
        self.metrics.operator_metrics[operator_id][metric_name] = value
        
        # Log metrics periodically
        current_time = time.time()
        if self.last_log_time and \
           current_time - self.last_log_time >= self.logging_interval.total_seconds():
            self._log_metrics()
            self.last_log_time = current_time
            
    def record_row_processed(self) -> None:
        """Record a processed row."""
        self.metrics.rows_processed += 1
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.metrics.rows_per_second = self.metrics.rows_processed / elapsed
            
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.metrics.cache_hits += 1
        
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.metrics.cache_misses += 1
        
    def stop_monitoring(self) -> PerformanceMetrics:
        """Stop monitoring and return metrics."""
        if self.start_time:
            self.metrics.execution_time = time.time() - self.start_time
            self.metrics.cpu_usage = psutil.cpu_percent()
            self.metrics.memory_usage = psutil.Process().memory_info().rss
            
        self._log_metrics()
        return self.metrics
        
    def _log_metrics(self) -> None:
        """Log current metrics."""
        metrics_dict = self.metrics.to_dict()
        self.logger.info("Performance Metrics: %s", metrics_dict)

class MonitoringContext(ExecutionContext):
    """Extended context with performance monitoring."""
    
    def __init__(self):
        super().__init__()
        self.monitor = PerformanceMonitor()
        
    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        self.monitor.start_monitoring()
        
    def stop_monitoring(self) -> PerformanceMetrics:
        """Stop monitoring and get metrics."""
        return self.monitor.stop_monitoring()

class MonitoredOperator(ExecutionOperator):
    """Base operator with performance monitoring."""
    
    def __init__(self, node: QueryNode, context: MonitoringContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        self.operator_id = str(id(self))
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with performance monitoring."""
        start_time = time.time()
        row_count = 0
        
        try:
            for row in super().execute():
                row_count += 1
                self.context.monitor.record_row_processed()
                
                if row_count % 1000 == 0:
                    # Update metrics periodically
                    elapsed = time.time() - start_time
                    self.context.monitor.update_metrics(
                        self.operator_id,
                        'rows_per_second',
                        row_count / elapsed
                    )
                    
                yield row
                
        finally:
            # Record final metrics
            elapsed = time.time() - start_time
            metrics = {
                'total_rows': row_count,
                'execution_time': elapsed,
                'rows_per_second': row_count / elapsed if elapsed > 0 else 0
            }
            
            for metric_name, value in metrics.items():
                self.context.monitor.update_metrics(
                    self.operator_id,
                    metric_name,
                    value
                )

class PerformanceAnalyzer:
    """Analyzes query performance and provides recommendations."""
    
    def analyze(self, metrics: PerformanceMetrics) -> List[str]:
        """Analyze metrics and generate recommendations."""
        recommendations = []
        
        # Analyze overall performance
        if metrics.rows_per_second < 1000:
            recommendations.append(
                "Query performance is below threshold. Consider optimization."
            )
            
        # Analyze cache efficiency
        total_cache_ops = metrics.cache_hits + metrics.cache_misses
        if total_cache_ops > 0:
            hit_ratio = metrics.cache_hits / total_cache_ops
            if hit_ratio < 0.8:
                recommendations.append(
                    f"Low cache hit ratio ({hit_ratio:.2%}). "
                    "Consider adjusting cache size or strategy."
                )
                
        # Analyze operator performance
        for op_id, op_metrics in metrics.operator_metrics.items():
            if 'rows_per_second' in op_metrics:
                rps = op_metrics['rows_per_second']
                if rps < 100:
                    recommendations.append(
                        f"Operator {op_id} has low throughput ({rps:.2f} rows/s). "
                        "Consider optimization."
                    )
                    
        # Analyze resource usage
        if metrics.cpu_usage > 80:
            recommendations.append(
                f"High CPU usage ({metrics.cpu_usage:.1f}%). "
                "Consider parallel execution."
            )
            
        if metrics.memory_usage > 1e9:  # 1GB
            recommendations.append(
                f"High memory usage ({metrics.memory_usage / 1e6:.1f} MB). "
                "Consider streaming execution."
            )
            
        return recommendations

class MonitoredExecutionEngine:
    """Execution engine with performance monitoring."""
    
    def __init__(self):
        self.context = MonitoringContext()
        self.analyzer = PerformanceAnalyzer()
        
    def execute_plan(self, plan: QueryPlan) -> Iterator[Dict[str, Any]]:
        """Execute a query plan with performance monitoring."""
        self.context.start_monitoring()
        
        try:
            # Build and execute monitored tree
            root_operator = self._build_monitored_tree(plan.root)
            yield from root_operator.execute()
            
        finally:
            # Stop monitoring and analyze
            metrics = self.context.stop_monitoring()
            recommendations = self.analyzer.analyze(metrics)
            
            # Log recommendations
            logger = logging.getLogger(__name__)
            for recommendation in recommendations:
                logger.info("Performance Recommendation: %s", recommendation)
                
    def _build_monitored_tree(self, node: QueryNode) -> ExecutionOperator:
        """Build an execution tree with monitoring."""
        operator = MonitoredOperator(node, self.context)
        
        # Recursively build children
        for child in node.children:
            child_operator = self._build_monitored_tree(child)
            operator.add_child(child_operator)
            
        return operator 