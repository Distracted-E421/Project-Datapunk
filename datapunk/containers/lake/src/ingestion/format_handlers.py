from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import json
import yaml
import xml.etree.ElementTree as ET
import csv
import io
import avro.schema
from avro.io import DatumReader, BinaryDecoder
import parquet
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from .monitoring import HandlerMetrics
from .handlers import RetryHandler, ExponentialBackoff

logger = logging.getLogger(__name__)

class FormatHandler(ABC):
    """Base class for format-specific handlers"""
    
    def __init__(self, metrics: HandlerMetrics):
        self.metrics = metrics
        self.retry_handler = RetryHandler(
            ExponentialBackoff(max_attempts=3)
        )
        
    @abstractmethod
    async def parse(self, data: Any) -> Dict[str, Any]:
        """Parse data in specific format"""
        pass
        
    @abstractmethod
    async def validate(self, data: Any) -> bool:
        """Validate data format"""
        pass
        
    async def process(self, data: Any) -> Dict[str, Any]:
        """Process data with metrics collection"""
        start_time = datetime.utcnow()
        try:
            if not await self.validate(data):
                raise ValueError("Invalid data format")
                
            result = await self.parse(data)
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self.metrics.record_processing_time(
                self.__class__.__name__,
                duration
            )
            await self.metrics.record_success(self.__class__.__name__)
            
            if isinstance(data, (str, bytes)):
                await self.metrics.record_data_size(
                    self.__class__.__name__,
                    len(data)
                )
                
            return result
        except Exception as e:
            await self.metrics.record_error(
                self.__class__.__name__,
                type(e).__name__
            )
            raise

class JSONHandler(FormatHandler):
    """Handler for JSON data"""
    
    async def parse(self, data: Union[str, bytes, Dict]) -> Dict[str, Any]:
        """Parse JSON data"""
        if isinstance(data, (str, bytes)):
            return json.loads(data)
        return data
        
    async def validate(self, data: Any) -> bool:
        """Validate JSON format"""
        try:
            if isinstance(data, (str, bytes)):
                json.loads(data)
            elif not isinstance(data, dict):
                return False
            return True
        except json.JSONDecodeError:
            return False

class YAMLHandler(FormatHandler):
    """Handler for YAML data"""
    
    async def parse(self, data: str) -> Dict[str, Any]:
        """Parse YAML data"""
        return yaml.safe_load(data)
        
    async def validate(self, data: Any) -> bool:
        """Validate YAML format"""
        try:
            if not isinstance(data, str):
                return False
            yaml.safe_load(data)
            return True
        except yaml.YAMLError:
            return False

class XMLHandler(FormatHandler):
    """Handler for XML data"""
    
    def _xml_to_dict(self, element: ET.Element) -> Union[Dict, str]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Handle attributes
        if element.attrib:
            result.update(element.attrib)
            
        # Handle children
        children = list(element)
        if not children:
            return element.text or ""
            
        for child in children:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
                
        return result
    
    async def parse(self, data: str) -> Dict[str, Any]:
        """Parse XML data"""
        root = ET.fromstring(data)
        return {root.tag: self._xml_to_dict(root)}
        
    async def validate(self, data: Any) -> bool:
        """Validate XML format"""
        try:
            if not isinstance(data, str):
                return False
            ET.fromstring(data)
            return True
        except ET.ParseError:
            return False

class CSVHandler(FormatHandler):
    """Handler for CSV data"""
    
    def __init__(self, metrics: HandlerMetrics, **kwargs):
        super().__init__(metrics)
        self.csv_options = kwargs
        
    async def parse(self, data: Union[str, bytes]) -> List[Dict[str, Any]]:
        """Parse CSV data"""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
            
        # Use pandas for efficient CSV processing
        df = pd.read_csv(
            io.StringIO(data),
            **self.csv_options
        )
        return df.to_dict(orient='records')
        
    async def validate(self, data: Any) -> bool:
        """Validate CSV format"""
        try:
            if not isinstance(data, (str, bytes)):
                return False
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            csv.Sniffer().sniff(data)
            return True
        except (csv.Error, UnicodeDecodeError):
            return False

class AvroHandler(FormatHandler):
    """Handler for Avro data"""
    
    def __init__(self, metrics: HandlerMetrics, schema: Union[str, Dict]):
        super().__init__(metrics)
        self.schema = (
            avro.schema.parse(schema)
            if isinstance(schema, str)
            else avro.schema.parse(json.dumps(schema))
        )
        self.reader = DatumReader(self.schema)
        
    async def parse(self, data: bytes) -> Dict[str, Any]:
        """Parse Avro data"""
        decoder = BinaryDecoder(io.BytesIO(data))
        return self.reader.read(decoder)
        
    async def validate(self, data: Any) -> bool:
        """Validate Avro format"""
        try:
            if not isinstance(data, bytes):
                return False
            decoder = BinaryDecoder(io.BytesIO(data))
            self.reader.read(decoder)
            return True
        except Exception:
            return False

class ParquetHandler(FormatHandler):
    """Handler for Parquet data"""
    
    async def parse(self, data: Union[bytes, Path]) -> pd.DataFrame:
        """Parse Parquet data"""
        if isinstance(data, bytes):
            buffer = io.BytesIO(data)
            return pd.read_parquet(buffer)
        return pd.read_parquet(data)
        
    async def validate(self, data: Any) -> bool:
        """Validate Parquet format"""
        try:
            if not isinstance(data, (bytes, Path)):
                return False
            if isinstance(data, bytes):
                buffer = io.BytesIO(data)
                pd.read_parquet(buffer)
            else:
                pd.read_parquet(data)
            return True
        except Exception:
            return False

class FormatHandlerFactory:
    """Factory for creating format-specific handlers"""
    
    def __init__(self, metrics: HandlerMetrics):
        self.metrics = metrics
        self.handlers = {
            'json': JSONHandler,
            'yaml': YAMLHandler,
            'xml': XMLHandler,
            'csv': CSVHandler,
            'avro': AvroHandler,
            'parquet': ParquetHandler
        }
        
    async def create_handler(
        self,
        format_type: str,
        **kwargs
    ) -> FormatHandler:
        """Create a handler for the specified format"""
        handler_class = self.handlers.get(format_type.lower())
        if not handler_class:
            raise ValueError(f"Unsupported format: {format_type}")
            
        return handler_class(self.metrics, **kwargs) 