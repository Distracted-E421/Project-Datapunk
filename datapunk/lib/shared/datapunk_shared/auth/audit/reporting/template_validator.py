"""
Template validation for audit reports.

This module provides validation capabilities for Jinja2 templates used in audit reporting.
It ensures that templates have all required variables and follows best practices for
template structure and performance.

Key features:
- Variable presence validation
- Syntax error detection
- Performance warning detection
- Nested structure analysis
"""
from typing import Dict, List, Optional, Any
import structlog
from jinja2 import Environment, meta
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class TemplateValidationResult:
    """
    Result of template validation containing comprehensive validation outcomes.
    
    Attributes:
        valid: Overall validation status
        missing_variables: Variables required by template but not provided in data
        undefined_variables: Variables provided in data but not used in template
        syntax_errors: List of template syntax parsing errors
        warnings: Non-critical issues that might affect template performance
    """

class TemplateValidator:
    """
    Validates Jinja2 templates and their data for audit report generation.
    
    This validator ensures that templates can be safely rendered with provided data
    by performing comprehensive validation checks including variable presence,
    syntax correctness, and performance considerations.
    """
    
    def __init__(self, jinja_env: Environment):
        self.env = jinja_env
        self.logger = logger.bind(component="template_validator")
    
    def validate_template(self,
                         template_name: str,
                         data: Dict[str, Any]) -> TemplateValidationResult:
        """
        Validate template against provided data.
        
        Performs multiple validation checks:
        1. Ensures all required template variables are present in data
        2. Identifies unused variables in provided data
        3. Validates template syntax
        4. Checks for potential performance issues
        
        Args:
            template_name: Name of the template to validate
            data: Dictionary containing variables for template rendering
            
        Returns:
            TemplateValidationResult containing validation outcomes
            
        Note:
            Template loading errors are caught and returned as syntax errors
            rather than raising exceptions to maintain consistent error handling.
        """
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
        """
        Check if variable exists in nested data structure.
        
        Supports dot notation (e.g., 'user.address.street') for nested dictionary access.
        
        Args:
            var: Variable name with optional dot notation
            data: Dictionary to search for variable
            
        Returns:
            True if variable exists at specified path, False otherwise
            
        Note:
            Returns False if any part of the path is invalid or if intermediate
            values are not dictionaries.
        """
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
        """
        Check template syntax using Jinja2 parser.
        
        Args:
            template_source: Raw template content
            
        Returns:
            List of syntax error messages, empty if syntax is valid
            
        Note:
            Catches and converts all parsing exceptions to string messages
            for consistent error reporting.
        """
        errors = []
        try:
            self.env.parse(template_source)
        except Exception as e:
            errors.append(str(e))
        return errors
    
    def _check_warnings(self,
                       template_source: str,
                       data: Dict) -> List[str]:
        """
        Check for potential performance and maintainability issues.
        
        Current checks include:
        - Detection of nested loops which may impact performance
        - Large data structures that could slow template rendering
        
        TODO: Consider adding checks for:
        - Complex conditional logic
        - Deep nesting levels
        - Template length/complexity metrics
        
        Args:
            template_source: Raw template content
            data: Template variables
            
        Returns:
            List of warning messages for potential issues
        """
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