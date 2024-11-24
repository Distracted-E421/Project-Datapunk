from typing import Dict, Optional, TYPE_CHECKING
import structlog
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import pytz

from .rules import RuleEngine, RuleType
from ..types import PolicyType, PolicyStatus
from ...core.exceptions import AuthError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient

logger = structlog.get_logger()

class PolicyEnforcementMiddleware(BaseHTTPMiddleware):
    """Enforces policy rules on requests."""
    
    def __init__(self,
                 app,
                 rule_engine: RuleEngine,
                 metrics: 'MetricsClient'):
        super().__init__(app)
        self.rule_engine = rule_engine
        self.metrics = metrics
        self.logger = logger.bind(component="policy_enforcement")
    
    async def dispatch(self,
                      request: Request,
                      call_next) -> Any:
        """Enforce policy on request."""
        try:
            # Get policy context from request state
            policy_type = getattr(request.state, "policy_type", PolicyType.ACCESS)
            
            # Build evaluation context
            context = {
                "method": request.method,
                "path": request.url.path,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "client_ip": request.client.host,
                "timestamp": datetime.utcnow().isoformat(),
                "policy_type": policy_type.value
            }
            
            # Evaluate applicable rules
            rule_results = await self.rule_engine.evaluate_rules(
                context=context,
                rule_types={
                    RuleType.TIME_BASED,
                    RuleType.RATE_LIMIT,
                    RuleType.GEO_LOCATION
                }
            )
            
            # Check if any rules failed
            failed_rules = {
                rule_id: result
                for rule_id, result in rule_results.items()
                if not result
            }
            
            if failed_rules:
                self.logger.warning("policy_rules_failed",
                                  failed_rules=failed_rules)
                raise HTTPException(
                    status_code=403,
                    detail=f"Policy rules failed: {list(failed_rules.keys())}"
                )
            
            # Add rule results to request state
            request.state.rule_results = rule_results
            
            # Execute request
            response = await call_next(request)
            
            # Update metrics
            self._update_metrics(request, rule_results, response)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("policy_enforcement_failed",
                            error=str(e))
            raise HTTPException(
                status_code=500,
                detail="Policy enforcement failed"
            )
    
    def _update_metrics(self,
                       request: Request,
                       rule_results: Dict[str, bool],
                       response: Any) -> None:
        """Update enforcement metrics."""
        self.metrics.increment(
            "policy_enforcement_total",
            {
                "path": request.url.path,
                "method": request.method,
                "status": response.status_code,
                "rules_passed": str(all(rule_results.values())).lower()
            }
        )
        
        # Track individual rule results
        for rule_id, result in rule_results.items():
            self.metrics.increment(
                "policy_rule_results",
                {
                    "rule_id": rule_id,
                    "result": str(result).lower()
                }
            )