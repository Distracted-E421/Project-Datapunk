from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass
import structlog
from enum import Enum
import re
import json
from datetime import datetime
from ..monitoring import MetricsClient
from ..tracing import trace_method

logger = structlog.get_logger()

class ValidationLevel(Enum):
    STRICT = "strict"      # All rules must pass
    LENIENT = "lenient"   # Non-critical rules can fail
    AUDIT = "audit"       # Log violations but don't fail

@dataclass
class ValidationRule:
    """Definition of a validation rule."""
    name: str
    description: str
    validator: callable
    error_message: str
    level: ValidationLevel = ValidationLevel.STRICT
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None

class ValidationResult:
    """Result of a validation operation."""
    def __init__(self):
        self.passed = True
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.audit_logs: List[Dict] = []
        self.metadata: Dict[str, Any] = {}
        
    def add_error(self, rule: str, message: str, details: Dict = None):
        """Add validation error."""
        self.passed = False
        self.errors.append({
            "rule": rule,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
        
    def add_warning(self, rule: str, message: str, details: Dict = None):
        """Add validation warning."""
        self.warnings.append({
            "rule": rule,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
        
    def add_audit_log(self, rule: str, message: str, details: Dict = None):
        """Add audit log entry."""
        self.audit_logs.append({
            "rule": rule,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })

class DataValidator:
    """Main validator implementation."""
    
    def __init__(self, metrics: MetricsClient):
        self.rules: Dict[str, ValidationRule] = {}
        self.metrics = metrics
        self.logger = logger.bind(component="validator")
    
    def register_rule(self, rule: ValidationRule):
        """Register a validation rule."""
        self.rules[rule.name] = rule
        self.logger.info("validation_rule_registered",
                        rule=rule.name,
                        level=rule.level.value)
    
    @trace_method("validate_data")
    async def validate(self,
                      data: Any,
                      rule_names: List[str] = None,
                      context: Dict = None) -> ValidationResult:
        """Validate data against specified rules."""
        result = ValidationResult()
        context = context or {}
        
        try:
            # Determine rules to apply
            rules_to_apply = (
                [self.rules[name] for name in rule_names]
                if rule_names
                else self.rules.values()
            )
            
            # Sort rules by dependencies
            rules_to_apply = self._sort_rules_by_dependencies(rules_to_apply)
            
            # Apply each rule
            for rule in rules_to_apply:
                try:
                    rule_passed = await rule.validator(data, context)
                    
                    if not rule_passed:
                        if rule.level == ValidationLevel.STRICT:
                            result.add_error(
                                rule.name,
                                rule.error_message,
                                {"data": str(data)}
                            )
                            self.metrics.increment(
                                "validation_errors",
                                {"rule": rule.name}
                            )
                        elif rule.level == ValidationLevel.LENIENT:
                            result.add_warning(
                                rule.name,
                                rule.error_message,
                                {"data": str(data)}
                            )
                            self.metrics.increment(
                                "validation_warnings",
                                {"rule": rule.name}
                            )
                        else:  # AUDIT
                            result.add_audit_log(
                                rule.name,
                                rule.error_message,
                                {"data": str(data)}
                            )
                            self.metrics.increment(
                                "validation_audit_logs",
                                {"rule": rule.name}
                            )
                    else:
                        self.metrics.increment(
                            "validation_successes",
                            {"rule": rule.name}
                        )
                        
                except Exception as e:
                    self.logger.error("rule_execution_failed",
                                    rule=rule.name,
                                    error=str(e))
                    result.add_error(
                        rule.name,
                        f"Rule execution failed: {str(e)}",
                        {"error": str(e)}
                    )
                    self.metrics.increment(
                        "validation_failures",
                        {"rule": rule.name}
                    )
                    
            return result
            
        except Exception as e:
            self.logger.error("validation_failed", error=str(e))
            result.add_error("system", f"Validation failed: {str(e)}")
            self.metrics.increment("validation_system_errors")
            return result
    
    def _sort_rules_by_dependencies(self,
                                  rules: List[ValidationRule]) -> List[ValidationRule]:
        """Sort rules based on their dependencies."""
        sorted_rules = []
        visited = set()
        
        def visit_rule(rule: ValidationRule):
            if rule.name in visited:
                return
            visited.add(rule.name)
            
            if rule.dependencies:
                for dep_name in rule.dependencies:
                    if dep_name in self.rules:
                        visit_rule(self.rules[dep_name])
            
            sorted_rules.append(rule)
        
        for rule in rules:
            visit_rule(rule)
            
        return sorted_rules

# Common validation rules
class CommonRules:
    @staticmethod
    def required_fields(fields: List[str]) -> ValidationRule:
        """Create rule for required fields."""
        async def validator(data: Dict, context: Dict) -> bool:
            return all(field in data for field in fields)
        
        return ValidationRule(
            name="required_fields",
            description="Validates presence of required fields",
            validator=validator,
            error_message="Missing required fields"
        )
    
    @staticmethod
    def string_pattern(field: str, pattern: str) -> ValidationRule:
        """Create rule for string pattern matching."""
        async def validator(data: Dict, context: Dict) -> bool:
            value = data.get(field)
            if not value or not isinstance(value, str):
                return False
            return bool(re.match(pattern, value))
        
        return ValidationRule(
            name=f"string_pattern_{field}",
            description=f"Validates {field} against pattern",
            validator=validator,
            error_message=f"Invalid format for {field}"
        )
    
    @staticmethod
    def numeric_range(field: str,
                     min_value: float = None,
                     max_value: float = None) -> ValidationRule:
        """Create rule for numeric range validation."""
        async def validator(data: Dict, context: Dict) -> bool:
            value = data.get(field)
            if not isinstance(value, (int, float)):
                return False
            if min_value is not None and value < min_value:
                return False
            if max_value is not None and value > max_value:
                return False
            return True
        
        return ValidationRule(
            name=f"numeric_range_{field}",
            description=f"Validates {field} is within range",
            validator=validator,
            error_message=f"Value for {field} out of range"
        )
    
    @staticmethod
    def enum_values(field: str, valid_values: List[Any]) -> ValidationRule:
        """Create rule for enum value validation."""
        async def validator(data: Dict, context: Dict) -> bool:
            return data.get(field) in valid_values
        
        return ValidationRule(
            name=f"enum_values_{field}",
            description=f"Validates {field} is one of allowed values",
            validator=validator,
            error_message=f"Invalid value for {field}"
        ) 