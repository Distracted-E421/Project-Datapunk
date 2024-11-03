from typing import Dict, Any, Optional, List
from haystack import Pipeline
from haystack.nodes import PreProcessor, TextConverter, DocumentStore
from haystack.document_stores import PostgreSQLDocumentStore
from .cache import CacheManager
from .config import Config

class HaystackEngine:
    """Core Haystack integration for document processing and QA"""
    
    def __init__(self, config: Dict[str, Any], cache_manager: CacheManager):
        self.config = config
        self.cache_manager = cache_manager
        self.document_store = self._initialize_document_store()
        self.pipelines: Dict[str, Pipeline] = {}
        
    def _initialize_document_store(self) -> DocumentStore:
        store_config = self.config["document_store"]
        return PostgreSQLDocumentStore(
            host=store_config["host"],
            port=store_config["port"],
            username=store_config["username"],
            password=store_config["password"],
            index=store_config["index"],
            embedding_dim=768  # Default for most transformer models
        )
    
    async def process_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process documents through appropriate Haystack pipeline"""
        pipeline = self._get_pipeline("document_qa")
        return await pipeline.run(documents=documents)
    
    def _get_pipeline(self, pipeline_type: str) -> Pipeline:
        """Get or create pipeline by type"""
        if pipeline_type not in self.pipelines:
            self.pipelines[pipeline_type] = self._create_pipeline(pipeline_type)
        return self.pipelines[pipeline_type]
    
    def _create_pipeline(self, pipeline_type: str) -> Pipeline:
        """Create new pipeline based on type"""
        pipeline = Pipeline()
        
        # Add standard preprocessing
        pipeline.add_node(PreProcessor(), name="preprocessor", inputs=["Query"])
        
        # Add pipeline-specific nodes
        if pipeline_type == "document_qa":
            self._add_qa_nodes(pipeline)
        elif pipeline_type == "indexing":
            self._add_indexing_nodes(pipeline)
            
        return pipeline
