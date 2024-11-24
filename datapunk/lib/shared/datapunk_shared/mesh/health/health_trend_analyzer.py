from typing import Dict, List, Optional, Any
import structlog
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from .health_aware_metrics import HealthAwareMetrics

logger = structlog.get_logger()

class TrendDirection(Enum):
    """Direction of health trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    UNKNOWN = "unknown"

@dataclass
class HealthTrendConfig:
    """Configuration for health trend analysis."""
    window_size: int = 60  # Number of data points to analyze
    min_points: int = 10   # Minimum points needed for analysis
    degradation_threshold: float = -0.1  # Negative slope threshold
    improvement_threshold: float = 0.1   # Positive slope threshold
    prediction_horizon: int = 30  # Future points to predict
    alert_threshold: float = 0.5  # Health score threshold for alerts

class HealthTrend:
    """Health trend analysis result."""
    def __init__(self,
                 direction: TrendDirection,
                 slope: float,
                 prediction: Optional[List[float]] = None,
                 confidence: float = 0.0,
                 details: Optional[Dict] = None):
        self.direction = direction
        self.slope = slope
        self.prediction = prediction
        self.confidence = confidence
        self.details = details or {}

class HealthTrendAnalyzer:
    """Analyzes health score trends to predict degradation."""
    
    def __init__(self,
                 config: HealthTrendConfig,
                 metrics: HealthAwareMetrics):
        self.config = config
        self.metrics = metrics
        self.logger = logger.bind(component="health_trend")
        self._health_history: Dict[str, List[tuple[datetime, float]]] = {}
    
    def record_health_score(self,
                          service: str,
                          instance: str,
                          score: float):
        """Record a new health score data point."""
        key = f"{service}:{instance}"
        if key not in self._health_history:
            self._health_history[key] = []
        
        # Add new point
        self._health_history[key].append((datetime.utcnow(), score))
        
        # Trim old data
        cutoff = datetime.utcnow() - timedelta(minutes=self.config.window_size)
        self._health_history[key] = [
            (ts, score) for ts, score in self._health_history[key]
            if ts > cutoff
        ]
    
    def analyze_trend(self,
                     service: str,
                     instance: str) -> HealthTrend:
        """Analyze health score trend for service instance."""
        key = f"{service}:{instance}"
        history = self._health_history.get(key, [])
        
        if len(history) < self.config.min_points:
            return HealthTrend(
                direction=TrendDirection.UNKNOWN,
                slope=0.0,
                confidence=0.0,
                details={"reason": "insufficient_data"}
            )
        
        try:
            # Extract time series data
            timestamps = np.array([
                (ts - history[0][0]).total_seconds()
                for ts, _ in history
            ])
            scores = np.array([score for _, score in history])
            
            # Calculate trend
            slope, intercept = np.polyfit(timestamps, scores, 1)
            r_squared = self._calculate_r_squared(timestamps, scores, slope, intercept)
            
            # Determine trend direction
            direction = self._determine_direction(slope)
            
            # Make predictions
            future_times = np.array([
                timestamps[-1] + (i * 60)  # Predict every minute
                for i in range(1, self.config.prediction_horizon + 1)
            ])
            predictions = slope * future_times + intercept
            
            # Clip predictions to valid range [0, 1]
            predictions = np.clip(predictions, 0, 1)
            
            # Calculate time to threshold crossing
            time_to_threshold = self._calculate_threshold_crossing(
                slope,
                intercept,
                scores[-1],
                self.config.alert_threshold
            )
            
            return HealthTrend(
                direction=direction,
                slope=slope,
                prediction=predictions.tolist(),
                confidence=r_squared,
                details={
                    "intercept": intercept,
                    "r_squared": r_squared,
                    "time_to_threshold": time_to_threshold,
                    "data_points": len(history)
                }
            )
            
        except Exception as e:
            self.logger.error("trend_analysis_failed",
                            service=service,
                            instance=instance,
                            error=str(e))
            return HealthTrend(
                direction=TrendDirection.UNKNOWN,
                slope=0.0,
                confidence=0.0,
                details={"error": str(e)}
            )
    
    def _calculate_r_squared(self,
                           x: np.ndarray,
                           y: np.ndarray,
                           slope: float,
                           intercept: float) -> float:
        """Calculate R-squared value for trend line."""
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    def _determine_direction(self, slope: float) -> TrendDirection:
        """Determine trend direction based on slope."""
        if slope > self.config.improvement_threshold:
            return TrendDirection.IMPROVING
        elif slope < self.config.degradation_threshold:
            return TrendDirection.DEGRADING
        else:
            return TrendDirection.STABLE
    
    def _calculate_threshold_crossing(self,
                                    slope: float,
                                    intercept: float,
                                    current_score: float,
                                    threshold: float) -> Optional[float]:
        """Calculate time until health score crosses threshold."""
        if slope == 0:
            return None
            
        if slope > 0 and current_score < threshold:
            # Time to improvement above threshold
            time_to_threshold = (threshold - current_score) / slope
            return time_to_threshold if time_to_threshold > 0 else None
            
        if slope < 0 and current_score > threshold:
            # Time to degradation below threshold
            time_to_threshold = (threshold - current_score) / slope
            return time_to_threshold if time_to_threshold > 0 else None
            
        return None
    
    def get_service_health_summary(self, service: str) -> Dict[str, Any]:
        """Get health trend summary for all instances of a service."""
        instances = {}
        service_trend = TrendDirection.STABLE
        service_confidence = 0.0
        
        # Analyze each instance
        for key in self._health_history:
            if key.startswith(f"{service}:"):
                _, instance = key.split(":", 1)
                trend = self.analyze_trend(service, instance)
                instances[instance] = {
                    "direction": trend.direction.value,
                    "confidence": trend.confidence,
                    "details": trend.details
                }
                
                # Update service-level trend
                if trend.confidence > service_confidence:
                    service_confidence = trend.confidence
                    service_trend = trend.direction
        
        return {
            "service": service,
            "overall_trend": service_trend.value,
            "confidence": service_confidence,
            "instances": instances,
            "timestamp": datetime.utcnow().isoformat()
        } 