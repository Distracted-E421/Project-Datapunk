from typing import Dict, Any, Optional
from haystack import Pipeline
from langchain import LLMChain
from .cache import CacheManager
from .models.selection import ModelSelector
from .pipeline import PipelineManager
from .haystack_engine import HaystackEngine
from .langchain_engine import LangChainEngine

class NeuroCortex:
    """Central AI orchestrator for the Datapunk system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config["neurocortex"]  # Access neurocortex section
        
        # Initialize core components
        self.cache_manager = CacheManager(self.config["cache"])
        self.model_selector = ModelSelector(self.config["model_selection"])
        
        # Initialize AI engines
        self.haystack_engine = HaystackEngine(
            config=self.config["integrations"]["haystack"],
            cache_manager=self.cache_manager
        )
        self.langchain_engine = LangChainEngine(
            config=self.config["integrations"]["langchain"],
            cache_manager=self.cache_manager
        )
        
        # Initialize pipeline manager
        self.pipeline_manager = PipelineManager(
            config=self.config,
            cache_manager=self.cache_manager,
            model_selector=self.model_selector
        )

    async def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming request through the appropriate pipeline"""
        try:
            # Check cache
            cache_key = f"request:{hash(str(input_data))}"
            cache_result = await self.cache_manager.get(cache_key)
            if cache_result:
                return cache_result

            # Select appropriate model
            selected_model = self.model_selector.select_model(input_data)
            
            # Get appropriate pipeline
            pipeline_type = "realtime" if input_data.get("streaming") else "standard"
            pipeline = self.pipeline_manager.get_pipeline(pipeline_type)
            
            # Process request
            result = await pipeline.run(
                input_data=input_data,
                model=selected_model
            )
            
            # Cache result
            await self.cache_manager.set(cache_key, result)
            
            return result
            
        except Exception as e:
            # Log error and raise appropriate exception
            raise RuntimeError(f"Error processing request: {str(e)}")

    async def cleanup(self):
        """Cleanup resources on shutdown"""
        await self.cache_manager.cleanup()
        await self.haystack_engine.cleanup()
        await self.langchain_engine.cleanup()