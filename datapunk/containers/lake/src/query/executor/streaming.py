from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Callable
from abc import ABC, abstractmethod
import asyncio
from collections import deque
from datetime import datetime, timedelta
from .core import ExecutionOperator, ExecutionContext
from ..parser.core import QueryNode, QueryPlan

class StreamBuffer:
    """Buffer for streaming data."""
    
    def __init__(self, max_size: int = 1000, 
                 window_size: timedelta = timedelta(minutes=5)):
        self.max_size = max_size
        self.window_size = window_size
        self.buffer: deque = deque(maxlen=max_size)
        self.timestamps: deque = deque(maxlen=max_size)
        
    def add(self, item: Dict[str, Any]) -> None:
        """Add an item to the buffer."""
        now = datetime.now()
        self.buffer.append(item)
        self.timestamps.append(now)
        
        # Remove expired items
        while self.timestamps and \
              now - self.timestamps[0] > self.window_size:
            self.buffer.popleft()
            self.timestamps.popleft()
            
    def get_window(self) -> List[Dict[str, Any]]:
        """Get all items in the current window."""
        return list(self.buffer)
        
    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()
        self.timestamps.clear()

class StreamingContext(ExecutionContext):
    """Extended context with streaming support."""
    
    def __init__(self):
        super().__init__()
        self.stream_buffers: Dict[str, StreamBuffer] = {}
        self.stream_handlers: Dict[str, List[Callable]] = {}
        
    def get_buffer(self, stream_id: str) -> StreamBuffer:
        """Get or create a buffer for a stream."""
        if stream_id not in self.stream_buffers:
            self.stream_buffers[stream_id] = StreamBuffer()
        return self.stream_buffers[stream_id]
        
    def register_handler(self, stream_id: str, 
                        handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register a handler for stream events."""
        if stream_id not in self.stream_handlers:
            self.stream_handlers[stream_id] = []
        self.stream_handlers[stream_id].append(handler)
        
    def notify_handlers(self, stream_id: str, item: Dict[str, Any]) -> None:
        """Notify all handlers for a stream."""
        if stream_id in self.stream_handlers:
            for handler in self.stream_handlers[stream_id]:
                handler(item)

class StreamingOperator(ExecutionOperator):
    """Base class for streaming operators."""
    
    def __init__(self, node: QueryNode, context: StreamingContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        self.stream_id = str(id(self))
        
    async def process_stream(self) -> None:
        """Process streaming data."""
        pass

class WindowedAggregation(StreamingOperator):
    """Operator for windowed aggregation on streams."""
    
    def __init__(self, node: QueryNode, context: StreamingContext,
                 window_size: timedelta = timedelta(minutes=5),
                 slide_interval: timedelta = timedelta(minutes=1)):
        super().__init__(node, context)
        self.window_size = window_size
        self.slide_interval = slide_interval
        self.last_emit = datetime.now()
        
    async def process_stream(self) -> None:
        """Process streaming data with sliding windows."""
        while True:
            now = datetime.now()
            
            # Check if it's time to emit results
            if now - self.last_emit >= self.slide_interval:
                buffer = self.context.get_buffer(self.stream_id)
                window_data = buffer.get_window()
                
                if window_data:
                    # Compute aggregates
                    results = self._compute_aggregates(window_data)
                    
                    # Notify handlers
                    self.context.notify_handlers(self.stream_id, results)
                    
                self.last_emit = now
                
            await asyncio.sleep(0.1)  # Prevent CPU hogging
            
    def _compute_aggregates(self, 
                          window_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute aggregates for the window."""
        aggregates = self.node.aggregates or []
        results = {}
        
        for agg in aggregates:
            func = agg['function']
            col = agg['column']
            alias = agg['alias']
            
            values = [row[col] for row in window_data if col in row]
            
            if func == 'sum':
                results[alias] = sum(values)
            elif func == 'avg':
                results[alias] = sum(values) / len(values) if values else None
            elif func == 'min':
                results[alias] = min(values) if values else None
            elif func == 'max':
                results[alias] = max(values) if values else None
            elif func == 'count':
                results[alias] = len(values)
                
        return results

class StreamJoin(StreamingOperator):
    """Operator for streaming joins."""
    
    def __init__(self, node: QueryNode, context: StreamingContext,
                 left_stream_id: str, right_stream_id: str):
        super().__init__(node, context)
        self.left_stream_id = left_stream_id
        self.right_stream_id = right_stream_id
        
    async def process_stream(self) -> None:
        """Process streaming join."""
        while True:
            # Get current windows
            left_buffer = self.context.get_buffer(self.left_stream_id)
            right_buffer = self.context.get_buffer(self.right_stream_id)
            
            left_data = left_buffer.get_window()
            right_data = right_buffer.get_window()
            
            # Perform join
            join_condition = self.node.join_condition
            left_key = join_condition['left']
            right_key = join_condition['right']
            
            # Build hash table for right side
            right_hash = {}
            for right_row in right_data:
                key = right_row.get(right_key)
                if key is not None:
                    if key not in right_hash:
                        right_hash[key] = []
                    right_hash[key].append(right_row)
                    
            # Probe with left side
            for left_row in left_data:
                key = left_row.get(left_key)
                if key is not None and key in right_hash:
                    for right_row in right_hash[key]:
                        result = {**left_row, **right_row}
                        self.context.notify_handlers(self.stream_id, result)
                        
            await asyncio.sleep(0.1)  # Prevent CPU hogging

class StreamingExecutionEngine:
    """Execution engine for streaming queries."""
    
    def __init__(self):
        self.context = StreamingContext()
        self.operators: List[StreamingOperator] = []
        
    def add_stream(self, stream_id: str) -> None:
        """Add a new stream."""
        self.context.get_buffer(stream_id)
        
    def push_data(self, stream_id: str, data: Dict[str, Any]) -> None:
        """Push data to a stream."""
        buffer = self.context.get_buffer(stream_id)
        buffer.add(data)
        
    def register_query(self, plan: QueryPlan) -> str:
        """Register a streaming query."""
        operator = self._build_streaming_tree(plan.root)
        self.operators.append(operator)
        return operator.stream_id
        
    def register_handler(self, stream_id: str, 
                        handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register a handler for query results."""
        self.context.register_handler(stream_id, handler)
        
    async def start(self) -> None:
        """Start processing all streaming queries."""
        tasks = [
            asyncio.create_task(operator.process_stream())
            for operator in self.operators
        ]
        await asyncio.gather(*tasks)
        
    def _build_streaming_tree(self, node: QueryNode) -> StreamingOperator:
        """Build a streaming operator tree."""
        if node.operation == 'aggregate':
            operator = WindowedAggregation(node, self.context)
        elif node.operation == 'join':
            # Assume first two children are stream identifiers
            operator = StreamJoin(
                node, 
                self.context,
                node.children[0].stream_id,
                node.children[1].stream_id
            )
        else:
            operator = StreamingOperator(node, self.context)
            
        # Recursively build children
        for child in node.children:
            child_operator = self._build_streaming_tree(child)
            operator.add_child(child_operator)
            
        return operator 