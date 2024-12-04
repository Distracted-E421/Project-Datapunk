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
    """Policy enforcement middleware that evaluates security rules for incoming requests.
    
    This middleware acts as a centralized policy enforcement point (PEP) that evaluates
    multiple types of security rules (time-based, rate limiting, geo-location) before
    allowing requests to proceed. It integrates with a metrics system for monitoring
    and provides detailed logging for security auditing.
    
    Design Notes:
    - Rules are evaluated asynchronously to minimize performance impact
    - Failed rules result in immediate 403 rejection
    - All rule evaluations are tracked via metrics for monitoring
    """
    
    def __init__(self,
                 app,
                 rule_engine: RuleEngine,
                 metrics: 'MetricsClient'):
        """Initialize the middleware with rule engine and metrics client.
        
        Args:
            app: The FastAPI application instance
            rule_engine: Engine responsible for evaluating security rules
            metrics: Client for tracking enforcement metrics
        """
        super().__init__(app)
        self.rule_engine = rule_engine
        self.metrics = metrics
        self.logger = logger.bind(component="policy_enforcement")
    
    async def dispatch(self,
                      request: Request,
                      call_next) -> Any:
        """Enforce security policies by evaluating rules against the request.
        
        The evaluation process:
        1. Extracts policy context from request
        2. Evaluates applicable security rules
        3. Rejects requests that fail any rules
        4. Tracks metrics for all evaluations
        
        Args:
            request: The incoming FastAPI request
            call_next: Async function to call the next middleware/route handler
            
        Returns:
            The response from the next handler if all rules pass
            
        Raises:
            HTTPException: 403 if any rules fail, 500 for unexpected errors
        """
        try:
            # Default to ACCESS policy if not explicitly set
            policy_type = getattr(request.state, "policy_type", PolicyType.ACCESS)
            
            # Construct evaluation context with all relevant request data
            # This context is passed to each rule for evaluation
            context = {
                "method": request.method,
                "path": request.url.path,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "client_ip": request.client.host,
                "timestamp": datetime.utcnow().isoformat(),
                "policy_type": policy_type.value
            }
            
            # Evaluate core security rules that apply to all requests
            # NOTE: Additional rule types can be added here as needed
            rule_results = await self.rule_engine.evaluate_rules(
                context=context,
                rule_types={
                    RuleType.TIME_BASED,    # Enforces time window restrictions
                    RuleType.RATE_LIMIT,    # Prevents abuse through rate limiting
                    RuleType.GEO_LOCATION   # Enforces geographic access controls
                }
            )
            
            # Track and handle any failed rules
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
            
            # Store results for potential use by downstream handlers
            request.state.rule_results = rule_results
            
            response = await call_next(request)
            
            # Track metrics for monitoring and alerting
            self._update_metrics(request, rule_results, response)
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (including our 403s) without modification
            raise
        except Exception as e:
            # Log unexpected errors and convert to 500 response
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
        """Track metrics for policy enforcement and individual rule results.
        
        Captures:
        - Overall enforcement results per endpoint
        - Individual rule pass/fail counts
        - Response status codes
        
        This data enables monitoring of:
        - Policy effectiveness
        - Rule failure patterns
        - Potential security incidents
        """
        self.metrics.increment(
            "policy_enforcement_total",
            {
                "path": request.url.path,
                "method": request.method,
                "status": response.status_code,
                "rules_passed": str(all(rule_results.values())).lower()
            }
        )
        
        # Track granular results for each rule
        for rule_id, result in rule_results.items():
            self.metrics.increment(
                "policy_rule_results",
                {
                    "rule_id": rule_id,
                    "result": str(result).lower()
                }
            )