from typing import Any, Dict, List, Optional, AsyncGenerator
from .base import BasePipelineTemplate
import structlog
import asyncio
from datetime import datetime

logger = structlog.get_logger()

"""
Streaming Data Processing Pipeline for Datapunk

Implements a robust streaming data processing pipeline designed to handle
continuous data flows with configurable batch processing and timeout handling.
Integrates with Datapunk's ETL framework for reliable data processing.

Key Features:
- Configurable batch processing
- Timeout handling
- Stream preprocessing
- Data filtering and aggregation
- Stream enrichment
- Metadata injection

Design Philosophy:
- Balance throughput and latency
- Handle backpressure gracefully
- Maintain data consistency
- Support monitoring and debugging

NOTE: This implementation assumes ordered data streams
TODO: Add support for out-of-order data handling
"""

class StreamingPipeline(BasePipelineTemplate):
    """
    Pipeline template for streaming data processing.
    
    Key Capabilities:
    - Batch collection with timeout
    - Stream preprocessing and filtering
    - Data aggregation and enrichment
    - Metadata management
    
    FIXME: Consider adding support for windowed operations
    """
    
    async def extract(self, source: AsyncGenerator) -> List[Dict]:
        """
        Extracts data from streaming source with batch processing.
        
        Implementation Notes:
        - Collects items into batches for efficiency
        - Implements timeout to prevent stalled processing
        - Handles stream interruptions gracefully
        
        WARNING: Ensure proper timeout configuration for your use case
        """
        try:
            batch = []
            batch_size = self.config.get("batch_size", 1000)
            timeout = self.config.get("batch_timeout", 60)  # seconds
            
            async def collect_batch():
                """
                Collects items from stream into batch.
                
                Design Considerations:
                - Stops at batch_size to manage memory
                - Handles stream errors gracefully
                - Provides error context for debugging
                """
                try:
                    async for item in source:
                        batch.append(item)
                        if len(batch) >= batch_size:
                            break
                except Exception as e:
                    logger.error("stream_collection_failed",
                                error=str(e))
                    raise
            
            # Implement timeout for batch collection
            try:
                await asyncio.wait_for(collect_batch(), timeout)
            except asyncio.TimeoutError:
                if not batch:
                    raise TimeoutError("No data received within timeout")
                logger.warning("batch_timeout_reached",
                             collected_items=len(batch))
            
            return batch
            
        except Exception as e:
            logger.error("streaming_extraction_failed",
                        error=str(e))
            raise
    
    async def transform(self, data: List[Dict]) -> List[Dict]:
        """
        Transforms streaming data through multiple stages.
        
        Processing Pipeline:
        - Preprocesses raw stream data
        - Filters unwanted data
        - Aggregates related items
        - Enriches with additional context
        
        TODO: Add support for custom transformation chains
        """
        try:
            transformers = [
                self._preprocess_stream,
                self._filter_stream,
                self._aggregate_stream,
                self._enrich_stream
            ]
            
            return await self.etl.transform(data, transformers)
            
        except Exception as e:
            logger.error("streaming_transformation_failed",
                        error=str(e))
            raise
    
    async def load(self, data: List[Dict]) -> bool:
        """
        Loads processed streaming data with metadata.
        
        Implementation Notes:
        - Adds processing metadata
        - Includes stream identification
        - Handles batch loading
        
        WARNING: Ensure stream sink is properly configured
        """
        try:
            # Add stream metadata for traceability
            for item in data:
                item["processed_at"] = datetime.utcnow().isoformat()
                item["stream_id"] = self.config.get("stream_id")
            
            return await self.etl.load(data, self._stream_load)
            
        except Exception as e:
            logger.error("streaming_load_failed",
                        error=str(e))
            raise
    
    # Helper methods
    async def _preprocess_stream(self, data: Dict) -> Dict:
        """
        Preprocesses streaming data for consistency.
        
        Design Considerations:
        - Uses configurable preprocessors
        - Maintains data structure
        - Supports async preprocessing
        
        NOTE: Order of preprocessors matters
        """
        preprocessors = self.config.get("preprocessors", [])
        for preprocessor in preprocessors:
            data = await preprocessor(data)
        return data
    
    async def _filter_stream(self, data: Dict) -> Dict:
        """
        Filters streaming data based on criteria.
        
        Implementation Notes:
        - Uses multiple filter functions
        - Short-circuits on first failure
        - Returns None for filtered items
        
        TODO: Add support for filter composition
        """
        filters = self.config.get("filters", [])
        for filter_func in filters:
            if not await filter_func(data):
                return None
        return data
    
    async def _aggregate_stream(self, data: Dict) -> Dict:
        """
        Aggregates streaming data items.
        
        Design Considerations:
        - Supports multiple aggregation steps
        - Maintains data consistency
        - Handles async aggregation
        
        FIXME: Consider adding windowed aggregation
        """
        aggregators = self.config.get("aggregators", [])
        for aggregator in aggregators:
            data = await aggregator(data)
        return data
    
    async def _enrich_stream(self, data: Dict) -> Dict:
        """
        Enriches streaming data with additional context.
        
        Implementation Notes:
        - Uses configurable enrichers
        - Supports async enrichment
        - Maintains original data
        
        WARNING: Enrichment may impact processing latency
        """
        enrichers = self.config.get("enrichers", [])
        for enricher in enrichers:
            data = await enricher(data)
        return data
    
    async def _stream_load(self, batch: List[Dict]) -> bool:
        """
        Loads streaming data batch to configured sink.
        
        Design Considerations:
        - Validates sink configuration
        - Handles batch loading
        - Returns success status
        
        NOTE: Implement retry logic in sink if needed
        """
        stream_sink = self.config.get("stream_sink")
        if not stream_sink:
            raise ValueError("No stream sink configured")
        
        return await stream_sink.write(batch) 