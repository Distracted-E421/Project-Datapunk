from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json
from .planner import DataSource, SubQuery
from .executor import QueryResult
from ..executor.monitoring import MetricsCollector

@dataclass
class FederationMetrics:
    """Metrics for federation operations."""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    data_transfer_bytes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    source_metrics: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        if self.source_metrics is None:
            self.source_metrics = {}

@dataclass
class QueryMetrics:
    """Metrics for a single federated query."""
    query_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    error: Optional[str] = None
    sub_queries: List[Dict[str, Any]] = None
    data_sources: List[str] = None
    rows_processed: int = 0
    bytes_transferred: int = 0

    def __post_init__(self):
        if self.sub_queries is None:
            self.sub_queries = []
        if self.data_sources is None:
            self.data_sources = []

class FederationMonitor:
    """Monitors and collects metrics for federated queries."""
    
    def __init__(self):
        self.metrics = FederationMetrics()
        self.active_queries: Dict[str, QueryMetrics] = {}
        self.completed_queries: List[QueryMetrics] = []
        self.logger = logging.getLogger(__name__)
        self.metrics_collector = MetricsCollector()
        
    def start_query(self, query_id: str, data_sources: List[DataSource]) -> None:
        """Record the start of a federated query."""
        self.active_queries[query_id] = QueryMetrics(
            query_id=query_id,
            start_time=datetime.now(),
            data_sources=[ds.name for ds in data_sources]
        )
        self.metrics.total_queries += 1
        
    def record_sub_query(self, query_id: str, sub_query: SubQuery) -> None:
        """Record execution of a sub-query."""
        if query_id in self.active_queries:
            self.active_queries[query_id].sub_queries.append({
                "source": sub_query.source.name,
                "estimated_cost": sub_query.estimated_cost,
                "start_time": datetime.now().isoformat()
            })
            
    def record_sub_query_completion(self, query_id: str, source_name: str,
                                  result: QueryResult) -> None:
        """Record completion of a sub-query."""
        if query_id in self.active_queries:
            query_metrics = self.active_queries[query_id]
            for sub_query in query_metrics.sub_queries:
                if sub_query["source"] == source_name and "end_time" not in sub_query:
                    sub_query["end_time"] = datetime.now().isoformat()
                    sub_query["rows"] = len(result.data)
                    sub_query["bytes"] = len(json.dumps(result.data).encode())
                    query_metrics.rows_processed += sub_query["rows"]
                    query_metrics.bytes_transferred += sub_query["bytes"]
                    break
                    
    def complete_query(self, query_id: str, error: Optional[str] = None) -> None:
        """Record completion of a federated query."""
        if query_id in self.active_queries:
            query_metrics = self.active_queries[query_id]
            query_metrics.end_time = datetime.now()
            query_metrics.status = "failed" if error else "completed"
            query_metrics.error = error
            
            # Update global metrics
            execution_time = (query_metrics.end_time - query_metrics.start_time).total_seconds()
            self.metrics.total_execution_time += execution_time
            self.metrics.avg_execution_time = (
                self.metrics.total_execution_time / self.metrics.total_queries
            )
            
            if error:
                self.metrics.failed_queries += 1
            else:
                self.metrics.successful_queries += 1
                
            self.metrics.data_transfer_bytes += query_metrics.bytes_transferred
            
            # Move to completed queries
            self.completed_queries.append(query_metrics)
            del self.active_queries[query_id]
            
    def record_cache_operation(self, hit: bool) -> None:
        """Record cache hit or miss."""
        if hit:
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1
            
    def update_source_metrics(self, source_name: str, metrics: Dict[str, Any]) -> None:
        """Update metrics for a data source."""
        self.metrics.source_metrics[source_name] = metrics
        
    def get_active_queries(self) -> List[Dict[str, Any]]:
        """Get information about currently executing queries."""
        return [
            {
                "query_id": qid,
                "runtime": (datetime.now() - metrics.start_time).total_seconds(),
                "sources": metrics.data_sources,
                "sub_queries": metrics.sub_queries
            }
            for qid, metrics in self.active_queries.items()
        ]
        
    def get_query_history(self, 
                         hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get historical query information."""
        cutoff = datetime.now() - timedelta(hours=hours) if hours else None
        
        history = []
        for metrics in self.completed_queries:
            if not cutoff or metrics.start_time >= cutoff:
                history.append({
                    "query_id": metrics.query_id,
                    "status": metrics.status,
                    "start_time": metrics.start_time.isoformat(),
                    "end_time": metrics.end_time.isoformat(),
                    "runtime": (metrics.end_time - metrics.start_time).total_seconds(),
                    "sources": metrics.data_sources,
                    "rows": metrics.rows_processed,
                    "bytes": metrics.bytes_transferred,
                    "error": metrics.error
                })
        return history
        
    def get_source_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics by data source."""
        performance = {}
        for metrics in self.completed_queries:
            for sub_query in metrics.sub_queries:
                source = sub_query["source"]
                if source not in performance:
                    performance[source] = {
                        "queries": 0,
                        "total_rows": 0,
                        "total_bytes": 0,
                        "total_time": 0.0
                    }
                    
                performance[source]["queries"] += 1
                performance[source]["total_rows"] += sub_query.get("rows", 0)
                performance[source]["total_bytes"] += sub_query.get("bytes", 0)
                
                if "start_time" in sub_query and "end_time" in sub_query:
                    start = datetime.fromisoformat(sub_query["start_time"])
                    end = datetime.fromisoformat(sub_query["end_time"])
                    performance[source]["total_time"] += (end - start).total_seconds()
                    
        # Calculate averages
        for source_metrics in performance.values():
            queries = source_metrics["queries"]
            if queries > 0:
                source_metrics["avg_rows"] = source_metrics["total_rows"] / queries
                source_metrics["avg_bytes"] = source_metrics["total_bytes"] / queries
                source_metrics["avg_time"] = source_metrics["total_time"] / queries
                
        return performance
        
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for the federation layer."""
        return {
            "total_queries": self.metrics.total_queries,
            "successful_queries": self.metrics.successful_queries,
            "failed_queries": self.metrics.failed_queries,
            "avg_execution_time": self.metrics.avg_execution_time,
            "total_data_transfer_mb": self.metrics.data_transfer_bytes / (1024 * 1024),
            "cache_hit_ratio": (
                self.metrics.cache_hits / 
                (self.metrics.cache_hits + self.metrics.cache_misses)
                if (self.metrics.cache_hits + self.metrics.cache_misses) > 0
                else 0
            ),
            "active_queries": len(self.active_queries)
        }