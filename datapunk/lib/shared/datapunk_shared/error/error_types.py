from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class ErrorSeverity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"

@dataclass
class ErrorContext:
    service_id: str
    operation: str
    trace_id: str
    timestamp: float
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class ServiceError(Exception):
    code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    retry_allowed: bool = True
    http_status: int = 500
    cause: Optional[Exception] = None 