from typing import Dict, Any, List, Optional, Set
import threading
import time
import logging
from datetime import datetime, timedelta
from .node import PartitionNode

class HealthStatus:
    """Represents health status of a node"""
    
    def __init__(self):
        self.last_check = datetime.now()
        self.status = 'unknown'  # unknown, healthy, degraded, unhealthy
        self.metrics: Dict[str, float] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.consecutive_failures = 0
        
class HealthMonitor:
    """Monitors health of nodes and cluster"""
    
    def __init__(self):
        self.node_status: Dict[str, HealthStatus] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self._stop_monitor = False
        self._monitor_thread = None
        self.alert_callbacks: List[callable] = []
        self.thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 80.0,
            'disk_usage': 80.0,
            'network_io': 90.0,
            'heartbeat_timeout': 30,  # seconds
            'max_consecutive_failures': 3
        }
        
    def start(self):
        """Start health monitoring"""
        self._stop_monitor = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_health,
            daemon=True
        )
        self._monitor_thread.start()
        
    def stop(self):
        """Stop health monitoring"""
        self._stop_monitor = True
        if self._monitor_thread:
            self._monitor_thread.join()
            
    def register_node(self, node: PartitionNode):
        """Register a node for health monitoring"""
        with self.lock:
            if node.node_id not in self.node_status:
                self.node_status[node.node_id] = HealthStatus()
                
    def deregister_node(self, node: PartitionNode):
        """Remove a node from health monitoring"""
        with self.lock:
            if node.node_id in self.node_status:
                del self.node_status[node.node_id]
                
    def update_node_metrics(self, node_id: str,
                          metrics: Dict[str, float]):
        """Update metrics for a node"""
        with self.lock:
            status = self.node_status.get(node_id)
            if status:
                status.metrics.update(metrics)
                status.last_check = datetime.now()
                self._evaluate_node_health(node_id, status)
                
    def get_node_health(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get health status for a node"""
        with self.lock:
            status = self.node_status.get(node_id)
            if not status:
                return None
                
            return {
                'status': status.status,
                'last_check': status.last_check,
                'metrics': status.metrics.copy(),
                'alerts': status.alerts.copy(),
                'consecutive_failures': status.consecutive_failures
            }
            
    def register_alert_callback(self, callback: callable):
        """Register callback for health alerts"""
        self.alert_callbacks.append(callback)
        
    def update_thresholds(self, thresholds: Dict[str, float]):
        """Update monitoring thresholds"""
        with self.lock:
            self.thresholds.update(thresholds)
            
    def _monitor_health(self):
        """Main health monitoring loop"""
        while not self._stop_monitor:
            try:
                self._check_all_nodes()
                self._cleanup_old_alerts()
            except Exception as e:
                self.logger.error(f"Health monitor error: {str(e)}")
                
            # Sleep for monitoring interval
            time.sleep(10)  # 10 second interval
            
    def _check_all_nodes(self):
        """Check health of all registered nodes"""
        with self.lock:
            now = datetime.now()
            for node_id, status in self.node_status.items():
                # Check heartbeat
                if (now - status.last_check).total_seconds() > self.thresholds['heartbeat_timeout']:
                    self._handle_node_failure(node_id, status, "Heartbeat timeout")
                    continue
                    
                # Evaluate metrics
                self._evaluate_node_health(node_id, status)
                
    def _evaluate_node_health(self, node_id: str,
                            status: HealthStatus):
        """Evaluate health based on metrics"""
        alerts = []
        
        # Check each metric against thresholds
        for metric, value in status.metrics.items():
            if metric in self.thresholds and value > self.thresholds[metric]:
                alerts.append({
                    'type': 'threshold_exceeded',
                    'metric': metric,
                    'value': value,
                    'threshold': self.thresholds[metric],
                    'timestamp': datetime.now()
                })
                
        # Update status based on alerts
        if not alerts:
            status.status = 'healthy'
            status.consecutive_failures = 0
        else:
            status.status = 'degraded' if len(alerts) < 2 else 'unhealthy'
            status.consecutive_failures += 1
            
            # Add new alerts
            status.alerts.extend(alerts)
            
            # Notify callbacks
            self._notify_alerts(node_id, alerts)
            
        # Check for consecutive failures
        if status.consecutive_failures >= self.thresholds['max_consecutive_failures']:
            self._handle_node_failure(node_id, status, "Max consecutive failures exceeded")
            
    def _handle_node_failure(self, node_id: str,
                           status: HealthStatus,
                           reason: str):
        """Handle a node failure"""
        status.status = 'unhealthy'
        alert = {
            'type': 'node_failure',
            'reason': reason,
            'timestamp': datetime.now()
        }
        status.alerts.append(alert)
        self._notify_alerts(node_id, [alert])
        
    def _notify_alerts(self, node_id: str,
                      alerts: List[Dict[str, Any]]):
        """Notify alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(node_id, alerts)
            except Exception as e:
                self.logger.error(f"Alert callback error: {str(e)}")
                
    def _cleanup_old_alerts(self):
        """Clean up old alerts"""
        with self.lock:
            now = datetime.now()
            max_age = timedelta(hours=24)
            
            for status in self.node_status.values():
                status.alerts = [
                    alert for alert in status.alerts
                    if now - alert['timestamp'] <= max_age
                ]
                
    def get_cluster_health(self) -> Dict[str, Any]:
        """Get overall cluster health status"""
        with self.lock:
            total_nodes = len(self.node_status)
            if not total_nodes:
                return {
                    'status': 'unknown',
                    'healthy_nodes': 0,
                    'total_nodes': 0
                }
                
            node_counts = {
                'healthy': 0,
                'degraded': 0,
                'unhealthy': 0,
                'unknown': 0
            }
            
            for status in self.node_status.values():
                node_counts[status.status] += 1
                
            # Determine overall status
            if node_counts['unhealthy'] > total_nodes * 0.2:  # More than 20% unhealthy
                cluster_status = 'unhealthy'
            elif node_counts['degraded'] > total_nodes * 0.3:  # More than 30% degraded
                cluster_status = 'degraded'
            elif node_counts['healthy'] > total_nodes * 0.8:  # More than 80% healthy
                cluster_status = 'healthy'
            else:
                cluster_status = 'degraded'
                
            return {
                'status': cluster_status,
                'node_counts': node_counts,
                'total_nodes': total_nodes,
                'healthy_percentage': (node_counts['healthy'] / total_nodes) * 100
            }
            
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts across all nodes"""
        with self.lock:
            now = datetime.now()
            max_age = timedelta(hours=hours)
            
            all_alerts = []
            for node_id, status in self.node_status.items():
                for alert in status.alerts:
                    if now - alert['timestamp'] <= max_age:
                        alert_copy = alert.copy()
                        alert_copy['node_id'] = node_id
                        all_alerts.append(alert_copy)
                        
            # Sort by timestamp
            return sorted(
                all_alerts,
                key=lambda x: x['timestamp'],
                reverse=True
            )
            
    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of metrics across all nodes"""
        with self.lock:
            metrics_sum = {}
            node_count = len(self.node_status)
            
            if not node_count:
                return {}
                
            # Calculate averages
            for status in self.node_status.values():
                for metric, value in status.metrics.items():
                    if metric not in metrics_sum:
                        metrics_sum[metric] = {
                            'min': float('inf'),
                            'max': float('-inf'),
                            'sum': 0.0,
                            'count': 0
                        }
                    metrics_sum[metric]['min'] = min(
                        metrics_sum[metric]['min'],
                        value
                    )
                    metrics_sum[metric]['max'] = max(
                        metrics_sum[metric]['max'],
                        value
                    )
                    metrics_sum[metric]['sum'] += value
                    metrics_sum[metric]['count'] += 1
                    
            # Calculate final statistics
            return {
                metric: {
                    'min': stats['min'],
                    'max': stats['max'],
                    'avg': stats['sum'] / stats['count']
                }
                for metric, stats in metrics_sum.items()
            } 