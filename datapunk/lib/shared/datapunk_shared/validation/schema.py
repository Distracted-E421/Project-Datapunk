"""
Schema Validation System for Datapunk's Data Pipeline

Provides a flexible schema validation framework supporting multiple schema types
(JSON, AVRO, Protobuf) for data validation across the service mesh. Integrates
with the validation rule system for configurable validation policies.

Key features:
- Multi-schema format support
- Dynamic schema registration
- Validation rule generation
- Integration with service mesh validation

NOTE: This component is critical for data integrity across the system.
Changes should consider impact on data flow and validation policies.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
import json
import jsonschema
from .validator import ValidationRule, ValidationLevel

class SchemaType(Enum):
    """
    Supported schema formats for data validation.
    
    NOTE: Currently only JSON Schema is fully implemented.
    AVRO and Protobuf support are planned for future releases.
    """
    JSON = "json"
    AVRO = "avro"  # TODO: Implement AVRO schema support
    PROTOBUF = "protobuf"  # TODO: Implement Protobuf schema support

class SchemaValidator:
    """
    Schema-based validation implementation for data pipeline integrity.
    
    Manages schema registration and validation rule creation for the
    data processing pipeline. Supports multiple schema formats and
    validation levels for flexible data validation policies.
    
    FIXME: Add schema version management and migration support
    """
    
    def __init__(self):
        # Separate storage for schemas and compiled validators
        # for better performance in high-throughput scenarios
        self.schemas: Dict[str, Dict] = {}
        self.validators: Dict[str, jsonschema.validators.Validator] = {}
    
    def register_schema(self,
                       name: str,
                       schema: Dict,
                       schema_type: SchemaType = SchemaType.JSON):
        """
        Register a new schema for validation.
        
        Compiles schema into optimized validator for performance.
        Currently supports JSON Schema with planned support for
        AVRO and Protobuf.
        
        Args:
            name: Unique identifier for the schema
            schema: Schema definition
            schema_type: Type of schema (JSON/AVRO/Protobuf)
            
        NOTE: Schema compilation is performed at registration time
        to optimize validation performance during data processing.
        """
        self.schemas[name] = schema
        
        if schema_type == SchemaType.JSON:
            # Pre-compile validator for performance
            self.validators[name] = jsonschema.validators.validator_for(schema)(schema)
    
    def create_validation_rule(self,
                             schema_name: str,
                             level: ValidationLevel = ValidationLevel.STRICT) -> ValidationRule:
        """
        Create a validation rule from a registered schema.
        
        Generates an async validation rule that can be integrated into
        the validation pipeline. Uses pre-compiled validators for
        optimal performance.
        
        Args:
            schema_name: Name of registered schema
            level: Validation strictness level
            
        Returns:
            ValidationRule configured for schema validation
            
        TODO: Add support for partial validation at LENIENT level
        TODO: Implement schema-specific error messages
        """
        async def validator(data: Any, context: Dict) -> bool:
            try:
                self.validators[schema_name].validate(data)
                return True
            except jsonschema.exceptions.ValidationError:
                return False
        
        return ValidationRule(
            name=f"schema_{schema_name}",
            description=f"Validates against {schema_name} schema",
            validator=validator,
            error_message=f"Data does not match {schema_name} schema",
            level=level
        ) 