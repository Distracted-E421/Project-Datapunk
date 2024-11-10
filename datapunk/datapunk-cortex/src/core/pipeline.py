from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from haystack import Pipeline as HaystackPipeline
from haystack.nodes import PreProcessor, BaseComponent
import asyncio
from .cache import CacheManager
from ..models.selection import ModelSelector

class PipelineType(Enum):
    STANDARD = "standard"
    REALTIME = "realtime"

@dataclass
class PipelineStage:
    name: str
    component: BaseComponent
    config: Dict[str, Any]
    enabled: bool = True

class PipelineManager:
    """Manages processing pipelines for both standard and real-time processing"""
    
    def __init__(self, config: Dict[str, Any], cache_manager: CacheManager, model_selector: ModelSelector):
        self.config = config
        self.cache_manager = cache_manager
        self.model_selector = model_selector
        self.pipelines: Dict[PipelineType, Pipeline] = {}
        
    def get_pipeline(self, pipeline_type: str) -> Pipeline:
        """Get or create pipeline by type"""
        p_type = PipelineType(pipeline_type)
        if p_type not in self.pipelines:
            self.pipelines[p_type] = self._create_pipeline(p_type)
        return self.pipelines[p_type]
        
    def _create_pipeline(self, pipeline_type: PipelineType) -> Pipeline:
        """Create new pipeline based on type"""
        if pipeline_type == PipelineType.STANDARD:
            return self._create_standard_pipeline()
        return self._create_realtime_pipeline()

    def initialize_pipelines(self):
        """Initialize both standard and real-time pipelines"""
        # Initialize standard pipeline with configuration from lines 61-75 in datapunk-cortex.md
        self.pipelines[PipelineType.STANDARD] = self._create_standard_pipeline()
        # Initialize real-time pipeline with configuration from lines 80-92 in datapunk-cortex.md
        self.pipelines[PipelineType.REALTIME] = self._create_realtime_pipeline()

    def _create_standard_pipeline(self) -> HaystackPipeline:
        """Create the standard processing pipeline"""
        pipeline = HaystackPipeline()
        
        # Add preprocessing stage
        pipeline.add_node(component=self._create_preprocessor(), 
                         name="preprocessor",
                         inputs=["Query"])
        
        # Add inference stage
        pipeline.add_node(component=self._create_inference_node(),
                         name="inference",
                         inputs=["preprocessor"])
        
        # Add postprocessing stage
        pipeline.add_node(component=self._create_postprocessor(),
                         name="postprocessor",
                         inputs=["inference"])
        
        return pipeline

    def _create_realtime_pipeline(self) -> HaystackPipeline:
        """Create the real-time processing pipeline"""
        pipeline = HaystackPipeline()
        
        # Add stream processing stage
        pipeline.add_node(component=self._create_stream_processor(),
                         name="stream_processor",
                         inputs=["Query"])
        
        # Add feature extraction stage
        pipeline.add_node(component=self._create_feature_extractor(),
                         name="feature_extractor",
                         inputs=["stream_processor"])
        
        # Add inference stage
        pipeline.add_node(component=self._create_realtime_inference(),
                         name="realtime_inference",
                         inputs=["feature_extractor"])
        
        return pipeline

    def _create_nlp_pipeline(self) -> Pipeline:
        """Create NLP-specific pipeline"""
        pipeline = Pipeline()
        
        # Add preprocessing stage
        pipeline.add_node(
            component=PreProcessor(
                clean_empty_lines=True,
                clean_whitespace=True,
                clean_header_footer=True
            ),
            name="preprocessor",
            inputs=["Query"]
        )
        
        # Add NLP processing stage
        pipeline.add_node(
            component=self.nlp_pipeline,
            name="nlp_processor",
            inputs=["preprocessor"]
        )
        
        # Add postprocessing stage
        pipeline.add_node(
            component=self._create_postprocessor(),
            name="postprocessor",
            inputs=["nlp_processor"]
        )
        
        return pipeline

    async def process(self, 
                     input_data: Dict[str, Any], 
                     pipeline_type: PipelineType = PipelineType.STANDARD) -> Dict[str, Any]:
        """Process input data through the specified pipeline"""
        
        # Check cache first
        cache_key = f"{pipeline_type.value}:{str(input_data)}"
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        # Select appropriate pipeline
        pipeline = self.pipelines[pipeline_type]
        
        # Process the data
        try:
            result = await self._run_pipeline(pipeline, input_data)
            
            # Cache the result
            await self.cache_manager.set(cache_key, result)
            
            return result
        except Exception as e:
            # Handle pipeline execution errors
            return {
                "error": str(e),
                "status": "failed",
                "pipeline_type": pipeline_type.value
            }

    async def _run_pipeline(self, 
                           pipeline: HaystackPipeline, 
                           input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the pipeline asynchronously"""
        # Convert to Haystack format
        query = {"Query": input_data}
        
        # Run pipeline in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, pipeline.run, query)
        
        return self._format_result(result)

    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format the pipeline result for API response"""
        return {
            "status": "success",
            "data": result,
            "metadata": {
                "processing_time": result.get("processing_time"),
                "model_version": result.get("model_version"),
                "confidence": result.get("confidence")
            }
        }