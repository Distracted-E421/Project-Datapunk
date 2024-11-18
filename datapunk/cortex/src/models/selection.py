from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class ModelType(Enum):
    LIGHTWEIGHT = "lightweight"
    HEAVY = "heavy"

class ModelConfig(BaseModel):
    name: str
    type: ModelType
    version: str
    metrics: Dict[str, float]
    max_batch_size: int
    supports_streaming: bool

class ModelSelector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = self._load_models()
        
    def _load_models(self) -> List[ModelConfig]:
        return [ModelConfig(**model_config) for model_config in self.config["models"]]
        
    def select_model(self, request: Dict[str, Any]) -> ModelConfig:
        """Select appropriate model based on request requirements"""
        if request.get("streaming", False):
            models = [m for m in self.models if m.supports_streaming]
        else:
            models = self.models
            
        # Apply selection criteria
        selected = self._apply_criteria(models, request)
        if not selected:
            # Use fallback model
            fallback = self.config["fallback"]["default_model"]
            selected = next(m for m in models if m.name == fallback)
            
        return selected