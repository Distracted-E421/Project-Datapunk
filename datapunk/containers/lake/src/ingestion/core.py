from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Enumeration of supported data sources"""
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"
    STREAM = "stream"

class ValidationLevel(Enum):
    """Validation severity levels"""
    STRICT = "strict"  # Fail on any validation error
    LENIENT = "lenient"  # Allow minor violations, log warnings
    AUDIT = "audit"  # Log all issues but don't block

class ValidationResult(BaseModel):
    """Validation result with detailed error information"""
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()

class SchemaRegistry:
    """Central registry for data schemas and validation rules"""
    
    def __init__(self):
        self._schemas: Dict[str, Type[BaseModel]] = {}
        self._rules: Dict[str, List[Dict[str, Any]]] = {}
        
    async def register_schema(self, name: str, schema: Type[BaseModel]) -> None:
        """Register a new schema"""
        if name in self._schemas:
            logger.warning(f"Overwriting existing schema: {name}")
        self._schemas[name] = schema
        logger.info(f"Registered schema: {name}")
        
    async def get_schema(self, name: str) -> Optional[Type[BaseModel]]:
        """Retrieve a registered schema"""
        return self._schemas.get(name)
        
    async def register_rules(self, schema_name: str, rules: List[Dict[str, Any]]) -> None:
        """Register validation rules for a schema"""
        if schema_name not in self._schemas:
            raise ValueError(f"Schema not found: {schema_name}")
        self._rules[schema_name] = rules
        logger.info(f"Registered rules for schema: {schema_name}")
        
    async def get_rules(self, schema_name: str) -> List[Dict[str, Any]]:
        """Retrieve validation rules for a schema"""
        return self._rules.get(schema_name, [])

class ValidationEngine:
    """Core validation engine for data ingestion"""
    
    def __init__(self, registry: SchemaRegistry, level: ValidationLevel = ValidationLevel.STRICT):
        self.registry = registry
        self.level = level
        
    async def validate(self, data: Any, schema_name: str) -> ValidationResult:
        """Validate data against registered schema and rules"""
        errors = []
        warnings = []
        metadata = {"schema": schema_name, "validation_level": self.level.value}
        
        # Schema validation
        schema = await self.registry.get_schema(schema_name)
        if not schema:
            errors.append({"error": "Schema not found", "schema": schema_name})
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
        try:
            validated_data = schema.parse_obj(data)
            metadata["validated_fields"] = list(validated_data.dict().keys())
        except ValidationError as e:
            for error in e.errors():
                if self.level == ValidationLevel.STRICT:
                    errors.append({"error": error["msg"], "field": error["loc"]})
                else:
                    warnings.append({"warning": error["msg"], "field": error["loc"]})
        
        # Custom rules validation
        rules = await self.registry.get_rules(schema_name)
        for rule in rules:
            try:
                await self._apply_rule(data, rule, errors, warnings)
            except Exception as e:
                logger.error(f"Rule application failed: {str(e)}")
                errors.append({"error": "Rule application failed", "rule": rule})
        
        is_valid = len(errors) == 0 if self.level == ValidationLevel.STRICT else True
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    async def _apply_rule(
        self, 
        data: Any, 
        rule: Dict[str, Any], 
        errors: List[Dict[str, Any]], 
        warnings: List[Dict[str, Any]]
    ) -> None:
        """Apply a single validation rule to the data"""
        rule_type = rule.get("type")
        field = rule.get("field")
        
        if not rule_type or not field:
            errors.append({"error": "Invalid rule format", "rule": rule})
            return
            
        field_value = data.get(field) if isinstance(data, dict) else None
        
        if rule_type == "required" and field_value is None:
            errors.append({"error": "Required field missing", "field": field})
        elif rule_type == "range" and field_value is not None:
            min_val = rule.get("min")
            max_val = rule.get("max")
            if min_val is not None and field_value < min_val:
                errors.append({"error": "Value below minimum", "field": field})
            if max_val is not None and field_value > max_val:
                errors.append({"error": "Value above maximum", "field": field})
        elif rule_type == "pattern" and field_value is not None:
            import re
            pattern = rule.get("pattern")
            if pattern and not re.match(pattern, str(field_value)):
                errors.append({"error": "Pattern mismatch", "field": field})

class DataIngestionManager:
    """Manages the data ingestion process"""
    
    def __init__(self, validation_engine: ValidationEngine):
        self.validation_engine = validation_engine
        self._handlers: Dict[DataSource, Any] = {}
        
    async def register_handler(self, source_type: DataSource, handler: Any) -> None:
        """Register a handler for a specific data source type"""
        self._handlers[source_type] = handler
        logger.info(f"Registered handler for source type: {source_type.value}")
        
    async def ingest(self, data: Any, source_type: DataSource, schema_name: str) -> ValidationResult:
        """Ingest and validate data from a specific source"""
        handler = self._handlers.get(source_type)
        if not handler:
            raise ValueError(f"No handler registered for source type: {source_type.value}")
            
        # Pre-process data using source-specific handler
        processed_data = await handler.process(data)
        
        # Validate the processed data
        validation_result = await self.validation_engine.validate(processed_data, schema_name)
        
        # Log validation results
        if not validation_result.is_valid:
            logger.error(f"Validation failed for {schema_name}: {validation_result.errors}")
        elif validation_result.warnings:
            logger.warning(f"Validation warnings for {schema_name}: {validation_result.warnings}")
            
        return validation_result 