from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Callable
from abc import ABC, abstractmethod
import time
import json
import pickle
import logging
from datetime import datetime, timedelta
from pathlib import Path
from .query_exec_core import ExecutionOperator, ExecutionContext
from ..parser.query_parser_core import QueryNode, QueryPlan

class CheckpointManager:
    """Manages operator checkpoints for fault tolerance."""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def save_checkpoint(self, operator_id: str, 
                       state: Dict[str, Any]) -> None:
        """Save operator state to checkpoint."""
        checkpoint_path = self.checkpoint_dir / f"{operator_id}.checkpoint"
        try:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(state, f)
            self.logger.info(f"Checkpoint saved for operator {operator_id}")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            
    def load_checkpoint(self, operator_id: str) -> Optional[Dict[str, Any]]:
        """Load operator state from checkpoint."""
        checkpoint_path = self.checkpoint_dir / f"{operator_id}.checkpoint"
        if not checkpoint_path.exists():
            return None
            
        try:
            with open(checkpoint_path, 'rb') as f:
                state = pickle.load(f)
            self.logger.info(f"Checkpoint loaded for operator {operator_id}")
            return state
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return None
            
    def clear_checkpoint(self, operator_id: str) -> None:
        """Clear operator checkpoint."""
        checkpoint_path = self.checkpoint_dir / f"{operator_id}.checkpoint"
        if checkpoint_path.exists():
            checkpoint_path.unlink()

class FailureDetector:
    """Detects and tracks operator failures."""
    
    def __init__(self, failure_threshold: int = 3,
                 recovery_timeout: timedelta = timedelta(minutes=5)):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_counts: Dict[str, int] = {}
        self.last_failure: Dict[str, datetime] = {}
        self.logger = logging.getLogger(__name__)
        
    def record_failure(self, operator_id: str) -> bool:
        """Record operator failure and check if recovery is needed."""
        now = datetime.now()
        
        if operator_id in self.last_failure:
            # Check if we're within recovery timeout
            if now - self.last_failure[operator_id] < self.recovery_timeout:
                self.failure_counts[operator_id] = \
                    self.failure_counts.get(operator_id, 0) + 1
            else:
                # Reset count if outside timeout
                self.failure_counts[operator_id] = 1
                
        else:
            self.failure_counts[operator_id] = 1
            
        self.last_failure[operator_id] = now
        
        # Check if threshold exceeded
        if self.failure_counts[operator_id] >= self.failure_threshold:
            self.logger.warning(
                f"Operator {operator_id} exceeded failure threshold"
            )
            return True
            
        return False
        
    def clear_failures(self, operator_id: str) -> None:
        """Clear failure history for an operator."""
        self.failure_counts.pop(operator_id, None)
        self.last_failure.pop(operator_id, None)

class FaultTolerantContext(ExecutionContext):
    """Extended context with fault tolerance support."""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        super().__init__()
        self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        self.failure_detector = FailureDetector()
        self.recovery_handlers: Dict[str, List[Callable]] = {}
        
    def register_recovery_handler(self, operator_id: str,
                                handler: Callable[[], None]) -> None:
        """Register a recovery handler for an operator."""
        if operator_id not in self.recovery_handlers:
            self.recovery_handlers[operator_id] = []
        self.recovery_handlers[operator_id].append(handler)
        
    def trigger_recovery(self, operator_id: str) -> None:
        """Trigger recovery handlers for an operator."""
        if operator_id in self.recovery_handlers:
            for handler in self.recovery_handlers[operator_id]:
                handler()

class FaultTolerantOperator(ExecutionOperator):
    """Base operator with fault tolerance capabilities."""
    
    def __init__(self, node: QueryNode, context: FaultTolerantContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        self.operator_id = str(id(self))
        self.state: Dict[str, Any] = {}
        self.checkpoint_interval = 1000  # Rows between checkpoints
        self.row_count = 0
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with fault tolerance."""
        # Try to restore from checkpoint
        saved_state = self.context.checkpoint_manager.load_checkpoint(
            self.operator_id)
        if saved_state:
            self.state = saved_state
            
        try:
            for row in self._execute_with_retries():
                self.row_count += 1
                
                # Periodic checkpointing
                if self.row_count % self.checkpoint_interval == 0:
                    self._save_checkpoint()
                    
                yield row
                
        except Exception as e:
            # Handle failure
            self._handle_failure(e)
            raise
            
    def _execute_with_retries(self) -> Iterator[Dict[str, Any]]:
        """Execute with retry logic."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                yield from super().execute()
                break
                
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                    
                # Record failure and check if recovery needed
                if self.context.failure_detector.record_failure(self.operator_id):
                    self.context.trigger_recovery(self.operator_id)
                    
                time.sleep(2 ** retry_count)  # Exponential backoff
                
    def _save_checkpoint(self) -> None:
        """Save operator state to checkpoint."""
        checkpoint_state = {
            'state': self.state,
            'row_count': self.row_count,
            'timestamp': datetime.now().isoformat()
        }
        self.context.checkpoint_manager.save_checkpoint(
            self.operator_id, checkpoint_state)
            
    def _handle_failure(self, error: Exception) -> None:
        """Handle operator failure."""
        logger = logging.getLogger(__name__)
        logger.error(f"Operator {self.operator_id} failed: {error}")
        
        # Save final state before failure
        self._save_checkpoint()
        
        # Record failure
        if self.context.failure_detector.record_failure(self.operator_id):
            self.context.trigger_recovery(self.operator_id)

class FaultTolerantExecutionEngine:
    """Execution engine with fault tolerance capabilities."""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.context = FaultTolerantContext(checkpoint_dir)
        
    def execute_plan(self, plan: QueryPlan) -> Iterator[Dict[str, Any]]:
        """Execute a query plan with fault tolerance."""
        # Build fault-tolerant execution tree
        root_operator = self._build_fault_tolerant_tree(plan.root)
        
        try:
            # Execute with fault tolerance
            yield from root_operator.execute()
            
        finally:
            # Clean up checkpoints
            self._cleanup_checkpoints(root_operator)
            
    def register_recovery_handler(self, operator_id: str,
                                handler: Callable[[], None]) -> None:
        """Register a recovery handler for an operator."""
        self.context.register_recovery_handler(operator_id, handler)
        
    def _build_fault_tolerant_tree(self, 
                                 node: QueryNode) -> FaultTolerantOperator:
        """Build a fault-tolerant execution tree."""
        operator = FaultTolerantOperator(node, self.context)
        
        # Recursively build children
        for child in node.children:
            child_operator = self._build_fault_tolerant_tree(child)
            operator.add_child(child_operator)
            
        return operator
        
    def _cleanup_checkpoints(self, operator: FaultTolerantOperator) -> None:
        """Clean up checkpoints after successful execution."""
        self.context.checkpoint_manager.clear_checkpoint(operator.operator_id)
        self.context.failure_detector.clear_failures(operator.operator_id)
        
        # Recursively clean up children
        for child in operator.children:
            if isinstance(child, FaultTolerantOperator):
                self._cleanup_checkpoints(child) 