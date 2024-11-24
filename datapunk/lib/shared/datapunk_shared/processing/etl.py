from typing import Any, Dict, List, Optional, Union, Callable
import asyncio
import structlog
from datetime import datetime
from dataclasses import dataclass
from ..validation import DataValidator, ValidationResult
from ..monitoring import MetricsClient
from ..tracing import trace_method
from ..exceptions import DatapunkError

logger = structlog.get_logger()

class ETLError(DatapunkError):
    """Base exception for ETL operations."""
    pass

class ExtractionError(ETLError):
    """Raised when data extraction fails."""
    pass

class TransformationError(ETLError):
    """Raised when data transformation fails."""
    pass

class LoadError(ETLError):
    """Raised when data loading fails."""
    pass

@dataclass
class ETLConfig:
    """Configuration for ETL pipeline."""
    batch_size: int = 1000
    max_retries: int = 3
    timeout: int = 300  # seconds
    parallel_transforms: int = 4
    validate_input: bool = True
    validate_output: bool = True
    error_threshold: float = 0.1  # 10% error rate threshold

class ETLPipeline:
    """Main ETL pipeline implementation."""
    
    def __init__(self,
                 config: ETLConfig,
                 validator: DataValidator,
                 metrics: MetricsClient):
        self.config = config
        self.validator = validator
        self.metrics = metrics
        self.logger = logger.bind(component="etl")
        
    @trace_method("extract_data")
    async def extract(self,
                     source: Any,
                     extractor: Callable) -> List[Dict]:
        """Extract data from source."""
        try:
            self.metrics.increment("etl_extraction_started")
            start_time = datetime.utcnow()
            
            # Extract data
            data = await extractor(source)
            
            # Validate if configured
            if self.config.validate_input:
                validation_result = await self.validator.validate(data)
                if not validation_result.passed:
                    self.logger.error("extraction_validation_failed",
                                    errors=validation_result.errors)
                    raise ExtractionError("Extracted data failed validation")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.observe("etl_extraction_duration", duration)
            self.metrics.increment("etl_extraction_success")
            
            return data
            
        except Exception as e:
            self.metrics.increment("etl_extraction_failed")
            self.logger.error("extraction_failed", error=str(e))
            raise ExtractionError(f"Data extraction failed: {str(e)}")
    
    @trace_method("transform_data")
    async def transform(self,
                       data: List[Dict],
                       transformers: List[Callable]) -> List[Dict]:
        """Transform data through multiple transformation steps."""
        try:
            self.metrics.increment("etl_transformation_started")
            start_time = datetime.utcnow()
            
            transformed_data = data
            error_count = 0
            
            # Process data in batches
            for i in range(0, len(data), self.config.batch_size):
                batch = data[i:i + self.config.batch_size]
                
                # Apply each transformer to the batch
                for transformer in transformers:
                    try:
                        # Process batch items in parallel
                        tasks = []
                        for item in batch:
                            task = asyncio.create_task(transformer(item))
                            tasks.append(task)
                        
                        # Wait for all transformations with timeout
                        batch_results = await asyncio.gather(
                            *tasks,
                            return_exceptions=True
                        )
                        
                        # Handle any errors in batch
                        for j, result in enumerate(batch_results):
                            if isinstance(result, Exception):
                                error_count += 1
                                self.logger.error("transformation_item_failed",
                                                error=str(result),
                                                item_index=i+j)
                                continue
                            transformed_data[i+j] = result
                            
                    except Exception as e:
                        self.logger.error("transformation_batch_failed",
                                        batch_index=i,
                                        error=str(e))
                        error_count += len(batch)
            
            # Check error threshold
            error_rate = error_count / len(data)
            if error_rate > self.config.error_threshold:
                raise TransformationError(
                    f"Error rate {error_rate:.2%} exceeds threshold "
                    f"{self.config.error_threshold:.2%}"
                )
            
            # Validate transformed data if configured
            if self.config.validate_output:
                validation_result = await self.validator.validate(transformed_data)
                if not validation_result.passed:
                    self.logger.error("transformation_validation_failed",
                                    errors=validation_result.errors)
                    raise TransformationError("Transformed data failed validation")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.observe("etl_transformation_duration", duration)
            self.metrics.increment("etl_transformation_success")
            
            return transformed_data
            
        except Exception as e:
            self.metrics.increment("etl_transformation_failed")
            self.logger.error("transformation_failed", error=str(e))
            raise TransformationError(f"Data transformation failed: {str(e)}")
    
    @trace_method("load_data")
    async def load(self,
                  data: List[Dict],
                  loader: Callable) -> bool:
        """Load transformed data to destination."""
        try:
            self.metrics.increment("etl_load_started")
            start_time = datetime.utcnow()
            
            # Load data in batches
            for i in range(0, len(data), self.config.batch_size):
                batch = data[i:i + self.config.batch_size]
                try:
                    await loader(batch)
                except Exception as e:
                    self.logger.error("load_batch_failed",
                                    batch_index=i,
                                    error=str(e))
                    raise LoadError(f"Failed to load batch {i}: {str(e)}")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.observe("etl_load_duration", duration)
            self.metrics.increment("etl_load_success")
            
            return True
            
        except Exception as e:
            self.metrics.increment("etl_load_failed")
            self.logger.error("load_failed", error=str(e))
            raise LoadError(f"Data loading failed: {str(e)}")
    
    @trace_method("execute_pipeline")
    async def execute(self,
                     source: Any,
                     extractor: Callable,
                     transformers: List[Callable],
                     loader: Callable) -> bool:
        """Execute complete ETL pipeline."""
        try:
            self.metrics.increment("etl_pipeline_started")
            start_time = datetime.utcnow()
            
            # Extract
            data = await self.extract(source, extractor)
            
            # Transform
            transformed_data = await self.transform(data, transformers)
            
            # Load
            success = await self.load(transformed_data, loader)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.observe("etl_pipeline_duration", duration)
            self.metrics.increment("etl_pipeline_success")
            
            return success
            
        except Exception as e:
            self.metrics.increment("etl_pipeline_failed")
            self.logger.error("pipeline_failed", error=str(e))
            raise ETLError(f"ETL pipeline failed: {str(e)}") 