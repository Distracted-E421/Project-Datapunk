from typing import Dict, Optional, Set, TYPE_CHECKING
import structlog
from datetime import datetime

from .standards import ComplianceStandards, ComplianceRule, ComplianceLevel
from ...core.exceptions import AuthError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient

logger = structlog.get_logger()

class ComplianceManager:
    """Manages compliance checks and validation."""
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 standards: ComplianceStandards):
        self.cache = cache_client
        self.metrics = metrics
        self.standards = standards
        self.logger = logger.bind(component="compliance_manager")
    
    async def validate_compliance(self,
                                data: Dict,
                                rules: Set[str]) -> Dict:
        """Validate data against compliance rules."""
        try:
            results = {}
            
            for rule_id in rules:
                rule = self.standards.rules.get(rule_id)
                if not rule:
                    continue
                
                validation_results = await self._run_validations(data, rule)
                results[rule_id] = {
                    "compliant": all(validation_results.values()),
                    "details": validation_results
                }
            
            return results
            
        except Exception as e:
            self.logger.error("compliance_validation_failed",
                            error=str(e))
            raise AuthError(f"Compliance validation failed: {str(e)}")
    
    async def _run_validations(self,
                             data: Dict,
                             rule: ComplianceRule) -> Dict[str, bool]:
        """Run all validations for a rule."""
        results = {}
        
        for check_name, check_method in rule.validations.items():
            validator = getattr(self, check_method, None)
            if validator:
                results[check_name] = await validator(data, rule)
            else:
                self.logger.warning("validation_method_not_found",
                                  method=check_method)
                results[check_name] = False
        
        return results 