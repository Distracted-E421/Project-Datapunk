from typing import Dict, Any
import structlog
from prometheus_client import Counter, Gauge, Histogram
from datetime import datetime

logger = structlog.get_logger()

class HealthAwareMetrics:
    """Metrics for health-aware load balancing."""
    
    def __init__(self):
        # Health Scores
        self.instance_health = Gauge(
            'load_balancer_instance_health_score',
            'Current health score of service instance',
            ['service', 'instance']
        )
        
        self.service_health = Gauge(
            'load_balancer_service_health_score',
            'Aggregate health score of service',
            ['service']
        )
        
        # Selection Metrics
        self.health_based_selections = Counter(
            'load_balancer_health_based_selections_total',
            'Number of health-based instance selections',
            ['service', 'strategy', 'health_range']
        )
        
        self.health_rejections = Counter(
            'load_balancer_health_rejections_total',
            'Number of instances rejected due to health',
            ['service', 'reason']
        )
        
        # Recovery Metrics
        self.recovery_attempts = Counter(
            'load_balancer_recovery_attempts_total',
            'Number of instance recovery attempts',
            ['service', 'instance']
        )
        
        self.recovery_success = Counter(
            'load_balancer_recovery_success_total',
            'Number of successful instance recoveries',
            ['service', 'instance']
        )
        
        # Circuit Breaker Metrics
        self.circuit_breaks = Counter(
            'load_balancer_circuit_breaks_total',
            'Number of circuit breaker activations',
            ['service', 'instance']
        )
        
        self.circuit_state = Gauge(
            'load_balancer_circuit_state',
            'Circuit breaker state (0=open, 1=half-open, 2=closed)',
            ['service', 'instance']
        )
        
        # Performance Impact
        self.health_check_duration = Histogram(
            'load_balancer_health_check_duration_seconds',
            'Duration of health checks',
            ['service', 'check_type']
        )
        
        self.balancing_latency = Histogram(
            'load_balancer_selection_latency_seconds',
            'Time taken to select instance',
            ['service', 'strategy']
        )
    
    def record_health_score(self,
                          service: str,
                          instance: str,
                          score: float):
        """Record instance health score."""
        self.instance_health.labels(
            service=service,
            instance=instance
        ).set(score)
    
    def record_service_health(self,
                            service: str,
                            score: float):
        """Record aggregate service health."""
        self.service_health.labels(
            service=service
        ).set(score)
    
    def record_selection(self,
                        service: str,
                        strategy: str,
                        health_score: float):
        """Record health-based selection."""
        health_range = "high" if health_score > 0.8 else \
                      "medium" if health_score > 0.5 else "low"
        
        self.health_based_selections.labels(
            service=service,
            strategy=strategy,
            health_range=health_range
        ).inc()
    
    def record_rejection(self,
                        service: str,
                        reason: str):
        """Record instance rejection."""
        self.health_rejections.labels(
            service=service,
            reason=reason
        ).inc()
    
    def record_recovery(self,
                       service: str,
                       instance: str,
                       success: bool):
        """Record recovery attempt."""
        self.recovery_attempts.labels(
            service=service,
            instance=instance
        ).inc()
        
        if success:
            self.recovery_success.labels(
                service=service,
                instance=instance
            ).inc()
    
    def record_circuit_break(self,
                           service: str,
                           instance: str,
                           state: str):
        """Record circuit breaker state change."""
        state_value = {
            "open": 0,
            "half-open": 1,
            "closed": 2
        }.get(state, 0)
        
        self.circuit_breaks.labels(
            service=service,
            instance=instance
        ).inc()
        
        self.circuit_state.labels(
            service=service,
            instance=instance
        ).set(state_value)
    
    def observe_health_check(self,
                           service: str,
                           check_type: str,
                           duration: float):
        """Record health check duration."""
        self.health_check_duration.labels(
            service=service,
            check_type=check_type
        ).observe(duration)
    
    def observe_selection_latency(self,
                                service: str,
                                strategy: str,
                                duration: float):
        """Record instance selection latency."""
        self.balancing_latency.labels(
            service=service,
            strategy=strategy
        ).observe(duration) 