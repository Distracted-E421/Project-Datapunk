from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Callable
from abc import ABC, abstractmethod
import time
import psutil
import threading
from datetime import datetime, timedelta
from .core import ExecutionOperator, ExecutionContext
from ..parser.core import QueryNode, QueryPlan

class ResourceLimits:
    """Container for resource limits."""
    
    def __init__(self, max_memory_mb: int = 1024,
                 max_cpu_percent: float = 80.0,
                 max_concurrent_queries: int = 10):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.max_concurrent_queries = max_concurrent_queries

class ResourceMetrics:
    """Container for resource usage metrics."""
    
    def __init__(self):
        self.memory_usage_mb: float = 0.0
        self.cpu_percent: float = 0.0
        self.active_queries: int = 0
        self.peak_memory_mb: float = 0.0
        self.peak_cpu_percent: float = 0.0
        self.query_queue_length: int = 0
        
    def update(self) -> None:
        """Update resource metrics."""
        process = psutil.Process()
        self.memory_usage_mb = process.memory_info().rss / (1024 * 1024)
        self.cpu_percent = process.cpu_percent()
        
        # Update peaks
        self.peak_memory_mb = max(self.peak_memory_mb, self.memory_usage_mb)
        self.peak_cpu_percent = max(self.peak_cpu_percent, self.cpu_percent)

class ResourceManager:
    """Manages query execution resources."""
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self.metrics = ResourceMetrics()
        self.query_semaphore = threading.Semaphore(
            self.limits.max_concurrent_queries)
        self.resource_lock = threading.Lock()
        self.query_queue: List[str] = []
        
    def acquire_resources(self, query_id: str) -> bool:
        """Attempt to acquire resources for a query."""
        # Check if resources are available
        with self.resource_lock:
            self.metrics.update()
            
            if (self.metrics.memory_usage_mb >= self.limits.max_memory_mb or
                self.metrics.cpu_percent >= self.limits.max_cpu_percent):
                return False
                
            # Add to queue if resources not immediately available
            if not self.query_semaphore.acquire(blocking=False):
                self.query_queue.append(query_id)
                self.metrics.query_queue_length = len(self.query_queue)
                return False
                
            self.metrics.active_queries += 1
            return True
            
    def release_resources(self, query_id: str) -> None:
        """Release resources held by a query."""
        with self.resource_lock:
            self.metrics.active_queries -= 1
            self.query_semaphore.release()
            
            # Process next query in queue
            if self.query_queue:
                next_query = self.query_queue.pop(0)
                self.metrics.query_queue_length = len(self.query_queue)
                self.acquire_resources(next_query)
                
    def get_metrics(self) -> Dict[str, Any]:
        """Get current resource metrics."""
        with self.resource_lock:
            self.metrics.update()
            return {
                'memory_usage_mb': self.metrics.memory_usage_mb,
                'cpu_percent': self.metrics.cpu_percent,
                'active_queries': self.metrics.active_queries,
                'peak_memory_mb': self.metrics.peak_memory_mb,
                'peak_cpu_percent': self.metrics.peak_cpu_percent,
                'query_queue_length': self.metrics.query_queue_length
            }

class ResourceContext(ExecutionContext):
    """Extended context with resource management."""
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        super().__init__()
        self.resource_manager = ResourceManager(limits)
        self.query_id: Optional[str] = None
        
    def set_query_id(self, query_id: str) -> None:
        """Set the current query ID."""
        self.query_id = query_id

class ResourceAwareOperator(ExecutionOperator):
    """Base operator with resource awareness."""
    
    def __init__(self, node: QueryNode, context: ResourceContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        self.operator_id = str(id(self))
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with resource management."""
        if not self.context.query_id:
            raise ValueError("Query ID not set in context")
            
        # Acquire resources
        if not self.context.resource_manager.acquire_resources(
            self.context.query_id):
            raise ResourceWarning(
                f"Insufficient resources for query {self.context.query_id}")
            
        try:
            yield from super().execute()
            
        finally:
            # Release resources
            self.context.resource_manager.release_resources(
                self.context.query_id)

class MemoryAwareOperator(ResourceAwareOperator):
    """Operator that manages its memory usage."""
    
    def __init__(self, node: QueryNode, context: ResourceContext,
                 batch_size: int = 1000):
        super().__init__(node, context)
        self.batch_size = batch_size
        self.buffer: List[Dict[str, Any]] = []
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with memory management."""
        for row in super().execute():
            self.buffer.append(row)
            
            if len(self.buffer) >= self.batch_size:
                yield from self._process_buffer()
                
        # Process remaining rows
        if self.buffer:
            yield from self._process_buffer()
            
    def _process_buffer(self) -> Iterator[Dict[str, Any]]:
        """Process and clear the buffer."""
        yield from self.buffer
        self.buffer.clear()

class CPUAwareOperator(ResourceAwareOperator):
    """Operator that manages its CPU usage."""
    
    def __init__(self, node: QueryNode, context: ResourceContext,
                 cpu_threshold: float = 80.0):
        super().__init__(node, context)
        self.cpu_threshold = cpu_threshold
        self.check_interval = 100  # Rows between CPU checks
        self.row_count = 0
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with CPU management."""
        for row in super().execute():
            self.row_count += 1
            
            # Periodically check CPU usage
            if self.row_count % self.check_interval == 0:
                cpu_percent = psutil.cpu_percent()
                if cpu_percent > self.cpu_threshold:
                    time.sleep(0.1)  # Back off if CPU usage is high
                    
            yield row

class ResourceAwareExecutionEngine:
    """Execution engine with resource management."""
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.context = ResourceContext(limits)
        
    def execute_plan(self, plan: QueryPlan, 
                    query_id: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Execute a query plan with resource management."""
        # Generate query ID if not provided
        if not query_id:
            query_id = f"query_{int(time.time())}"
            
        self.context.set_query_id(query_id)
        
        try:
            # Build and execute resource-aware tree
            root_operator = self._build_resource_tree(plan.root)
            yield from root_operator.execute()
            
        except ResourceWarning as e:
            # Handle resource constraints
            metrics = self.context.resource_manager.get_metrics()
            raise ResourceWarning(
                f"Query {query_id} failed due to resource constraints: {e}\n"
                f"Current metrics: {metrics}"
            )
            
    def get_resource_metrics(self) -> Dict[str, Any]:
        """Get current resource metrics."""
        return self.context.resource_manager.get_metrics()
        
    def _build_resource_tree(self, node: QueryNode) -> ResourceAwareOperator:
        """Build a resource-aware execution tree."""
        if node.operation in ('table_scan', 'join'):
            # Memory-intensive operations
            operator = MemoryAwareOperator(node, self.context)
        elif node.operation in ('aggregate', 'sort'):
            # CPU-intensive operations
            operator = CPUAwareOperator(node, self.context)
        else:
            operator = ResourceAwareOperator(node, self.context)
            
        # Recursively build children
        for child in node.children:
            child_operator = self._build_resource_tree(child)
            operator.add_child(child_operator)
            
        return operator 