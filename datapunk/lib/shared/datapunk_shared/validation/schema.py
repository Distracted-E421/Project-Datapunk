from typing import Any, Dict, List, Optional, Union
from enum import Enum
import json
import jsonschema
from .validator import ValidationRule, ValidationLevel

class SchemaType(Enum):
    JSON = "json"
    AVRO = "avro"
    PROTOBUF = "protobuf"

class SchemaValidator:
    """Schema-based validation implementation."""
    
    def __init__(self):
        self.schemas: Dict[str, Dict] = {}
        self.validators: Dict[str, jsonschema.validators.Validator] = {}
    
    def register_schema(self,
                       name: str,
                       schema: Dict,
                       schema_type: SchemaType = SchemaType.JSON):
        """Register a new schema."""
        self.schemas[name] = schema
        
        if schema_type == SchemaType.JSON:
            self.validators[name] = jsonschema.validators.validator_for(schema)(schema)
    
    def create_validation_rule(self,
                             schema_name: str,
                             level: ValidationLevel = ValidationLevel.STRICT) -> ValidationRule:
        """Create a validation rule from a schema."""
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