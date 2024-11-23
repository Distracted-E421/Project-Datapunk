from typing import Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ThresholdConfig(BaseModel):
    """Configuration for monitoring thresholds"""
    
    # Response time thresholds (in seconds)
    response_time: Dict[str, float] = {
        "warning": 1.0,    # 1 second
        "critical": 3.0    # 3 seconds
    }
    
    # Error rate thresholds (in percentage)
    error_rate: Dict[str, float] = {
        "warning": 5.0,    # 5%
        "critical": 10.0   # 10%
    }
    
    # Resource usage thresholds
    cpu_usage: Dict[str, float] = {
        "warning": 70.0,   # 70%
        "critical": 85.0   # 85%
    }
    
    memory_usage: Dict[str, float] = {
        "warning": 75.0,   # 75%
        "critical": 90.0   # 90%
    }
    
    # Performance thresholds
    requests_per_second: Dict[str, float] = {
        "warning": 100.0,  # Below 100 RPS
        "critical": 50.0   # Below 50 RPS
    }
    
    # Cache performance
    cache_hit_rate: Dict[str, float] = {
        "warning": 70.0,   # Below 70%
        "critical": 50.0   # Below 50%
    }
    
    def check_threshold(self, metric: str, value: float) -> Optional[AlertSeverity]:
        """Check if value exceeds thresholds"""
        thresholds = getattr(self, metric, None)
        if not thresholds:
            return None
            
        if value >= thresholds.get("critical", float("inf")):
            return AlertSeverity.CRITICAL
        elif value >= thresholds.get("warning", float("inf")):
            return AlertSeverity.WARNING
        return None 