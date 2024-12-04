"""
Health Trend Analysis System

Provides predictive health monitoring for the Datapunk service mesh by analyzing
historical health data to identify degradation patterns and predict potential failures.

Key Features:
- Time series analysis of health scores
- Trend direction classification
- Future health state prediction
- Confidence scoring
- Service-level health aggregation

NOTE: This implementation uses linear regression for trend analysis. While simple,
it provides a good balance of performance and accuracy for health monitoring.
Future versions may implement more sophisticated algorithms as needed.
"""

from typing import Dict, List, Optional, Any
import structlog
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from .health_aware_metrics import HealthAwareMetrics

logger = structlog.get_logger()

class TrendDirection(Enum):
    """
    Classification of health score trends.
    
    Used to provide clear, actionable insights about service health trajectories.
    These states map to different alert levels in the monitoring system.
    """
    IMPROVING = "improving"   # Positive trend above threshold
    STABLE = "stable"        # No significant change
    DEGRADING = "degrading"  # Negative trend below threshold
    UNKNOWN = "unknown"      # Insufficient data for analysis

@dataclass
class HealthTrendConfig:
    """
    Configuration parameters for trend analysis.
    
    Default values are tuned for typical microservice behavior patterns.
    Adjust based on specific service characteristics and SLO requirements.
    
    NOTE: window_size and prediction_horizon affect memory usage and
    computation time. Scale carefully in large deployments.
    """
    window_size: int = 60        # Analysis window in minutes
    min_points: int = 10         # Minimum data points for reliable analysis
    degradation_threshold: float = -0.1  # Negative slope indicating degradation
    improvement_threshold: float = 0.1   # Positive slope indicating improvement
    prediction_horizon: int = 30  # Future prediction window in minutes
    alert_threshold: float = 0.5  # Critical health score threshold

class HealthTrend:
    """
    Encapsulates trend analysis results for a service instance.
    
    Combines multiple metrics to provide a comprehensive view of service health
    trajectory, including confidence scoring and future state predictions.
    """
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
    """
    Analyzes service health trends to predict potential degradation.
    
    Uses linear regression on historical health scores to identify trends and
    predict future health states. Designed to provide early warning of service
    degradation before critical failures occur.
    
    TODO: Implement non-linear regression for complex degradation patterns
    TODO: Add support for seasonal pattern detection
    """
    
    def __init__(self,
                 config: HealthTrendConfig,
                 metrics: HealthAwareMetrics):
        """
        Initialize trend analyzer with configuration and metrics system.
        
        Args:
            config: Analysis parameters and thresholds
            metrics: Interface to the metrics collection system
        """
        self.config = config
        self.metrics = metrics
        self.logger = logger.bind(component="health_trend")
        self._health_history: Dict[str, List[tuple[datetime, float]]] = {}
    
    def record_health_score(self,
                          service: str,
                          instance: str,
                          score: float):
        """
        Record new health score data point for trend analysis.
        
        Maintains a rolling window of health scores per service instance.
        Automatically prunes old data points to manage memory usage.
        
        Args:
            service: Service identifier
            instance: Instance identifier
            score: Health score [0.0-1.0]
        """
        key = f"{service}:{instance}"
        if key not in self._health_history:
            self._health_history[key] = []
        
        # Add new data point
        self._health_history[key].append((datetime.utcnow(), score))
        
        # Maintain rolling window to limit memory usage
        cutoff = datetime.utcnow() - timedelta(minutes=self.config.window_size)
        self._health_history[key] = [
            (ts, score) for ts, score in self._health_history[key]
            if ts > cutoff
        ]
    
    def analyze_trend(self,
                     service: str,
                     instance: str) -> HealthTrend:
        """
        Analyze health score trend for service instance.
        
        Performs linear regression on historical health scores to determine
        trend direction and predict future health states.
        
        IMPORTANT: Returns UNKNOWN status if insufficient data points exist.
        This prevents false positives during service startup or data gaps.
        
        Args:
            service: Service to analyze
            instance: Specific instance to analyze
            
        Returns:
            HealthTrend containing direction, predictions, and confidence score
        """
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
            # Convert time series to numpy arrays for analysis
            timestamps = np.array([
                (ts - history[0][0]).total_seconds()
                for ts, _ in history
            ])
            scores = np.array([score for _, score in history])
            
            # Perform linear regression
            slope, intercept = np.polyfit(timestamps, scores, 1)
            r_squared = self._calculate_r_squared(timestamps, scores, slope, intercept)
            
            # Classify trend direction
            direction = self._determine_direction(slope)
            
            # Generate future predictions
            future_times = np.array([
                timestamps[-1] + (i * 60)  # Project forward by minutes
                for i in range(1, self.config.prediction_horizon + 1)
            ])
            predictions = slope * future_times + intercept
            
            # Ensure predictions stay within valid range
            predictions = np.clip(predictions, 0, 1)
            
            # Calculate time until threshold breach
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
        """
        Calculate R-squared value to assess trend line fit quality.
        
        Higher R-squared values indicate more reliable trend predictions.
        
        Args:
            x: Time values
            y: Health score values
            slope: Calculated trend line slope
            intercept: Calculated trend line intercept
            
        Returns:
            R-squared value [0.0-1.0]
        """
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    def _determine_direction(self, slope: float) -> TrendDirection:
        """
        Classify trend direction based on slope and configured thresholds.
        
        Args:
            slope: Calculated trend line slope
            
        Returns:
            TrendDirection classification
        """
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
        """
        Calculate time until health score crosses alert threshold.
        
        IMPORTANT: Returns None if:
        - Slope is 0 (no trend)
        - Current score is already past threshold in trend direction
        - Trend will never reach threshold
        
        Args:
            slope: Trend line slope
            intercept: Trend line intercept
            current_score: Current health score
            threshold: Alert threshold value
            
        Returns:
            Minutes until threshold crossing, or None if N/A
        """
        if slope == 0:
            return None
            
        if slope > 0 and current_score < threshold:
            # Time until improvement above threshold
            time_to_threshold = (threshold - current_score) / slope
            return time_to_threshold if time_to_threshold > 0 else None
            
        if slope < 0 and current_score > threshold:
            # Time until degradation below threshold
            time_to_threshold = (threshold - current_score) / slope
            return time_to_threshold if time_to_threshold > 0 else None
            
        return None
    
    def get_service_health_summary(self, service: str) -> Dict[str, Any]:
        """
        Generate aggregate health trend summary for all instances of a service.
        
        Combines trend analysis from all instances to provide service-level
        health insights. Uses confidence scores to weight instance contributions.
        
        Args:
            service: Service to summarize
            
        Returns:
            Dictionary containing service-level health trend analysis
        """
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