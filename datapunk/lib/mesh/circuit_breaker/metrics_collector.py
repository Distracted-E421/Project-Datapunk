"""
Advanced Circuit Breaker Metrics Collector

Provides comprehensive metrics collection and analysis for the circuit breaker system.
Includes performance monitoring, pattern detection, and health status reporting.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import structlog
from dataclasses import dataclass
from statistics import mean, stdev
import numpy as np
from collections import deque

logger = structlog.get_logger()

@dataclass
class CircuitMetricsConfig:
    """Configuration for metrics collection"""
    window_size: int = 60  # Rolling window size in seconds
    bucket_size: int = 1   # Size of each time bucket in seconds
    percentiles: List[float] = (50, 90, 95, 99)  # Percentiles to track
    anomaly_threshold: float = 2.0  # Standard deviations for anomaly detection
    trend_window: int = 300  # Window for trend analysis in seconds

class MetricsBucket:
    """Time bucket for storing metrics"""
    def __init__(self):
        self.request_count: int = 0
        self.error_count: int = 0
        self.latencies: List[float] = []
        self.circuit_trips: int = 0
        self.recovery_attempts: int = 0
        self.partial_success: int = 0
        self.resource_usage: Dict[str, float] = {}
        self.timestamp: datetime = datetime.utcnow()

class CircuitBreakerMetricsCollector:
    """
    Advanced metrics collector for circuit breaker monitoring.
    
    Features:
    - Real-time metrics collection
    - Pattern detection
    - Anomaly detection
    - Trend analysis
    - Resource utilization tracking
    - Health status reporting
    """
    
    def __init__(self, config: Optional[CircuitMetricsConfig] = None):
        """Initialize metrics collector with configuration"""
        self.config = config or CircuitMetricsConfig()
        self.logger = logger.bind(component="circuit_breaker_metrics")
        
        # Initialize metric storage
        self.buckets: deque[MetricsBucket] = deque(maxlen=self.config.window_size)
        self.current_bucket: Optional[MetricsBucket] = None
        self.bucket_start: Optional[datetime] = None
        
        # Pattern detection state
        self.pattern_history: List[Dict[str, Any]] = []
        self.known_patterns: Dict[str, Any] = {}
        
        # Resource tracking
        self.resource_thresholds: Dict[str, float] = {}
        self.resource_baselines: Dict[str, float] = {}
        
        # Analysis state
        self.trend_data: Dict[str, deque] = {
            'error_rates': deque(maxlen=self.config.trend_window),
            'latencies': deque(maxlen=self.config.trend_window),
            'circuit_trips': deque(maxlen=self.config.trend_window)
        }

    async def start(self):
        """Start metrics collection"""
        self._ensure_current_bucket()
        asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Background task to clean up old metrics"""
        while True:
            try:
                now = datetime.utcnow()
                cutoff = now - timedelta(seconds=self.config.window_size)
                
                # Remove old buckets
                while self.buckets and self.buckets[0].timestamp < cutoff:
                    self.buckets.popleft()
                    
                # Update trend data
                await self._update_trends()
                
                # Sleep until next cleanup
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error("Error in metrics cleanup", error=str(e))

    def _ensure_current_bucket(self):
        """Ensure we have a current bucket for metrics"""
        now = datetime.utcnow()
        if (not self.current_bucket or 
            not self.bucket_start or
            (now - self.bucket_start).total_seconds() >= self.config.bucket_size):
            
            if self.current_bucket:
                self.buckets.append(self.current_bucket)
            
            self.current_bucket = MetricsBucket()
            self.bucket_start = now

    async def record_request(self, latency_ms: float, is_error: bool = False):
        """Record a request with its latency and status"""
        self._ensure_current_bucket()
        
        if self.current_bucket:
            self.current_bucket.request_count += 1
            self.current_bucket.latencies.append(latency_ms)
            
            if is_error:
                self.current_bucket.error_count += 1
                
            # Check for anomalies
            await self._check_anomalies(latency_ms, is_error)

    async def record_circuit_trip(self):
        """Record a circuit breaker trip"""
        self._ensure_current_bucket()
        
        if self.current_bucket:
            self.current_bucket.circuit_trips += 1
            
            # Analyze trip patterns
            await self._analyze_trip_patterns()

    async def record_recovery_attempt(self, success: bool):
        """Record a recovery attempt"""
        self._ensure_current_bucket()
        
        if self.current_bucket:
            self.current_bucket.recovery_attempts += 1
            if success:
                self.current_bucket.partial_success += 1

    async def record_resource_usage(self, resource: str, usage: float):
        """Record resource utilization"""
        self._ensure_current_bucket()
        
        if self.current_bucket:
            self.current_bucket.resource_usage[resource] = usage
            
            # Update baseline if needed
            if resource not in self.resource_baselines:
                self.resource_baselines[resource] = usage
            else:
                # Rolling average
                self.resource_baselines[resource] = (
                    0.9 * self.resource_baselines[resource] + 0.1 * usage
                )

    async def _check_anomalies(self, latency_ms: float, is_error: bool):
        """Check for metric anomalies"""
        # Calculate statistics over window
        latencies = []
        for bucket in self.buckets:
            latencies.extend(bucket.latencies)
            
        if latencies:
            avg = mean(latencies)
            std = stdev(latencies) if len(latencies) > 1 else 0
            
            # Check for latency anomaly
            if (latency_ms > avg + self.config.anomaly_threshold * std):
                await self._handle_anomaly('latency', latency_ms, avg, std)

    async def _handle_anomaly(self, metric_type: str, value: float, 
                            baseline: float, std: float):
        """Handle detected anomalies"""
        self.logger.warning(
            "Metric anomaly detected",
            metric_type=metric_type,
            value=value,
            baseline=baseline,
            std=std
        )
        
        # Record pattern
        pattern = {
            'type': metric_type,
            'value': value,
            'baseline': baseline,
            'std': std,
            'timestamp': datetime.utcnow()
        }
        self.pattern_history.append(pattern)

    async def _analyze_trip_patterns(self):
        """Analyze circuit breaker trip patterns"""
        trips = []
        for bucket in self.buckets:
            if bucket.circuit_trips > 0:
                trips.append({
                    'count': bucket.circuit_trips,
                    'timestamp': bucket.timestamp,
                    'error_rate': (bucket.error_count / bucket.request_count 
                                 if bucket.request_count > 0 else 0)
                })
                
        if trips:
            # Look for patterns in trip frequency
            await self._detect_trip_patterns(trips)

    async def _detect_trip_patterns(self, trips: List[Dict[str, Any]]):
        """Detect patterns in circuit breaker trips"""
        if len(trips) < 2:
            return
            
        # Calculate time differences between trips
        intervals = []
        for i in range(1, len(trips)):
            interval = (trips[i]['timestamp'] - 
                       trips[i-1]['timestamp']).total_seconds()
            intervals.append(interval)
            
        # Look for regular patterns
        if intervals:
            avg_interval = mean(intervals)
            std_interval = stdev(intervals) if len(intervals) > 1 else 0
            
            # Record if pattern is regular
            if std_interval < avg_interval * 0.2:  # 20% variation threshold
                pattern_key = f"regular_trips_{int(avg_interval)}"
                self.known_patterns[pattern_key] = {
                    'avg_interval': avg_interval,
                    'std_interval': std_interval,
                    'occurrences': len(trips)
                }

    async def _update_trends(self):
        """Update trend analysis data"""
        if not self.buckets:
            return
            
        # Calculate current metrics
        total_requests = sum(b.request_count for b in self.buckets)
        total_errors = sum(b.error_count for b in self.buckets)
        error_rate = total_errors / total_requests if total_requests > 0 else 0
        
        latencies = []
        for bucket in self.buckets:
            latencies.extend(bucket.latencies)
        avg_latency = mean(latencies) if latencies else 0
        
        # Update trend data
        self.trend_data['error_rates'].append(error_rate)
        self.trend_data['latencies'].append(avg_latency)
        self.trend_data['circuit_trips'].append(
            sum(b.circuit_trips for b in self.buckets)
        )

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics and analysis"""
        self._ensure_current_bucket()
        
        # Calculate window metrics
        total_requests = sum(b.request_count for b in self.buckets)
        total_errors = sum(b.error_count for b in self.buckets)
        total_trips = sum(b.circuit_trips for b in self.buckets)
        
        # Collect all latencies
        all_latencies = []
        for bucket in self.buckets:
            all_latencies.extend(bucket.latencies)
            
        # Calculate percentiles
        percentiles = {}
        if all_latencies:
            for p in self.config.percentiles:
                percentiles[f"p{p}"] = float(np.percentile(all_latencies, p))
                
        # Calculate trends
        trends = {}
        for metric, values in self.trend_data.items():
            if len(values) >= 2:
                trend = (values[-1] - values[0]) / len(values)
                trends[f"{metric}_trend"] = trend
                
        return {
            "window_size": self.config.window_size,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "circuit_trips": total_trips,
            "latency_percentiles": percentiles,
            "known_patterns": self.known_patterns,
            "trends": trends,
            "resource_usage": {
                resource: {
                    "current": self.current_bucket.resource_usage.get(resource, 0),
                    "baseline": self.resource_baselines.get(resource, 0)
                }
                for resource in self.resource_baselines
            }
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status based on metrics"""
        metrics = await self.get_metrics()
        
        # Define health thresholds
        thresholds = {
            "error_rate": 0.1,  # 10% error rate
            "latency_p95": 1000,  # 1 second
            "trip_rate": 0.1,  # 10% of window
        }
        
        # Calculate health scores
        health_scores = {
            "error_rate": 1.0 - (metrics["error_rate"] / thresholds["error_rate"]
                                if metrics["error_rate"] < thresholds["error_rate"]
                                else 0),
            "latency": 1.0 - (metrics["latency_percentiles"]["p95"] / 
                             thresholds["latency_p95"]
                             if metrics["latency_percentiles"].get("p95", 0) < 
                             thresholds["latency_p95"] else 0),
            "stability": 1.0 - (metrics["circuit_trips"] / 
                               (self.config.window_size * thresholds["trip_rate"])
                               if metrics["circuit_trips"] > 0 else 1.0)
        }
        
        # Calculate overall health
        overall_health = mean(health_scores.values())
        
        return {
            "overall_health": overall_health,
            "health_scores": health_scores,
            "status": "healthy" if overall_health >= 0.8 else
                     "degraded" if overall_health >= 0.5 else "unhealthy"
        } 