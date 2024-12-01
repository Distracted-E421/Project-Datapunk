from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime
import aiofiles
import aiohttp
from pathlib import Path
import logging
from .core import DataSource
from .handlers import RetryHandler, ExponentialBackoff

logger = logging.getLogger(__name__)

class SourceHandler(ABC):
    """Base class for all data source handlers"""
    
    @abstractmethod
    async def process(self, data: Any) -> Dict[str, Any]:
        """Process incoming data into a standardized format"""
        pass
        
    @abstractmethod
    async def validate_source(self) -> bool:
        """Validate the data source configuration"""
        pass

class StructuredDataHandler(SourceHandler):
    """Handler for structured data sources (CSV, JSON, SQL)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.retry_handler = RetryHandler(
            ExponentialBackoff(max_attempts=3)
        )
        
    async def process(self, data: Any) -> Dict[str, Any]:
        """Process structured data into standardized format"""
        if isinstance(data, (str, Path)):
            return await self._process_file(data)
        elif isinstance(data, dict):
            return await self._process_dict(data)
        elif isinstance(data, (pd.DataFrame, pd.Series)):
            return await self._process_pandas(data)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
            
    async def _process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process data from file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        async def read_operation():
            async with aiofiles.open(file_path, mode='r') as f:
                content = await f.read()
                
            if file_path.suffix.lower() == '.json':
                return json.loads(content)
            elif file_path.suffix.lower() == '.csv':
                # Use pandas for CSV processing
                return pd.read_csv(file_path).to_dict(orient='records')
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
                
        return await self.retry_handler.execute_with_retry(read_operation)
        
    async def _process_dict(self, data: Dict) -> Dict[str, Any]:
        """Process dictionary data"""
        return {
            "data": data,
            "metadata": {
                "source_type": "structured",
                "timestamp": datetime.utcnow().isoformat(),
                "format": "dict"
            }
        }
        
    async def _process_pandas(self, data: Union[pd.DataFrame, pd.Series]) -> Dict[str, Any]:
        """Process pandas data structures"""
        return {
            "data": data.to_dict(orient='records') if isinstance(data, pd.DataFrame) else data.to_dict(),
            "metadata": {
                "source_type": "structured",
                "timestamp": datetime.utcnow().isoformat(),
                "format": "pandas",
                "shape": data.shape if hasattr(data, 'shape') else None
            }
        }
        
    async def validate_source(self) -> bool:
        """Validate structured data source configuration"""
        required_fields = ["format", "schema"]
        return all(field in self.config for field in required_fields)

class UnstructuredDataHandler(SourceHandler):
    """Handler for unstructured data sources (text, images, binary)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.retry_handler = RetryHandler(
            ExponentialBackoff(max_attempts=3)
        )
        self.supported_mime_types = {
            'text': ['text/plain', 'text/html', 'text/markdown'],
            'image': ['image/jpeg', 'image/png', 'image/gif'],
            'binary': ['application/octet-stream']
        }
        
    async def process(self, data: Any) -> Dict[str, Any]:
        """Process unstructured data into standardized format"""
        if isinstance(data, (str, Path)):
            return await self._process_file(data)
        elif isinstance(data, bytes):
            return await self._process_binary(data)
        elif isinstance(data, str):
            return await self._process_text(data)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
            
    async def _process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process unstructured file data"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        async def read_operation():
            import mimetypes
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            if mime_type in self.supported_mime_types['text']:
                async with aiofiles.open(file_path, mode='r') as f:
                    content = await f.read()
                return await self._process_text(content)
            else:
                async with aiofiles.open(file_path, mode='rb') as f:
                    content = await f.read()
                return await self._process_binary(content)
                
        return await self.retry_handler.execute_with_retry(read_operation)
        
    async def _process_binary(self, data: bytes) -> Dict[str, Any]:
        """Process binary data"""
        return {
            "data": data,
            "metadata": {
                "source_type": "unstructured",
                "timestamp": datetime.utcnow().isoformat(),
                "format": "binary",
                "size": len(data)
            }
        }
        
    async def _process_text(self, data: str) -> Dict[str, Any]:
        """Process text data"""
        return {
            "data": data,
            "metadata": {
                "source_type": "unstructured",
                "timestamp": datetime.utcnow().isoformat(),
                "format": "text",
                "length": len(data)
            }
        }
        
    async def validate_source(self) -> bool:
        """Validate unstructured data source configuration"""
        required_fields = ["type", "max_size"]
        return all(field in self.config for field in required_fields)

class StreamDataHandler(SourceHandler):
    """Handler for streaming data sources (Kafka, MQTT, WebSocket)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.retry_handler = RetryHandler(
            ExponentialBackoff(max_attempts=3)
        )
        self.buffer: List[Dict[str, Any]] = []
        self.buffer_size = config.get('buffer_size', 1000)
        self.flush_interval = config.get('flush_interval', 60)  # seconds
        self._flush_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the stream handler"""
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
    async def stop(self):
        """Stop the stream handler"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush_buffer()
        
    async def process(self, data: Any) -> Dict[str, Any]:
        """Process streaming data"""
        processed = await self._process_stream_data(data)
        await self._buffer_data(processed)
        return processed
        
    async def _process_stream_data(self, data: Any) -> Dict[str, Any]:
        """Process individual stream message"""
        if isinstance(data, bytes):
            try:
                decoded = data.decode('utf-8')
                data = json.loads(decoded)
            except (UnicodeDecodeError, json.JSONDecodeError):
                # Handle binary data
                return await self._process_binary_stream(data)
        
        return {
            "data": data,
            "metadata": {
                "source_type": "stream",
                "timestamp": datetime.utcnow().isoformat(),
                "sequence": len(self.buffer)
            }
        }
        
    async def _process_binary_stream(self, data: bytes) -> Dict[str, Any]:
        """Process binary stream data"""
        return {
            "data": data,
            "metadata": {
                "source_type": "stream",
                "timestamp": datetime.utcnow().isoformat(),
                "format": "binary",
                "size": len(data)
            }
        }
        
    async def _buffer_data(self, data: Dict[str, Any]):
        """Buffer processed data"""
        self.buffer.append(data)
        if len(self.buffer) >= self.buffer_size:
            await self._flush_buffer()
            
    async def _flush_buffer(self):
        """Flush buffered data to storage"""
        if not self.buffer:
            return
            
        try:
            # Implement your storage logic here
            logger.info(f"Flushing {len(self.buffer)} records to storage")
            self.buffer.clear()
        except Exception as e:
            logger.error(f"Error flushing buffer: {str(e)}")
            
    async def _periodic_flush(self):
        """Periodically flush the buffer"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {str(e)}")
                
    async def validate_source(self) -> bool:
        """Validate stream source configuration"""
        required_fields = ["type", "buffer_size", "flush_interval"]
        return all(field in self.config for field in required_fields)

class HandlerFactory:
    """Factory for creating appropriate data source handlers"""
    
    @staticmethod
    async def create_handler(source_type: DataSource, config: Dict[str, Any]) -> SourceHandler:
        """Create a handler instance based on source type"""
        handlers = {
            DataSource.STRUCTURED: StructuredDataHandler,
            DataSource.UNSTRUCTURED: UnstructuredDataHandler,
            DataSource.STREAM: StreamDataHandler
        }
        
        handler_class = handlers.get(source_type)
        if not handler_class:
            raise ValueError(f"Unsupported source type: {source_type}")
            
        handler = handler_class(config)
        if not await handler.validate_source():
            raise ValueError(f"Invalid configuration for source type: {source_type}")
            
        return handler 