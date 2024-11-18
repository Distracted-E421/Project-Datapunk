from typing import Dict, Any, Optional
import prometheus_client as prom
from datetime import datetime

class MetricsCollector:
    def __init__(self):
        # Initialize Prometheus metrics
        self.inference_latency = prom.Histogram(
            'inference_latency_seconds',
            'Model inference latency in seconds',
            ['model_name', 'pipeline_type']
        )
        
        self.model_accuracy = prom.Gauge(
            'model_accuracy',
            'Model prediction accuracy',
            ['model_name']
        )
        
        self.resource_usage = prom.Gauge(
            'resource_usage',
            'Resource utilization',
            ['resource_type']
        )
        
        self.error_counter = prom.Counter(
            'inference_errors_total',
            'Total number of inference errors',
            ['error_type']
        )

    async def record_inference(
        self, 
        model_name: str, 
        pipeline_type: str,
        start_time: datetime,
        end_time: datetime,
        error: Optional[str] = None
    ):
        """Record inference metrics"""
        duration = (end_time - start_time).total_seconds()
        self.inference_latency.labels(
            model_name=model_name,
            pipeline_type=pipeline_type
        ).observe(duration)
        
        if error:
            self.error_counter.labels(error_type=error).inc()