"""
Circuit Breaker Failure Prediction

Implements predictive failure detection for circuit breaker system.
Uses statistical analysis and machine learning techniques to predict
service failures before they occur.

Key features:
- Time series analysis
- Pattern recognition
- Anomaly detection
- Resource utilization prediction
- Error rate forecasting
"""

from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import asyncio
import structlog
import numpy as np
from datetime import datetime, timedelta
from collections import deque
from .circuit_breaker_strategies import CircuitState

logger = structlog.get_logger()

class PredictionMetric(Enum):
    """Metrics used for failure prediction"""
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    REQUEST_RATE = "request_rate"
    QUEUE_SIZE = "queue_size"

class PredictionWindow:
    """Configuration for prediction window"""
    def __init__(self,
                 size_seconds: int = 300,  # 5 minutes
                 resolution_seconds: int = 10):  # 10 second buckets
        self.size_seconds = size_seconds
        self.resolution_seconds = resolution_seconds
        self.num_buckets = size_seconds // resolution_seconds

class MetricHistory:
    """Stores historical metric data"""
    def __init__(self, window: PredictionWindow):
        self.window = window
        self.values = deque(maxlen=window.num_buckets)
        self.timestamps = deque(maxlen=window.num_buckets)
        
    def add(self, value: float, timestamp: datetime = None):
        """Add new metric value"""
        if timestamp is None:
            timestamp = datetime.utcnow()
            
        self.values.append(value)
        self.timestamps.append(timestamp)
        
    def get_series(self) -> Tuple[List[float], List[datetime]]:
        """Get time series data"""
        return list(self.values), list(self.timestamps)
        
    def is_ready(self) -> bool:
        """Check if enough data is available"""
        return len(self.values) == self.window.num_buckets

class AnomalyDetector:
    """
    Detects anomalies in metric time series.
    
    Uses statistical methods to identify unusual patterns
    that may indicate impending failures.
    """
    
    def __init__(self,
                 threshold_sigmas: float = 3.0,
                 min_samples: int = 30):
        self.threshold_sigmas = threshold_sigmas
        self.min_samples = min_samples
        
    def is_anomalous(self, values: List[float]) -> bool:
        """Check if latest value is anomalous"""
        if len(values) < self.min_samples:
            return False
            
        mean = np.mean(values[:-1])  # Exclude latest
        std = np.std(values[:-1])
        latest = values[-1]
        
        z_score = abs(latest - mean) / std if std > 0 else 0
        return z_score > self.threshold_sigmas

class TrendAnalyzer:
    """
    Analyzes metric trends to predict future values.
    
    Uses linear regression and moving averages to
    detect concerning trends early.
    """
    
    def __init__(self,
                 forecast_seconds: int = 60,
                 trend_threshold: float = 0.1):
        self.forecast_seconds = forecast_seconds
        self.trend_threshold = trend_threshold
        
    def predict_value(self,
                     values: List[float],
                     timestamps: List[datetime]) -> float:
        """Predict value at forecast horizon"""
        if not values:
            return 0.0
            
        # Convert timestamps to seconds from start
        x = [(t - timestamps[0]).total_seconds() 
             for t in timestamps]
        y = values
        
        # Fit linear regression
        coeffs = np.polyfit(x, y, deg=1)
        slope = coeffs[0]
        
        # Project forward
        forecast_x = x[-1] + self.forecast_seconds
        forecast_y = np.polyval(coeffs, forecast_x)
        
        return forecast_y
        
    def get_trend(self,
                  values: List[float],
                  timestamps: List[datetime]) -> float:
        """Calculate trend strength"""
        if len(values) < 2:
            return 0.0
            
        # Use linear regression slope
        x = [(t - timestamps[0]).total_seconds() 
             for t in timestamps]
        y = values
        
        coeffs = np.polyfit(x, y, deg=1)
        slope = coeffs[0]
        
        # Normalize by mean value
        mean = np.mean(values)
        if mean == 0:
            return 0.0
            
        return slope / mean

class FailurePredictor:
    """
    Predicts service failures using multiple detection methods.
    
    Features:
    - Multi-metric monitoring
    - Anomaly detection
    - Trend analysis
    - Pattern matching
    - Confidence scoring
    """
    
    def __init__(self,
                 metrics_client=None,
                 window: Optional[PredictionWindow] = None):
        self.metrics = metrics_client
        self.window = window or PredictionWindow()
        self.logger = logger.bind(component="failure_predictor")
        
        # Initialize detectors
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        
        # Initialize metric histories
        self.histories: Dict[PredictionMetric, MetricHistory] = {
            metric: MetricHistory(self.window)
            for metric in PredictionMetric
        }
        
        # Configure thresholds
        self.thresholds = {
            PredictionMetric.ERROR_RATE: 0.1,    # 10% errors
            PredictionMetric.LATENCY: 1000.0,    # 1 second
            PredictionMetric.CPU_USAGE: 80.0,    # 80% CPU
            PredictionMetric.MEMORY_USAGE: 80.0, # 80% memory
            PredictionMetric.REQUEST_RATE: None,  # Learned dynamically
            PredictionMetric.QUEUE_SIZE: None    # Learned dynamically
        }
        
    async def record_metric(self,
                          metric: PredictionMetric,
                          value: float):
        """Record new metric value"""
        history = self.histories[metric]
        history.add(value)
        
        if self.metrics:
            await self.metrics.gauge(
                f"circuit_breaker_metric_{metric.value}",
                value
            )
            
    async def predict_failure(self) -> Tuple[bool, float]:
        """
        Predict if service is likely to fail.
        
        Returns:
            Tuple[bool, float]: (will_fail, confidence)
        """
        # Check if we have enough data
        if not all(h.is_ready() for h in self.histories.values()):
            return False, 0.0
            
        # Calculate prediction signals
        signals = []
        
        for metric, history in self.histories.items():
            values, timestamps = history.get_series()
            
            # Check current thresholds
            threshold = self.thresholds[metric]
            if threshold and values[-1] > threshold:
                signals.append(0.8)  # High confidence
                
            # Check for anomalies
            if self.anomaly_detector.is_anomalous(values):
                signals.append(0.6)  # Medium confidence
                
            # Check trends
            trend = self.trend_analyzer.get_trend(values, timestamps)
            if abs(trend) > self.trend_analyzer.trend_threshold:
                signals.append(0.4)  # Lower confidence
                
            # Check forecasts
            forecast = self.trend_analyzer.predict_value(
                values,
                timestamps
            )
            if threshold and forecast > threshold:
                signals.append(0.5)  # Medium confidence
                
        if not signals:
            return False, 0.0
            
        # Combine signals
        confidence = max(signals)  # Use strongest signal
        will_fail = confidence > 0.5  # Threshold for prediction
        
        if will_fail and self.metrics:
            await self.metrics.increment(
                "circuit_breaker_failure_predicted",
                {"confidence": f"{confidence:.2f}"}
            )
            
        return will_fail, confidence
        
    async def update_thresholds(self):
        """Update dynamic thresholds based on history"""
        for metric, history in self.histories.items():
            if self.thresholds[metric] is not None:
                continue  # Skip fixed thresholds
                
            values, _ = history.get_series()
            if not values:
                continue
                
            # Use mean + 2 standard deviations
            mean = np.mean(values)
            std = np.std(values)
            self.thresholds[metric] = mean + 2 * std
            
            if self.metrics:
                await self.metrics.gauge(
                    f"circuit_breaker_threshold_{metric.value}",
                    self.thresholds[metric]
                )
                
    def get_prediction_metrics(self) -> Dict[str, Any]:
        """Get current prediction metrics for monitoring"""
        metrics = {}
        
        for metric, history in self.histories.items():
            values, _ = history.get_series()
            if not values:
                continue
                
            metrics[f"{metric.value}_current"] = values[-1]
            metrics[f"{metric.value}_mean"] = np.mean(values)
            metrics[f"{metric.value}_std"] = np.std(values)
            
            if self.thresholds[metric] is not None:
                metrics[f"{metric.value}_threshold"] = \
                    self.thresholds[metric]
                    
        return metrics 