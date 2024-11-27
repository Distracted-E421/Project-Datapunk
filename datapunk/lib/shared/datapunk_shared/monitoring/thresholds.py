from typing import Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

"""
Threshold Configuration and Monitoring System for Datapunk

This module implements a flexible threshold configuration system for monitoring
various metrics across the Datapunk platform. It enables dynamic alerting based
on predefined thresholds for different performance and operational metrics.

Key Features:
- Configurable thresholds for multiple metric types
- Multi-level alerting (warning, critical)
- Easy-to-use interface for threshold checks
- Extensible for custom metric types

Design Philosophy:
- Prioritize simplicity in configuration
- Enable fine-grained control over alerting
- Support gradual degradation detection
- Facilitate easy integration with monitoring systems

NOTE: This implementation assumes static threshold configuration
TODO: Add support for dynamic threshold adjustments based on historical data
"""

class AlertSeverity(Enum):
    """
    Alert severity levels for threshold breaches.
    
    Why These Levels:
    INFO: For informational notifications, no immediate action required
    WARNING: Indicates potential issues, may require attention
    CRITICAL: Signals severe problems, immediate action typically needed
    
    NOTE: These levels align with common monitoring system conventions
    """
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ThresholdConfig(BaseModel):
    """
    Configuration for monitoring thresholds across various metrics.
    
    Design Considerations:
    - Uses dictionary for flexible threshold definitions
    - Separates warning and critical thresholds for gradual alerting
    - Includes common performance and resource metrics
    
    WARNING: Ensure thresholds are set appropriately for your system's capacity
    TODO: Add support for custom metric thresholds
    """
    
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
        """
        Checks if a given metric value exceeds defined thresholds.
        
        Implementation Notes:
        - Prioritizes critical threshold check
        - Returns None if no threshold is breached
        - Assumes higher values are worse (except for requests_per_second and cache_hit_rate)
        
        FIXME: Add support for metrics where lower values are worse
        """
        thresholds = getattr(self, metric, None)
        if not thresholds:
            return None
            
        if value >= thresholds.get("critical", float("inf")):
            return AlertSeverity.CRITICAL
        elif value >= thresholds.get("warning", float("inf")):
            return AlertSeverity.WARNING
        return None 