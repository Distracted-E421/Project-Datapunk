from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from ..etl import ETLPipeline, ETLConfig
from ...validation import DataValidator
from ...monitoring import MetricsClient

class BasePipelineTemplate(ABC):
    """Base class for ETL pipeline templates."""
    
    def __init__(self,
                 etl: ETLPipeline,
                 config: Dict[str, Any]):
        self.etl = etl
        self.config = config
        
    @abstractmethod
    async def extract(self, source: Any) -> List[Dict]:
        """Template extract implementation."""
        pass
        
    @abstractmethod
    async def transform(self, data: List[Dict]) -> List[Dict]:
        """Template transform implementation."""
        pass
        
    @abstractmethod
    async def load(self, data: List[Dict]) -> bool:
        """Template load implementation."""
        pass
        
    async def execute(self, source: Any) -> bool:
        """Execute the pipeline template."""
        return await self.etl.execute(
            source=source,
            extractor=self.extract,
            transformers=[self.transform],
            loader=self.load
        ) 