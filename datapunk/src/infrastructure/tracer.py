from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging
import json
import asyncio
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

class SpanKind(Enum):
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"

@dataclass
class SpanContext:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    sampled: bool = True

@dataclass
class Span:
    name: str
    context: SpanContext
    kind: SpanKind
    start_time: datetime
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status_code: Optional[str] = None
    status_message: Optional[str] = None

class Sampler:
    """Determines which traces should be sampled."""
    
    def __init__(self, sample_rate: float = 1.0):
        """Initialize sampler with a rate between 0.0 and 1.0."""
        if not 0.0 <= sample_rate <= 1.0:
            raise ValueError("Sample rate must be between 0.0 and 1.0")
        self.sample_rate = sample_rate
    
    def should_sample(self, trace_id: str) -> bool:
        """Determine if a trace should be sampled."""
        if self.sample_rate >= 1.0:
            return True
        if self.sample_rate <= 0.0:
            return False
        
        # Use last 8 chars of trace_id as random value
        random_value = int(trace_id[-8:], 16) / 0xffffffff
        return random_value < self.sample_rate

class SpanProcessor:
    """Processes spans as they start and end."""
    
    def __init__(self):
        self.spans: Dict[str, List[Span]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def on_start(self, span: Span) -> None:
        """Process a span when it starts."""
        pass
    
    def on_end(self, span: Span) -> None:
        """Process a span when it ends."""
        with self._lock:
            self.spans[span.context.trace_id].append(span)
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace."""
        with self._lock:
            return self.spans.get(trace_id, [])
    
    def export_trace(self, trace_id: str) -> str:
        """Export a trace in JSON format."""
        spans = self.get_trace(trace_id)
        if not spans:
            return "{}"
        
        def span_to_dict(span: Span) -> Dict:
            return {
                "name": span.name,
                "trace_id": span.context.trace_id,
                "span_id": span.context.span_id,
                "parent_span_id": span.context.parent_span_id,
                "kind": span.kind.value,
                "start_time": span.start_time.isoformat(),
                "end_time": span.end_time.isoformat() if span.end_time else None,
                "attributes": span.attributes,
                "events": span.events,
                "status": {
                    "code": span.status_code,
                    "message": span.status_message
                } if span.status_code else None
            }
        
        trace_data = {
            "trace_id": trace_id,
            "spans": [span_to_dict(span) for span in spans]
        }
        return json.dumps(trace_data, indent=2)

class Tracer:
    """Main tracing interface."""
    
    def __init__(self, sampler: Optional[Sampler] = None):
        self.sampler = sampler or Sampler()
        self.processor = SpanProcessor()
        self._context_stack: List[SpanContext] = []
        self._local = threading.local()
    
    def get_current_span(self) -> Optional[SpanContext]:
        """Get the current span context."""
        if not hasattr(self._local, 'context_stack'):
            self._local.context_stack = []
        return self._local.context_stack[-1] if self._local.context_stack else None
    
    def start_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL,
                  attributes: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new span."""
        parent_context = self.get_current_span()
        
        if parent_context:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
            sampled = parent_context.sampled
        else:
            trace_id = str(uuid.uuid4())
            parent_span_id = None
            sampled = self.sampler.should_sample(trace_id)
        
        context = SpanContext(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            sampled=sampled
        )
        
        span = Span(
            name=name,
            context=context,
            kind=kind,
            start_time=datetime.now(),
            attributes=attributes or {}
        )
        
        if span.context.sampled:
            self.processor.on_start(span)
        
        return span
    
    def end_span(self, span: Span) -> None:
        """End a span."""
        if not span.end_time:
            span.end_time = datetime.now()
            if span.context.sampled:
                self.processor.on_end(span)
    
    @contextmanager
    def span(self, name: str, kind: SpanKind = SpanKind.INTERNAL,
            attributes: Optional[Dict[str, Any]] = None):
        """Context manager for creating and ending spans."""
        span = self.start_span(name, kind, attributes)
        if not hasattr(self._local, 'context_stack'):
            self._local.context_stack = []
        self._local.context_stack.append(span.context)
        
        try:
            yield span
        finally:
            self._local.context_stack.pop()
            self.end_span(span)
    
    def add_event(self, span: Span, name: str, 
                 attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to a span."""
        event = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "attributes": attributes or {}
        }
        span.events.append(event)
    
    def set_status(self, span: Span, code: str, message: Optional[str] = None) -> None:
        """Set the status of a span."""
        span.status_code = code
        span.status_message = message
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace."""
        return self.processor.get_trace(trace_id)
    
    def export_trace(self, trace_id: str) -> str:
        """Export a trace in JSON format."""
        return self.processor.export_trace(trace_id)

class AsyncTracer(Tracer):
    """Async version of the tracer."""
    
    def __init__(self, sampler: Optional[Sampler] = None):
        super().__init__(sampler)
        self._task_local = {}
    
    def get_current_span(self) -> Optional[SpanContext]:
        """Get the current span context for the current task."""
        task = asyncio.current_task()
        if task is None:
            return None
        
        task_id = id(task)
        if task_id not in self._task_local:
            self._task_local[task_id] = []
        
        context_stack = self._task_local[task_id]
        return context_stack[-1] if context_stack else None
    
    @contextmanager
    async def span(self, name: str, kind: SpanKind = SpanKind.INTERNAL,
                  attributes: Optional[Dict[str, Any]] = None):
        """Async context manager for creating and ending spans."""
        span = self.start_span(name, kind, attributes)
        task = asyncio.current_task()
        if task:
            task_id = id(task)
            if task_id not in self._task_local:
                self._task_local[task_id] = []
            self._task_local[task_id].append(span.context)
        
        try:
            yield span
        finally:
            if task:
                task_id = id(task)
                self._task_local[task_id].pop()
                if not self._task_local[task_id]:
                    del self._task_local[task_id]
            self.end_span(span) 