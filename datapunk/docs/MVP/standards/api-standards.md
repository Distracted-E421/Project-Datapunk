# API Standards

## Purpose

Define consistent API design patterns, versioning strategies, and documentation standards across all Datapunk services.

## Context

APIs serve as the primary interface between services and clients, requiring standardization for maintainability, security, and usability.

## Design/Details

### 1. API Versioning

```yaml
versioning_strategy:
  format: "v{major}"  # e.g., v1, v2
  location: "url-path"  # /api/v1/resource
  
  compatibility:
    breaking_changes: "new_version"
    non_breaking: "same_version"
    deprecation_period: "6_months"
    
  version_metadata:
    header: "X-API-Version"
    response_field: "_version"
    documentation_tag: "version"
```

### 2. URL Structure

```yaml
url_patterns:
  base: "/api/v{version}"
  resource: "/{resource}"
  collection: "/{resource}s"
  instance: "/{resource}s/{id}"
  action: "/{resource}s/{id}/{action}"
  
  examples:
    - "/api/v1/users"           # List users
    - "/api/v1/users/123"       # Get user
    - "/api/v1/users/123/activate"  # Action
    - "/api/v1/search?q=term"   # Search
```

### 3. HTTP Methods and Status Codes

```yaml
http_methods:
  GET:
    purpose: "Retrieve resource(s)"
    idempotent: true
    cacheable: true
    success_codes: [200, 206]
    
  POST:
    purpose: "Create resource"
    idempotent: false
    cacheable: false
    success_codes: [201]
    
  PUT:
    purpose: "Replace resource"
    idempotent: true
    cacheable: false
    success_codes: [200, 204]
    
  PATCH:
    purpose: "Partial update"
    idempotent: true
    cacheable: false
    success_codes: [200, 204]
    
  DELETE:
    purpose: "Remove resource"
    idempotent: true
    cacheable: false
    success_codes: [204]

status_codes:
  success:
    200: "OK - Request succeeded"
    201: "Created - Resource created"
    204: "No Content - Success with no body"
    
  client_errors:
    400: "Bad Request - Invalid input"
    401: "Unauthorized - Authentication required"
    403: "Forbidden - Insufficient permissions"
    404: "Not Found - Resource doesn't exist"
    409: "Conflict - Resource state conflict"
    422: "Unprocessable Entity - Validation failed"
    429: "Too Many Requests - Rate limit exceeded"
    
  server_errors:
    500: "Internal Server Error"
    502: "Bad Gateway"
    503: "Service Unavailable"
    504: "Gateway Timeout"
```

### 4. Request/Response Format

```json
{
  "request": {
    "headers": {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "X-Request-ID": "uuid",
      "X-API-Version": "v1"
    },
    "body": {
      "data": {},
      "meta": {
        "client_version": "string",
        "timestamp": "ISO8601"
      }
    }
  },
  "response": {
    "headers": {
      "Content-Type": "application/json",
      "X-Request-ID": "uuid",
      "X-Rate-Limit-Remaining": "integer"
    },
    "body": {
      "data": {},
      "meta": {
        "version": "string",
        "timestamp": "ISO8601",
        "pagination": {
          "total": "integer",
          "page": "integer",
          "per_page": "integer"
        }
      },
      "errors": [{
        "code": "string",
        "message": "string",
        "field": "string",
        "details": {}
      }]
    }
  }
}
```

### 5. Documentation Standards

```yaml
openapi:
  version: "3.0.3"
  format: "yaml"
  location: "/docs/api/openapi.yaml"
  
  components:
    - schemas
    - security_schemes
    - parameters
    - responses
    
  required_sections:
    - description
    - authentication
    - rate_limits
    - examples
    - error_responses
```

### 6. Input Validation

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class APIModel(BaseModel):
    """Base model for API requests/responses."""
    class Config:
        extra = "forbid"  # Reject unknown fields
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    order: Optional[str] = Field(default="asc", regex="^(asc|desc)$")

class ErrorResponse(BaseModel):
    """Standard error response."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[dict] = None
```

## Implementation Patterns

### 1. API Versioning Implementation

```python
from fastapi import FastAPI, APIRouter
from typing import Callable

class VersionedAPI:
    def __init__(self):
        self.app = FastAPI()
        self.versions = {}
        
    def version(self, ver: str) -> Callable:
        """Decorator to version API endpoints."""
        def decorator(func: Callable) -> Callable:
            if ver not in self.versions:
                self.versions[ver] = APIRouter(prefix=f"/api/{ver}")
            router = self.versions[ver]
            return router.get(func.__name__)(func)
        return decorator
    
    def mount_versions(self):
        """Mount all versioned routers."""
        for ver, router in self.versions.items():
            self.app.include_router(router)
```

### 2. Request Validation

```python
from fastapi import Request, HTTPException
from typing import Type, TypeVar
from pydantic import ValidationError

T = TypeVar('T', bound=BaseModel)

async def validate_request(request: Request, model: Type[T]) -> T:
    """Validate request body against model."""
    try:
        body = await request.json()
        return model.parse_obj(body)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=e.errors()
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
```

## Security Considerations

### 1. Authentication and Authorization

```yaml
security:
  authentication:
    required: true
    methods:
      - "JWT"
      - "API Key"
      - "OAuth2"
    
  authorization:
    rbac_enabled: true
    scope_required: true
    audit_logging: true
```

### 2. Rate Limiting

```yaml
rate_limiting:
  default_limits:
    requests_per_second: 10
    burst: 20
    
  custom_limits:
    authenticated:
      requests_per_second: 50
      burst: 100
    
  headers:
    - "X-RateLimit-Limit"
    - "X-RateLimit-Remaining"
    - "X-RateLimit-Reset"
```

## Monitoring and Metrics

```yaml
api_metrics:
  request_duration:
    type: "histogram"
    buckets: [0.1, 0.5, 1.0, 2.0, 5.0]
    
  status_codes:
    type: "counter"
    labels: ["method", "path", "status"]
    
  active_requests:
    type: "gauge"
    labels: ["method", "path"]
```

## Known Issues and Mitigations

### 1. Version Compatibility

```python
class VersionCompatibility:
    def __init__(self):
        self.compatibility_matrix = {}
        
    def register_compatibility(self,
                             old_version: str,
                             new_version: str,
                             transformer: Callable):
        """Register version compatibility transformer."""
        self.compatibility_matrix[(old_version, new_version)] = transformer
    
    async def transform_request(self,
                              request_data: dict,
                              from_version: str,
                              to_version: str) -> dict:
        """Transform request between versions."""
        transformer = self.compatibility_matrix.get((from_version, to_version))
        if not transformer:
            raise ValueError(f"No transformer for {from_version} -> {to_version}")
        return await transformer(request_data)
```

### 2. Documentation Drift

```python
class APIDocValidator:
    async def validate_endpoints(self):
        """Validate API documentation against actual endpoints."""
        schema = self.load_openapi_schema()
        routes = self.get_actual_routes()
        
        for route in routes:
            if not self.is_documented(route, schema):
                logger.warning(f"Undocumented endpoint: {route}")
```

## Testing Requirements

```yaml
api_testing:
  required_tests:
    - input_validation
    - authentication
    - authorization
    - rate_limiting
    - version_compatibility
    
  performance_tests:
    - response_time
    - concurrent_requests
    - rate_limit_behavior
```
