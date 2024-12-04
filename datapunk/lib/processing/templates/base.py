from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from ..etl import ETLPipeline, ETLConfig
from ...validation import DataValidator
from ...monitoring import MetricsClient

"""
Base Pipeline Template for Datapunk's ETL System

Provides a foundational template for building ETL pipelines with standardized
interfaces and common functionality. Designed to ensure consistency and 
reliability across different data processing workflows.

Key Features:
- Standardized ETL interface
- Configurable pipeline behavior
- Integration with monitoring
- Validation support
- Error handling framework

Design Philosophy:
- Separation of concerns (extract, transform, load)
- Flexibility in implementation
- Consistent error handling
- Observable operations

NOTE: All pipeline implementations should inherit from this base
TODO: Add support for pipeline composition and chaining
"""

class BasePipelineTemplate(ABC):
    """
    Abstract base class for ETL pipeline templates.
    
    Key Capabilities:
    - Configurable pipeline behavior
    - Standardized ETL operations
    - Monitoring integration
    - Validation support
    
    FIXME: Consider adding pipeline state management
    """
    
    def __init__(self,
                 etl: ETLPipeline,
                 config: Dict[str, Any]):
        """
        Initializes pipeline template with configuration.
        
        Design Decisions:
        - Accepts external ETL pipeline for flexibility
        - Uses configuration dictionary for customization
        - Integrates with monitoring system
        
        WARNING: Config validation should be implemented by subclasses
        """
        self.etl = etl
        self.config = config
        
    @abstractmethod
    async def extract(self, source: Any) -> List[Dict]:
        """
        Template method for data extraction phase.
        
        Implementation Requirements:
        - Handle source validation
        - Implement error handling
        - Return standardized data format
        - Support monitoring integration
        
        NOTE: Source type varies by implementation
        """
        pass
        
    @abstractmethod
    async def transform(self, data: List[Dict]) -> List[Dict]:
        """
        Template method for data transformation phase.
        
        Implementation Requirements:
        - Maintain data consistency
        - Handle validation
        - Support monitoring
        - Implement error handling
        
        TODO: Add support for transformation pipelines
        """
        pass
        
    @abstractmethod
    async def load(self, data: List[Dict]) -> bool:
        """
        Template method for data loading phase.
        
        Implementation Requirements:
        - Handle target validation
        - Implement error handling
        - Support transaction management
        - Enable monitoring integration
        
        WARNING: Ensure proper error handling for partial loads
        """
        pass
        
    async def execute(self, source: Any) -> bool:
        """
        Executes the complete ETL pipeline.
        
        Pipeline Flow:
        - Extracts data from source
        - Applies transformations
        - Loads to target
        - Handles errors and monitoring
        
        NOTE: Returns success/failure status
        """
        return await self.etl.execute(
            source=source,
            extractor=self.extract,
            transformers=[self.transform],
            loader=self.load
        ) 