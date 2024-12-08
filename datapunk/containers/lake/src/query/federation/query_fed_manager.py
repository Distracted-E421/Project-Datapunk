from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .fed_visualization import QueryVisualization
from .fed_alerting import AlertManager
from .query_fed_monitoring import FederationMonitor
from .query_fed_core import FederationCore
from .fed_adapters import DataSourceAdapter
from .fed_merger import ResultMerger
from .fed_splitter import QuerySplitter
from ..optimizer.executor_bridge import OptimizerExecutorBridge, OptimizedPlan

@dataclass
class FederationMetrics:
    query_duration: float
    data_volume: int
    source_count: int
    error_count: int
    timestamp: datetime

class FederationManager:
    def __init__(
        self,
        optimizer_executor: OptimizerExecutorBridge,
        alert_threshold: float = 0.8
    ):
        self.optimizer_executor = optimizer_executor
        self.federation_core = FederationCore()
        self.visualizer = QueryVisualization()
        self.alert_manager = AlertManager(threshold=alert_threshold)
        self.monitor = FederationMonitor()
        self.merger = ResultMerger()
        self.splitter = QuerySplitter()
        self.adapters: Dict[str, DataSourceAdapter] = {}

    def register_data_source(self, source_id: str, adapter: DataSourceAdapter):
        """Register a new data source with the federation"""
        self.adapters[source_id] = adapter
        self.federation_core.register_source(source_id, adapter.get_capabilities())
        self.visualizer.add_data_source(source_id, adapter.get_metadata())

    def execute_federated_query(
        self,
        query: Any,
        visualization_required: bool = True,
        alert_on_threshold: bool = True
    ) -> Dict[str, Any]:
        """Execute a query across federated data sources with visualization and alerting"""
        start_time = datetime.now()
        
        try:
            # Split query into sub-queries for different data sources
            sub_queries = self.splitter.split_query(query, self.adapters.keys())
            
            # Create execution plans for each sub-query
            plans: Dict[str, OptimizedPlan] = {}
            for source_id, sub_query in sub_queries.items():
                plans[source_id] = self.optimizer_executor.create_execution_plan(sub_query)
            
            # Execute sub-queries and collect results
            results: Dict[str, Any] = {}
            errors: List[Dict[str, Any]] = []
            
            for source_id, plan in plans.items():
                try:
                    adapter = self.adapters[source_id]
                    transformed_query = adapter.transform_query(sub_queries[source_id])
                    result = self.optimizer_executor.execute_plan(transformed_query, plan)
                    results[source_id] = adapter.transform_result(result)
                except Exception as e:
                    errors.append({
                        "source_id": source_id,
                        "error": str(e),
                        "query": sub_queries[source_id]
                    })
            
            # Merge results
            merged_result = self.merger.merge_results(results)
            
            # Calculate metrics
            end_time = datetime.now()
            metrics = FederationMetrics(
                query_duration=(end_time - start_time).total_seconds(),
                data_volume=sum(len(str(r)) for r in results.values()),
                source_count=len(results),
                error_count=len(errors),
                timestamp=end_time
            )
            
            # Update monitoring
            self.monitor.record_execution(metrics)
            
            # Generate visualization if required
            visualization = None
            if visualization_required:
                visualization = self.visualizer.create_visualization(
                    query=query,
                    results=results,
                    metrics=metrics,
                    errors=errors
                )
            
            # Check alerts if enabled
            if alert_on_threshold:
                self._check_alerts(metrics, errors)
            
            return {
                "result": merged_result,
                "metrics": {
                    "duration": metrics.query_duration,
                    "data_volume": metrics.data_volume,
                    "source_count": metrics.source_count,
                    "error_count": metrics.error_count
                },
                "visualization": visualization,
                "errors": errors if errors else None
            }
            
        except Exception as e:
            self.alert_manager.send_alert(
                level="ERROR",
                message=f"Federation execution failed: {str(e)}",
                context={"query": query}
            )
            raise

    def _check_alerts(self, metrics: FederationMetrics, errors: List[Dict[str, Any]]):
        """Check and send alerts based on metrics and errors"""
        # Alert on high error rate
        if metrics.source_count > 0:
            error_rate = metrics.error_count / metrics.source_count
            if error_rate > self.alert_manager.threshold:
                self.alert_manager.send_alert(
                    level="WARNING",
                    message=f"High federation error rate: {error_rate:.2%}",
                    context={
                        "error_count": metrics.error_count,
                        "source_count": metrics.source_count,
                        "errors": errors
                    }
                )
        
        # Alert on long query duration
        if metrics.query_duration > 30:  # 30 seconds threshold
            self.alert_manager.send_alert(
                level="WARNING",
                message=f"Long-running federated query: {metrics.query_duration:.2f}s",
                context={"metrics": metrics.__dict__}
            )
        
        # Alert on large data volume
        data_volume_mb = metrics.data_volume / (1024 * 1024)
        if data_volume_mb > 100:  # 100MB threshold
            self.alert_manager.send_alert(
                level="INFO",
                message=f"Large data volume in federation: {data_volume_mb:.2f}MB",
                context={"metrics": metrics.__dict__}
            )

    def get_federation_status(self) -> Dict[str, Any]:
        """Get current status of the federation system"""
        return {
            "sources": {
                source_id: adapter.get_status()
                for source_id, adapter in self.adapters.items()
            },
            "metrics": self.monitor.get_recent_metrics(),
            "alerts": self.alert_manager.get_recent_alerts(),
            "visualization": self.visualizer.get_federation_overview()
        }

    def get_source_statistics(self, source_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific data source"""
        if source_id not in self.adapters:
            raise ValueError(f"Unknown data source: {source_id}")
            
        adapter = self.adapters[source_id]
        return {
            "metadata": adapter.get_metadata(),
            "capabilities": adapter.get_capabilities(),
            "metrics": self.monitor.get_source_metrics(source_id),
            "alerts": self.alert_manager.get_source_alerts(source_id),
            "visualization": self.visualizer.get_source_visualization(source_id)
        } 