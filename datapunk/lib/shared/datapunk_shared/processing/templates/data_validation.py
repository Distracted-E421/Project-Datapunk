from typing import Any, Dict, List, Optional
from .base import BasePipelineTemplate
from ...validation import ValidationRule, ValidationLevel
import structlog

logger = structlog.get_logger()

class DataValidationPipeline(BasePipelineTemplate):
    """Pipeline template for data validation and cleaning."""
    
    async def extract(self, source: Any) -> List[Dict]:
        """Extract data with validation."""
        try:
            # Apply source-specific validation rules
            validation_rules = [
                ValidationRule(
                    name="source_format",
                    description="Validates source data format",
                    validator=self._validate_source_format,
                    error_message="Invalid source format",
                    level=ValidationLevel.STRICT
                ),
                ValidationRule(
                    name="required_fields",
                    description="Validates required fields presence",
                    validator=self._validate_required_fields,
                    error_message="Missing required fields",
                    level=ValidationLevel.STRICT
                )
            ]
            
            for rule in validation_rules:
                if not await rule.validator(source, {}):
                    raise ValueError(f"Source validation failed: {rule.error_message}")
            
            return await self.etl.extract(source, self._extract_data)
            
        except Exception as e:
            logger.error("data_validation_extraction_failed",
                        error=str(e),
                        source=str(source))
            raise
    
    async def transform(self, data: List[Dict]) -> List[Dict]:
        """Transform with data cleaning and validation."""
        try:
            transformers = [
                self._clean_data,
                self._validate_data_types,
                self._normalize_fields,
                self._enrich_data
            ]
            
            return await self.etl.transform(data, transformers)
            
        except Exception as e:
            logger.error("data_validation_transformation_failed",
                        error=str(e))
            raise
    
    async def load(self, data: List[Dict]) -> bool:
        """Load validated data."""
        try:
            # Final validation before loading
            validation_result = await self.etl.validator.validate(
                data,
                rule_names=["final_validation"]
            )
            
            if not validation_result.passed:
                raise ValueError("Final validation failed before loading")
            
            return await self.etl.load(data, self._load_data)
            
        except Exception as e:
            logger.error("data_validation_load_failed",
                        error=str(e))
            raise
    
    # Helper methods
    async def _validate_source_format(self, source: Any, context: Dict) -> bool:
        """Validate source data format."""
        try:
            return isinstance(source, (dict, list))
        except Exception:
            return False
    
    async def _validate_required_fields(self, source: Any, context: Dict) -> bool:
        """Validate required fields presence."""
        required_fields = self.config.get("required_fields", [])
        if isinstance(source, dict):
            return all(field in source for field in required_fields)
        elif isinstance(source, list):
            return all(
                all(field in item for field in required_fields)
                for item in source
            )
        return False
    
    async def _extract_data(self, source: Any) -> List[Dict]:
        """Extract data from source."""
        if isinstance(source, dict):
            return [source]
        return source
    
    async def _clean_data(self, data: Dict) -> Dict:
        """Clean data by removing invalid fields."""
        return {
            k: v for k, v in data.items()
            if v is not None and v != ""
        }
    
    async def _validate_data_types(self, data: Dict) -> Dict:
        """Validate and convert data types."""
        type_mapping = self.config.get("type_mapping", {})
        for field, expected_type in type_mapping.items():
            if field in data:
                try:
                    data[field] = expected_type(data[field])
                except (ValueError, TypeError):
                    data[field] = None
        return data
    
    async def _normalize_fields(self, data: Dict) -> Dict:
        """Normalize field values."""
        normalizers = self.config.get("normalizers", {})
        for field, normalizer in normalizers.items():
            if field in data:
                data[field] = normalizer(data[field])
        return data
    
    async def _enrich_data(self, data: Dict) -> Dict:
        """Enrich data with additional information."""
        enrichers = self.config.get("enrichers", {})
        for field, enricher in enrichers.items():
            data[field] = await enricher(data)
        return data
    
    async def _load_data(self, data: List[Dict]) -> bool:
        """Load data to destination."""
        destination = self.config.get("destination")
        if not destination:
            raise ValueError("No destination configured")
        
        # Implement destination-specific loading logic
        return True 