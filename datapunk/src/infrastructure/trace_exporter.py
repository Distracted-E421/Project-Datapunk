from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
import aiohttp
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .tracer import Span, SpanProcessor

logger = logging.getLogger(__name__)

@dataclass
class ExporterConfig:
    endpoint: str
    api_key: Optional[str] = None
    batch_size: int = 100
    flush_interval: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    tags: Optional[Dict[str, str]] = None

class TraceExporter(ABC):
    """Base class for trace exporters."""
    
    @abstractmethod
    async def export(self, spans: List[Span]) -> bool:
        """Export spans to the backend system."""
        pass

class ConsoleExporter(TraceExporter):
    """Exports traces to console for debugging."""
    
    async def export(self, spans: List[Span]) -> bool:
        for span in spans:
            logger.info(f"Trace: {span.context.trace_id}, Span: {span.name}")
        return True

class JsonFileExporter(TraceExporter):
    """Exports traces to a JSON file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
    
    async def export(self, spans: List[Span]) -> bool:
        try:
            # Convert spans to dict format
            span_data = []
            for span in spans:
                span_data.append({
                    "trace_id": span.context.trace_id,
                    "span_id": span.context.span_id,
                    "parent_span_id": span.context.parent_span_id,
                    "name": span.name,
                    "kind": span.kind.value,
                    "start_time": span.start_time.isoformat(),
                    "end_time": span.end_time.isoformat() if span.end_time else None,
                    "attributes": span.attributes,
                    "events": span.events,
                    "status": {
                        "code": span.status_code,
                        "message": span.status_message
                    } if span.status_code else None
                })
            
            # Append to file
            with open(self.filepath, 'a') as f:
                for data in span_data:
                    json.dump(data, f)
                    f.write('\n')
            
            return True
        except Exception as e:
            logger.error(f"Failed to export spans to file: {e}")
            return False

class HttpExporter(TraceExporter):
    """Exports traces to an HTTP endpoint."""
    
    def __init__(self, config: ExporterConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            if self.config.tags:
                headers.update(self.config.tags)
            
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session
    
    async def export(self, spans: List[Span]) -> bool:
        """Export spans to HTTP endpoint."""
        if not spans:
            return True
        
        # Convert spans to JSON format
        span_data = []
        for span in spans:
            span_data.append({
                "trace_id": span.context.trace_id,
                "span_id": span.context.span_id,
                "parent_span_id": span.context.parent_span_id,
                "name": span.name,
                "kind": span.kind.value,
                "start_time": span.start_time.isoformat(),
                "end_time": span.end_time.isoformat() if span.end_time else None,
                "attributes": span.attributes,
                "events": span.events,
                "status": {
                    "code": span.status_code,
                    "message": span.status_message
                } if span.status_code else None
            })
        
        payload = {
            "spans": span_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        session = await self._get_session()
        
        for attempt in range(self.config.retry_count):
            try:
                async with session.post(
                    self.config.endpoint,
                    json=payload
                ) as response:
                    if response.status < 400:
                        return True
                    
                    error_text = await response.text()
                    logger.error(
                        f"Failed to export spans (attempt {attempt + 1}): "
                        f"HTTP {response.status} - {error_text}"
                    )
            
            except Exception as e:
                logger.error(
                    f"Failed to export spans (attempt {attempt + 1}): {str(e)}"
                )
            
            if attempt < self.config.retry_count - 1:
                await asyncio.sleep(
                    self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                )
        
        return False
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

class BatchSpanProcessor(SpanProcessor):
    """Processes spans in batches for efficient exporting."""
    
    def __init__(self, exporter: TraceExporter, config: ExporterConfig):
        super().__init__()
        self.exporter = exporter
        self.config = config
        self._batch: List[Span] = []
        self._last_export = datetime.now()
        self._export_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def _export_batch(self) -> None:
        """Export the current batch of spans."""
        async with self._lock:
            if not self._batch:
                return
            
            spans_to_export = self._batch[:]
            self._batch = []
        
        success = await self.exporter.export(spans_to_export)
        if not success:
            logger.error(f"Failed to export {len(spans_to_export)} spans")
            # Could implement a retry queue here
    
    async def _run_export_loop(self) -> None:
        """Periodically export spans based on flush interval."""
        while True:
            try:
                await asyncio.sleep(self.config.flush_interval)
                await self._export_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in export loop: {e}")
    
    def on_end(self, span: Span) -> None:
        """Process a completed span."""
        super().on_end(span)
        
        self._batch.append(span)
        if len(self._batch) >= self.config.batch_size:
            asyncio.create_task(self._export_batch())
    
    async def start(self) -> None:
        """Start the batch processor."""
        if self._export_task is None:
            self._export_task = asyncio.create_task(self._run_export_loop())
    
    async def shutdown(self) -> None:
        """Shutdown the batch processor."""
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
            self._export_task = None
        
        # Export any remaining spans
        await self._export_batch()
        
        # Close exporter if it's an HTTP exporter
        if isinstance(self.exporter, HttpExporter):
            await self.exporter.close() 