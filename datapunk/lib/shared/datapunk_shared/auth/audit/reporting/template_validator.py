"""Template validation for audit reports."""
from typing import Dict, List, Optional, Any
import structlog
from jinja2 import Environment, meta
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class TemplateValidationResult:
    """Result of template validation."""
    valid: bool
    missing_variables: List[str]
    undefined_variables: List[str]
    syntax_errors: List[str]
    warnings: List[str]

class TemplateValidator:
    """Validates Jinja2 templates and their data."""
    
    def __init__(self, jinja_env: Environment):
        self.env = jinja_env
        self.logger = logger.bind(component="template_validator")
    
    def validate_template(self,
                         template_name: str,
                         data: Dict[str, Any]) -> TemplateValidationResult:
        """Validate template against provided data."""
        try:
            # Get template
            template_source = self.env.loader.get_source(
                self.env,
                template_name
            )[0]
            
            # Parse template
            ast = self.env.parse(template_source)
            
            # Get required variables
            required_vars = meta.find_undeclared_variables(ast)
            
            # Check for missing variables
            missing_vars = [
                var for var in required_vars
                if not self._has_variable(var, data)
            ]
            
            # Check for undefined variables
            undefined_vars = [
                key for key in data.keys()
                if key not in required_vars
            ]
            
            # Check syntax
            syntax_errors = self._check_syntax(template_source)
            
            # Check for potential issues
            warnings = self._check_warnings(template_source, data)
            
            return TemplateValidationResult(
                valid=len(missing_vars) == 0 and len(syntax_errors) == 0,
                missing_variables=missing_vars,
                undefined_variables=undefined_vars,
                syntax_errors=syntax_errors,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error("template_validation_failed",
                            template=template_name,
                            error=str(e))
            return TemplateValidationResult(
                valid=False,
                missing_variables=[],
                undefined_variables=[],
                syntax_errors=[str(e)],
                warnings=[]
            )
    
    def _has_variable(self, var: str, data: Dict) -> bool:
        """Check if variable exists in data."""
        parts = var.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return False
                current = current[part]
            else:
                return False
        
        return True
    
    def _check_syntax(self, template_source: str) -> List[str]:
        """Check template syntax."""
        errors = []
        try:
            self.env.parse(template_source)
        except Exception as e:
            errors.append(str(e))
        return errors
    
    def _check_warnings(self,
                       template_source: str,
                       data: Dict) -> List[str]:
        """Check for potential issues."""
        warnings = []
        
        # Check for nested loops
        if "{% for" in template_source:
            if template_source.count("{% for") > 1:
                warnings.append("Template contains nested loops")
        
        # Check for large data structures
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 1000:
                warnings.append(f"Large list in {key} may impact performance")
            elif isinstance(value, dict) and len(value) > 100:
                warnings.append(f"Large dictionary in {key} may impact performance")
        
        return warnings 