from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
import structlog
from datetime import datetime
import pytz
from .key_policies_extended import AdvancedKeyPolicy, ResourceType, TimeWindow
from ..monitoring import MetricsClient

logger = structlog.get_logger()

class PolicyEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing advanced key policies."""
    
    def __init__(self,
                 app,
                 metrics: MetricsClient):
        super().__init__(app)
        self.metrics = metrics
        self.logger = logger.bind(component="policy_enforcement")
    
    async def dispatch(self,
                      request: Request,
                      call_next) -> Any:
        """Enforce policy on request."""
        try:
            # Get API key and policy from request state
            # (set by previous authentication middleware)
            key = getattr(request.state, "api_key", None)
            policy = getattr(request.state, "key_policy", None)
            
            if not key or not policy:
                return await call_next(request)
            
            # Perform all policy checks
            await self._check_resource_access(request, policy)
            await self._check_time_windows(request, policy)
            await self._check_quota(request, policy)
            await self._check_geo_restrictions(request, policy)
            await self._check_compliance(request, policy)
            
            # Add policy context to request
            request.state.policy_context = {
                "monitoring_level": policy.monitoring_level,
                "encryption_level": policy.encryption_level,
                "compliance": policy.compliance
            }
            
            # Execute request
            response = await call_next(request)
            
            # Update metrics
            self._update_metrics(request, policy, response)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("policy_enforcement_failed",
                            error=str(e))
            raise HTTPException(status_code=500,
                              detail="Policy enforcement failed")
    
    async def _check_resource_access(self,
                                   request: Request,
                                   policy: AdvancedKeyPolicy):
        """Check resource access permissions."""
        resource_type = self._get_resource_type(request)
        
        if policy.denied_resources and resource_type in policy.denied_resources:
            raise HTTPException(status_code=403,
                              detail="Resource access denied")
            
        if (policy.allowed_resources and 
            resource_type not in policy.allowed_resources):
            raise HTTPException(status_code=403,
                              detail="Resource not allowed")
    
    async def _check_time_windows(self,
                                request: Request,
                                policy: AdvancedKeyPolicy):
        """Check time-based access restrictions."""
        if not policy.time_windows:
            return
            
        now = datetime.now(pytz.timezone(policy.time_windows[0].timezone))
        current_time = now.time()
        current_day = now.weekday()
        
        allowed = any(
            current_day in window.days and
            window.start_time <= current_time <= window.end_time
            for window in policy.time_windows
        )
        
        if not allowed:
            raise HTTPException(status_code=403,
                              detail="Access not allowed at this time")
    
    async def _check_quota(self,
                          request: Request,
                          policy: AdvancedKeyPolicy):
        """Check resource quota limits."""
        if not policy.quota:
            return
            
        # Implementation would check quota usage from storage
        # This is a placeholder
        pass
    
    async def _check_geo_restrictions(self,
                                    request: Request,
                                    policy: AdvancedKeyPolicy):
        """Check geographic restrictions."""
        if not policy.geo_restrictions:
            return
            
        # Implementation would check client geo-location
        # This is a placeholder
        pass
    
    async def _check_compliance(self,
                              request: Request,
                              policy: AdvancedKeyPolicy):
        """Check compliance requirements."""
        if not policy.compliance:
            return
            
        if (policy.compliance.encryption_required and
            not request.headers.get("X-Encryption-Level")):
            raise HTTPException(status_code=400,
                              detail="Encryption required")
    
    def _get_resource_type(self, request: Request) -> ResourceType:
        """Determine resource type from request."""
        path = request.url.path.lower()
        
        if "/model" in path:
            return ResourceType.MODEL
        elif "/analytics" in path:
            return ResourceType.ANALYTICS
        elif "/stream" in path:
            return ResourceType.STREAM
        elif "/admin" in path:
            return ResourceType.ADMIN
        elif "/storage" in path:
            return ResourceType.STORAGE
        elif "/compute" in path:
            return ResourceType.COMPUTE
        else:
            return ResourceType.DATA
    
    def _update_metrics(self,
                       request: Request,
                       policy: AdvancedKeyPolicy,
                       response: Any):
        """Update policy enforcement metrics."""
        self.metrics.increment(
            "policy_enforcement_total",
            {
                "resource_type": self._get_resource_type(request).value,
                "policy_type": policy.type.value,
                "status": response.status_code
            }
        ) 