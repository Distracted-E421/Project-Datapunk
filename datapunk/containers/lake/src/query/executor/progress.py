from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Callable
from abc import ABC, abstractmethod
import time
from datetime import datetime, timedelta
from enum import Enum, auto
from .core import ExecutionOperator, ExecutionContext
from ..parser.core import QueryNode, QueryPlan

class ProgressState(Enum):
    """Possible states for query progress."""
    NOT_STARTED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()

class ProgressMetrics:
    """Container for progress metrics."""
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.total_rows: int = 0
        self.processed_rows: int = 0
        self.estimated_total_rows: int = 0
        self.current_phase: str = ""
        self.state: ProgressState = ProgressState.NOT_STARTED
        self.error_message: Optional[str] = None
        
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.estimated_total_rows == 0:
            return 0.0
        return (self.processed_rows / self.estimated_total_rows) * 100
        
    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """Calculate elapsed time."""
        if not self.start_time:
            return None
        end = self.end_time or datetime.now()
        return end - self.start_time
        
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Estimate remaining time based on progress."""
        if not self.elapsed_time or self.progress_percentage == 0:
            return None
            
        elapsed_seconds = self.elapsed_time.total_seconds()
        total_estimated_seconds = (elapsed_seconds / 
                                 (self.progress_percentage / 100))
        remaining_seconds = total_estimated_seconds - elapsed_seconds
        
        return timedelta(seconds=remaining_seconds)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'estimated_total_rows': self.estimated_total_rows,
            'progress_percentage': self.progress_percentage,
            'current_phase': self.current_phase,
            'state': self.state.name,
            'error_message': self.error_message,
            'elapsed_time': str(self.elapsed_time) if self.elapsed_time else None,
            'estimated_remaining_time': str(self.estimated_remaining_time) 
                                     if self.estimated_remaining_time else None
        }

class ProgressTracker:
    """Tracks query execution progress."""
    
    def __init__(self):
        self.metrics = ProgressMetrics()
        self.progress_handlers: List[Callable[[ProgressMetrics], None]] = []
        self.update_interval: timedelta = timedelta(seconds=1)
        self.last_update: Optional[datetime] = None
        
    def start(self, estimated_total_rows: int = 0) -> None:
        """Start progress tracking."""
        self.metrics.start_time = datetime.now()
        self.metrics.estimated_total_rows = estimated_total_rows
        self.metrics.state = ProgressState.RUNNING
        self._notify_handlers()
        
    def update(self, rows_processed: int, 
              current_phase: Optional[str] = None) -> None:
        """Update progress metrics."""
        self.metrics.processed_rows = rows_processed
        if current_phase:
            self.metrics.current_phase = current_phase
            
        now = datetime.now()
        if (not self.last_update or 
            now - self.last_update >= self.update_interval):
            self._notify_handlers()
            self.last_update = now
            
    def pause(self) -> None:
        """Pause progress tracking."""
        self.metrics.state = ProgressState.PAUSED
        self._notify_handlers()
        
    def resume(self) -> None:
        """Resume progress tracking."""
        self.metrics.state = ProgressState.RUNNING
        self._notify_handlers()
        
    def complete(self) -> None:
        """Mark progress as complete."""
        self.metrics.end_time = datetime.now()
        self.metrics.state = ProgressState.COMPLETED
        self._notify_handlers()
        
    def fail(self, error_message: str) -> None:
        """Mark progress as failed."""
        self.metrics.end_time = datetime.now()
        self.metrics.state = ProgressState.FAILED
        self.metrics.error_message = error_message
        self._notify_handlers()
        
    def register_handler(self, 
                        handler: Callable[[ProgressMetrics], None]) -> None:
        """Register a progress update handler."""
        self.progress_handlers.append(handler)
        
    def _notify_handlers(self) -> None:
        """Notify all progress handlers."""
        for handler in self.progress_handlers:
            handler(self.metrics)

class ProgressContext(ExecutionContext):
    """Extended context with progress tracking."""
    
    def __init__(self):
        super().__init__()
        self.progress_tracker = ProgressTracker()
        
    def register_progress_handler(self, 
                                handler: Callable[[ProgressMetrics], None]) -> None:
        """Register a progress update handler."""
        self.progress_tracker.register_handler(handler)

class ProgressOperator(ExecutionOperator):
    """Base operator with progress tracking."""
    
    def __init__(self, node: QueryNode, context: ProgressContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        self.operator_id = str(id(self))
        self.row_count = 0
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with progress tracking."""
        self.context.progress_tracker.start()
        
        try:
            # Update phase
            self.context.progress_tracker.update(
                0, f"Executing {self.node.operation}")
                
            for row in super().execute():
                self.row_count += 1
                self.context.progress_tracker.update(self.row_count)
                yield row
                
            self.context.progress_tracker.complete()
            
        except Exception as e:
            self.context.progress_tracker.fail(str(e))
            raise

class ProgressAwareExecutionEngine:
    """Execution engine with progress tracking."""
    
    def __init__(self):
        self.context = ProgressContext()
        
    def execute_plan(self, plan: QueryPlan) -> Iterator[Dict[str, Any]]:
        """Execute a query plan with progress tracking."""
        # Estimate total rows
        estimated_rows = self._estimate_total_rows(plan.root)
        self.context.progress_tracker.start(estimated_rows)
        
        try:
            # Build and execute progress-aware tree
            root_operator = self._build_progress_tree(plan.root)
            yield from root_operator.execute()
            
        except Exception as e:
            self.context.progress_tracker.fail(str(e))
            raise
            
    def register_progress_handler(self, 
                                handler: Callable[[ProgressMetrics], None]) -> None:
        """Register a progress update handler."""
        self.context.register_progress_handler(handler)
        
    def _build_progress_tree(self, node: QueryNode) -> ProgressOperator:
        """Build a progress-aware execution tree."""
        operator = ProgressOperator(node, self.context)
        
        # Recursively build children
        for child in node.children:
            child_operator = self._build_progress_tree(child)
            operator.add_child(child_operator)
            
        return operator
        
    def _estimate_total_rows(self, node: QueryNode) -> int:
        """Estimate total rows to be processed."""
        # This is a simplified estimation
        # In practice, you would use statistics and cost models
        if hasattr(node, 'table_name'):
            # Get table statistics if available
            return 1000  # Default estimate
            
        child_estimates = sum(self._estimate_total_rows(child) 
                            for child in node.children)
            
        if node.operation == 'join':
            # Assume some selectivity
            return int(child_estimates * 0.8)
        elif node.operation == 'filter':
            # Assume some selectivity
            return int(child_estimates * 0.5)
        else:
            return child_estimates 