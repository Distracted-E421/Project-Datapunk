import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import json
from collections import defaultdict
import numpy as np
from enum import Enum

class PatternType(Enum):
    PERIODIC = "periodic"
    BURST = "burst"
    GRADUAL_INCREASE = "gradual_increase"
    GRADUAL_DECREASE = "gradual_decrease"
    ANOMALY = "anomaly"

@dataclass
class ServiceMetric:
    service_name: str
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Optional[Dict] = None

@dataclass
class Pattern:
    pattern_type: PatternType
    confidence: float
    start_time: datetime
    end_time: datetime
    affected_services: Set[str]
    description: str
    metadata: Optional[Dict] = None

class PatternAnalyzer:
    def __init__(self, 
                 window_size: timedelta = timedelta(hours=1),
                 min_confidence: float = 0.8,
                 anomaly_threshold: float = 2.0):
        self.window_size = window_size
        self.min_confidence = min_confidence
        self.anomaly_threshold = anomaly_threshold
        self.metrics_history: List[ServiceMetric] = []
        self.detected_patterns: List[Pattern] = []
        self.logger = logging.getLogger(__name__)

    def add_metric(self, metric: ServiceMetric) -> None:
        """Add a new metric to the analyzer."""
        self.metrics_history.append(metric)
        self._cleanup_old_metrics()
        self._analyze_new_metric(metric)

    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than the window size."""
        cutoff_time = datetime.now() - self.window_size
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]

    def _analyze_new_metric(self, metric: ServiceMetric) -> None:
        """Analyze a new metric for patterns."""
        self._detect_periodic_patterns()
        self._detect_burst_patterns()
        self._detect_gradual_changes()
        self._detect_anomalies()

    def _detect_periodic_patterns(self) -> None:
        """Detect periodic patterns in metrics."""
        # Group metrics by service and metric name
        grouped_metrics = self._group_metrics()
        
        for (service, metric_name), metrics in grouped_metrics.items():
            if len(metrics) < 10:  # Need enough data points
                continue

            # Extract timestamps and values
            timestamps = np.array([m.timestamp.timestamp() for m in metrics])
            values = np.array([m.value for m in metrics])

            # Perform FFT to detect periodicity
            fft = np.fft.fft(values)
            frequencies = np.fft.fftfreq(len(timestamps))
            main_freq_idx = np.argmax(np.abs(fft))
            
            if np.abs(fft[main_freq_idx]) > len(values) * 0.5:
                period = 1 / frequencies[main_freq_idx]
                if period > 0:  # Valid period found
                    self._record_pattern(
                        PatternType.PERIODIC,
                        0.85,
                        metrics[0].timestamp,
                        metrics[-1].timestamp,
                        {service},
                        f"Periodic pattern detected in {service}.{metric_name} with period {period:.2f}s"
                    )

    def _detect_burst_patterns(self) -> None:
        """Detect burst patterns in metrics."""
        grouped_metrics = self._group_metrics()
        
        for (service, metric_name), metrics in grouped_metrics.items():
            if len(metrics) < 5:
                continue

            values = [m.value for m in metrics]
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            # Look for sudden spikes
            for i in range(len(values) - 4):
                window = values[i:i+5]
                if np.mean(window) > mean_val + (2 * std_val):
                    self._record_pattern(
                        PatternType.BURST,
                        0.9,
                        metrics[i].timestamp,
                        metrics[i+4].timestamp,
                        {service},
                        f"Burst pattern detected in {service}.{metric_name}"
                    )

    def _detect_gradual_changes(self) -> None:
        """Detect gradual increases or decreases in metrics."""
        grouped_metrics = self._group_metrics()
        
        for (service, metric_name), metrics in grouped_metrics.items():
            if len(metrics) < 10:
                continue

            values = np.array([m.value for m in metrics])
            timestamps = np.array([m.timestamp.timestamp() for m in metrics])
            
            # Calculate linear regression
            z = np.polyfit(timestamps, values, 1)
            slope = z[0]
            
            if abs(slope) > 0.1:  # Significant change
                pattern_type = (
                    PatternType.GRADUAL_INCREASE if slope > 0 
                    else PatternType.GRADUAL_DECREASE
                )
                
                self._record_pattern(
                    pattern_type,
                    0.85,
                    metrics[0].timestamp,
                    metrics[-1].timestamp,
                    {service},
                    f"Gradual {'increase' if slope > 0 else 'decrease'} detected in {service}.{metric_name}"
                )

    def _detect_anomalies(self) -> None:
        """Detect anomalous behavior in metrics."""
        grouped_metrics = self._group_metrics()
        
        for (service, metric_name), metrics in grouped_metrics.items():
            if len(metrics) < 10:
                continue

            values = np.array([m.value for m in metrics])
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            # Detect values outside normal range
            for i, metric in enumerate(metrics):
                if abs(metric.value - mean_val) > (self.anomaly_threshold * std_val):
                    self._record_pattern(
                        PatternType.ANOMALY,
                        0.95,
                        metric.timestamp,
                        metric.timestamp + timedelta(minutes=1),
                        {service},
                        f"Anomaly detected in {service}.{metric_name}"
                    )

    def _group_metrics(self) -> Dict[tuple, List[ServiceMetric]]:
        """Group metrics by service and metric name."""
        grouped = defaultdict(list)
        for metric in self.metrics_history:
            key = (metric.service_name, metric.metric_name)
            grouped[key].append(metric)
        return grouped

    def _record_pattern(self, 
                       pattern_type: PatternType,
                       confidence: float,
                       start_time: datetime,
                       end_time: datetime,
                       affected_services: Set[str],
                       description: str,
                       metadata: Optional[Dict] = None) -> None:
        """Record a detected pattern."""
        if confidence >= self.min_confidence:
            pattern = Pattern(
                pattern_type=pattern_type,
                confidence=confidence,
                start_time=start_time,
                end_time=end_time,
                affected_services=affected_services,
                description=description,
                metadata=metadata
            )
            self.detected_patterns.append(pattern)
            self.logger.info(f"New pattern detected: {description}")

    def get_recent_patterns(self, 
                          pattern_type: Optional[PatternType] = None,
                          service: Optional[str] = None) -> List[Pattern]:
        """Get recently detected patterns with optional filtering."""
        patterns = self.detected_patterns
        
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
            
        if service:
            patterns = [p for p in patterns if service in p.affected_services]
            
        return sorted(patterns, key=lambda x: x.end_time, reverse=True)

    def get_pattern_summary(self) -> Dict:
        """Get a summary of detected patterns."""
        summary = defaultdict(int)
        for pattern in self.detected_patterns:
            summary[pattern.pattern_type.value] += 1
            
        return {
            'total_patterns': len(self.detected_patterns),
            'pattern_types': dict(summary),
            'unique_services': len({
                service 
                for pattern in self.detected_patterns 
                for service in pattern.affected_services
            })
        }

    def export_patterns(self, file_path: str) -> None:
        """Export detected patterns to a JSON file."""
        patterns_data = [
            {
                'type': p.pattern_type.value,
                'confidence': p.confidence,
                'start_time': p.start_time.isoformat(),
                'end_time': p.end_time.isoformat(),
                'affected_services': list(p.affected_services),
                'description': p.description,
                'metadata': p.metadata
            }
            for p in self.detected_patterns
        ]
        
        with open(file_path, 'w') as f:
            json.dump(patterns_data, f, indent=2) 