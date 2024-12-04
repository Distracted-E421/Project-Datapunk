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

"""
Core ETL Pipeline Implementation for Datapunk

A robust, configurable ETL (Extract, Transform, Load) pipeline system designed
to handle complex data processing workflows with built-in monitoring,
validation, and error handling capabilities.

Key Features:
- Configurable batch processing
- Parallel transformation support
- Comprehensive error handling
- Integrated monitoring and tracing
- Data validation at key points
- Configurable retry policies

Design Philosophy:
- Reliability over speed
- Comprehensive observability
- Graceful error handling
- Flexible configuration

NOTE: All pipeline operations are traced for debugging
TODO: Add support for distributed processing
"""

class ETLError(DatapunkError):
    """Base exception for ETL operations."""
    pass

class ExtractionError(ETLError):
    """
    Raised when data extraction fails.
    Used to distinguish extraction failures from other ETL errors.
    """
    pass

class TransformationError(ETLError):
    """
    Raised when data transformation fails.
    Includes support for partial transformation failures.
    """
    pass

class LoadError(ETLError):
    """
    Raised when data loading fails.
    Helps identify target system issues.
    """
    pass

@dataclass
class ETLConfig:
    """
    Configuration for ETL pipeline behavior.
    
    Design Considerations:
    - Batch size affects memory usage and performance
    - Retry configuration for resilience
    - Timeout prevention for hung operations
    - Parallel processing capabilities
    - Validation controls for data quality
    
    WARNING: Adjust batch_size based on available memory
    """
    batch_size: int = 1000
    max_retries: int = 3
    timeout: int = 300  # seconds
    parallel_transforms: int = 4
    validate_input: bool = True
    validate_output: bool = True
    error_threshold: float = 0.1  # 10% error rate threshold

class ETLPipeline:
    """
    Main ETL pipeline implementation with monitoring and validation.
    
    Key Capabilities:
    - Batch processing with configurable size
    - Parallel transformation support
    - Input/output validation
    - Error rate monitoring
    - Performance metrics collection
    
    FIXME: Consider adding transaction support for atomic operations
    """
    
    def __init__(self,
                 config: ETLConfig,
                 validator: DataValidator,
                 metrics: MetricsClient):
        """
        Initializes ETL pipeline with configuration and dependencies.
        
        Implementation Notes:
        - Uses external validator for flexibility
        - Integrates metrics for monitoring
        - Configures component-specific logging
        
        NOTE: Ensure validator rules match data requirements
        """
        self.config = config
        self.validator = validator
        self.metrics = metrics
        self.logger = logger.bind(component="etl")
        
    @trace_method("extract_data")
    async def extract(self,
                     source: Any,
                     extractor: Callable) -> List[Dict]:
        """
        Extracts data from source with validation and monitoring.
        
        Design Considerations:
        - Validates input data if configured
        - Records extraction metrics
        - Handles extraction failures gracefully
        
        WARNING: Ensure source is accessible before extraction
        """
        try:
            self.metrics.increment("etl_extraction_started")
            start_time = datetime.utcnow()
            
            # Extract data with monitoring
            data = await extractor(source)
            
            # Validate extracted data if configured
            if self.config.validate_input:
                validation_result = await self.validator.validate(data)
                if not validation_result.passed:
                    self.logger.error("extraction_validation_failed",
                                    errors=validation_result.errors)
                    raise ExtractionError("Extracted data failed validation")
            
            # Record metrics
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
        """
        Transforms data through multiple transformation steps.
        
        Implementation Notes:
        - Processes data in configurable batches
        - Supports parallel transformations
        - Monitors error rates
        - Validates transformed data
        
        TODO: Add support for transformation rollback
        """
        try:
            self.metrics.increment("etl_transformation_started")
            start_time = datetime.utcnow()
            
            transformed_data = data
            error_count = 0
            
            # Process in batches for memory efficiency
            for i in range(0, len(data), self.config.batch_size):
                batch = data[i:i + self.config.batch_size]
                
                # Apply transformers with parallel processing
                for transformer in transformers:
                    tasks = []
                    for item in batch:
                        task = asyncio.create_task(transformer(item))
                        tasks.append(task)
                    
                    # Wait for transformations with error handling
                    batch_results = await asyncio.gather(
                        *tasks,
                        return_exceptions=True
                    )
                    
                    # Handle transformation results
                    for j, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            error_count += 1
                            self.logger.error("transformation_item_failed",
                                            error=str(result),
                                            item_index=i+j)
                            continue
                        transformed_data[i+j] = result
            
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
            
            # Record metrics
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
        """
        Loads transformed data to destination.
        
        Design Considerations:
        - Processes data in batches
        - Handles partial load failures
        - Records load metrics
        - Supports custom loaders
        
        WARNING: Ensure target system can handle batch loads
        """
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
            
            # Record metrics
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