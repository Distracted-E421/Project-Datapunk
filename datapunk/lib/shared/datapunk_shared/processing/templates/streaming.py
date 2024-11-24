from typing import Any, Dict, List, Optional, AsyncGenerator
from .base import BasePipelineTemplate
import structlog
import asyncio
from datetime import datetime

logger = structlog.get_logger()

class StreamingPipeline(BasePipelineTemplate):
    """Pipeline template for streaming data processing."""
    
    async def extract(self, source: AsyncGenerator) -> List[Dict]:
        """Extract data from streaming source."""
        try:
            batch = []
            batch_size = self.config.get("batch_size", 1000)
            timeout = self.config.get("batch_timeout", 60)  # seconds
            
            async def collect_batch():
                try:
                    async for item in source:
                        batch.append(item)
                        if len(batch) >= batch_size:
                            break
                except Exception as e:
                    logger.error("stream_collection_failed",
                                error=str(e))
                    raise
            
            # Collect batch with timeout
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
        """Transform streaming data."""
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
        """Load streaming data."""
        try:
            # Add stream metadata
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
        """Preprocess streaming data."""
        preprocessors = self.config.get("preprocessors", [])
        for preprocessor in preprocessors:
            data = await preprocessor(data)
        return data
    
    async def _filter_stream(self, data: Dict) -> Dict:
        """Filter streaming data."""
        filters = self.config.get("filters", [])
        for filter_func in filters:
            if not await filter_func(data):
                return None
        return data
    
    async def _aggregate_stream(self, data: Dict) -> Dict:
        """Aggregate streaming data."""
        aggregators = self.config.get("aggregators", [])
        for aggregator in aggregators:
            data = await aggregator(data)
        return data
    
    async def _enrich_stream(self, data: Dict) -> Dict:
        """Enrich streaming data."""
        enrichers = self.config.get("enrichers", [])
        for enricher in enrichers:
            data = await enricher(data)
        return data
    
    async def _stream_load(self, batch: List[Dict]) -> bool:
        """Load streaming data batch."""
        stream_sink = self.config.get("stream_sink")
        if not stream_sink:
            raise ValueError("No stream sink configured")
        
        return await stream_sink.write(batch) 