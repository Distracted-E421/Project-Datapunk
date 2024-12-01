from typing import Any, Dict, List, Set, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from elasticsearch import Elasticsearch
from .adapters import DataSourceAdapter, AdapterMetrics
from .core import DataSourceStats
from ..parser.core import QueryPlan, QueryNode

@dataclass
class AdapterCapabilities:
    """Capabilities of a data source adapter."""
    operations: Set[str]  # Supported operations
    functions: Set[str]  # Supported functions
    data_types: Set[str]  # Supported data types
    max_concurrent_queries: int
    supports_transactions: bool
    supports_streaming: bool
    supports_pushdown: bool
    max_result_size: int  # bytes

class EnhancedAdapter(DataSourceAdapter):
    """Base class for enhanced data source adapters."""
    
    def __init__(self, name: str, capabilities: AdapterCapabilities):
        super().__init__(name)
        self.capabilities = capabilities
        self.metrics = AdapterMetrics()
        self.logger = logging.getLogger(__name__)
        self._active_queries: Dict[str, asyncio.Task] = {}
        self._query_semaphore = asyncio.Semaphore(
            capabilities.max_concurrent_queries
        )
    
    async def execute_query(self,
                          query: QueryPlan,
                          timeout_ms: Optional[int] = None) -> Any:
        """Execute query with enhanced features."""
        query_id = self._generate_query_id()
        
        try:
            # Check capabilities
            self._validate_query(query)
            
            # Apply query optimizations
            optimized_query = await self._optimize_query(query)
            
            # Execute with resource management
            async with self._query_semaphore:
                task = asyncio.create_task(
                    self._execute_with_monitoring(
                        query_id,
                        optimized_query,
                        timeout_ms
                    )
                )
                self._active_queries[query_id] = task
                
                try:
                    result = await task
                    return result
                finally:
                    del self._active_queries[query_id]
        except Exception as e:
            self.logger.error(f"Error executing query {query_id}: {e}")
            raise
    
    async def cancel_query(self, query_id: str) -> None:
        """Cancel an active query."""
        if query_id in self._active_queries:
            self._active_queries[query_id].cancel()
            await self._cleanup_query(query_id)
    
    async def get_active_queries(self) -> List[Dict[str, Any]]:
        """Get information about active queries."""
        return [
            {
                'query_id': qid,
                'start_time': task.get_start_time(),
                'elapsed_ms': task.get_elapsed_ms()
            }
            for qid, task in self._active_queries.items()
        ]
    
    def _validate_query(self, query: QueryPlan) -> None:
        """Validate query against adapter capabilities."""
        def validate_node(node: Any) -> None:
            if hasattr(node, 'operation_type'):
                if node.operation_type.lower() not in self.capabilities.operations:
                    raise ValueError(
                        f"Operation not supported: {node.operation_type}"
                    )
            
            if hasattr(node, 'functions'):
                for func in node.functions:
                    if func.lower() not in self.capabilities.functions:
                        raise ValueError(f"Function not supported: {func}")
            
            if hasattr(node, 'data_type'):
                if node.data_type.lower() not in self.capabilities.data_types:
                    raise ValueError(f"Data type not supported: {node.data_type}")
            
            if hasattr(node, 'children'):
                for child in node.children:
                    validate_node(child)
        
        validate_node(query.root)
    
    async def _optimize_query(self, query: QueryPlan) -> QueryPlan:
        """Apply source-specific optimizations."""
        # Base implementation - override in specific adapters
        return query
    
    async def _execute_with_monitoring(self,
                                     query_id: str,
                                     query: QueryPlan,
                                     timeout_ms: Optional[int]) -> Any:
        """Execute query with monitoring and resource management."""
        start_time = datetime.utcnow()
        
        try:
            # Set up monitoring
            monitor_task = asyncio.create_task(
                self._monitor_execution(query_id, start_time)
            )
            
            # Execute query with timeout
            if timeout_ms:
                result = await asyncio.wait_for(
                    self._execute_query_internal(query),
                    timeout_ms / 1000
                )
            else:
                result = await self._execute_query_internal(query)
            
            # Update metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.metrics.update_execution_time(execution_time)
            
            return result
        except asyncio.TimeoutError:
            self.metrics.record_timeout()
            raise
        except Exception as e:
            self.metrics.record_error()
            raise
        finally:
            monitor_task.cancel()
            await self._cleanup_query(query_id)
    
    async def _monitor_execution(self,
                               query_id: str,
                               start_time: datetime) -> None:
        """Monitor query execution."""
        try:
            while True:
                # Get execution statistics
                stats = await self._get_query_stats(query_id)
                
                # Check resource usage
                if stats.get('memory_usage', 0) > self.capabilities.max_result_size:
                    await self.cancel_query(query_id)
                    raise MemoryError("Query exceeded memory limit")
                
                # Log progress
                self.logger.debug(
                    f"Query {query_id} progress: {stats.get('progress', 0)}%"
                )
                
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    async def _cleanup_query(self, query_id: str) -> None:
        """Clean up resources after query execution."""
        # Implementation depends on source type
        pass
    
    async def _get_query_stats(self, query_id: str) -> Dict[str, Any]:
        """Get statistics for an active query."""
        # Implementation depends on source type
        pass
    
    def _generate_query_id(self) -> str:
        """Generate unique query ID."""
        # Implementation depends on requirements
        pass

class StreamingAdapter(EnhancedAdapter):
    """Adapter for streaming data sources."""
    
    def __init__(self,
                 name: str,
                 capabilities: AdapterCapabilities,
                 batch_size: int = 1000):
        super().__init__(name, capabilities)
        self.batch_size = batch_size
        self._streams: Dict[str, asyncio.Queue] = {}
    
    async def execute_query(self,
                          query: QueryPlan,
                          timeout_ms: Optional[int] = None) -> Any:
        """Execute streaming query."""
        stream_id = self._generate_stream_id()
        
        try:
            # Create stream queue
            queue = asyncio.Queue(maxsize=self.batch_size)
            self._streams[stream_id] = queue
            
            # Start stream processing
            process_task = asyncio.create_task(
                self._process_stream(stream_id, query)
            )
            
            # Return stream interface
            return StreamInterface(
                stream_id=stream_id,
                queue=queue,
                cleanup=lambda: self._cleanup_stream(stream_id)
            )
        except Exception as e:
            self.logger.error(f"Error starting stream {stream_id}: {e}")
            await self._cleanup_stream(stream_id)
            raise
    
    async def _process_stream(self, stream_id: str, query: QueryPlan) -> None:
        """Process streaming query."""
        try:
            queue = self._streams[stream_id]
            
            async for batch in self._get_stream_data(query):
                await queue.put(batch)
                
            # Signal end of stream
            await queue.put(None)
        except Exception as e:
            self.logger.error(f"Error processing stream {stream_id}: {e}")
            raise
        finally:
            await self._cleanup_stream(stream_id)
    
    async def _cleanup_stream(self, stream_id: str) -> None:
        """Clean up stream resources."""
        if stream_id in self._streams:
            await self._streams[stream_id].put(None)
            del self._streams[stream_id]
    
    async def _get_stream_data(self, query: QueryPlan) -> Any:
        """Get data from streaming source."""
        # Implementation depends on source type
        pass
    
    def _generate_stream_id(self) -> str:
        """Generate unique stream ID."""
        # Implementation depends on requirements
        pass

class BatchAdapter(EnhancedAdapter):
    """Adapter for batch processing sources."""
    
    def __init__(self,
                 name: str,
                 capabilities: AdapterCapabilities,
                 max_batch_size: int = 10000):
        super().__init__(name, capabilities)
        self.max_batch_size = max_batch_size
    
    async def execute_query(self,
                          query: QueryPlan,
                          timeout_ms: Optional[int] = None) -> Any:
        """Execute batch query."""
        # Split query into batches
        batches = self._create_batches(query)
        
        results = []
        for batch in batches:
            # Execute batch with parent's implementation
            batch_result = await super().execute_query(batch, timeout_ms)
            results.append(batch_result)
        
        # Combine batch results
        return self._combine_results(results)
    
    def _create_batches(self, query: QueryPlan) -> List[QueryPlan]:
        """Split query into batches."""
        # Implementation depends on query type
        pass
    
    def _combine_results(self, results: List[Any]) -> Any:
        """Combine results from multiple batches."""
        # Implementation depends on result type
        pass

class CachingAdapter(EnhancedAdapter):
    """Adapter with query result caching."""
    
    def __init__(self,
                 name: str,
                 capabilities: AdapterCapabilities,
                 cache_size_mb: int = 1024):
        super().__init__(name, capabilities)
        self.cache_size_bytes = cache_size_mb * 1024 * 1024
        self._cache: Dict[str, Any] = {}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def execute_query(self,
                          query: QueryPlan,
                          timeout_ms: Optional[int] = None) -> Any:
        """Execute query with caching."""
        cache_key = self._generate_cache_key(query)
        
        # Check cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute query
        result = await super().execute_query(query, timeout_ms)
        
        # Cache result if appropriate
        if self._should_cache(query, result):
            self._add_to_cache(cache_key, result)
        
        return result
    
    def _generate_cache_key(self, query: QueryPlan) -> str:
        """Generate cache key for query."""
        # Implementation depends on query structure
        pass
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get result from cache."""
        if key in self._cache:
            metadata = self._cache_metadata[key]
            if not self._is_expired(metadata):
                return self._cache[key]
            else:
                self._remove_from_cache(key)
        return None
    
    def _add_to_cache(self, key: str, value: Any) -> None:
        """Add result to cache."""
        # Check cache size
        while self._get_cache_size() + self._estimate_size(value) > self.cache_size_bytes:
            self._evict_one()
        
        self._cache[key] = value
        self._cache_metadata[key] = {
            'added_time': datetime.utcnow(),
            'size_bytes': self._estimate_size(value),
            'access_count': 0
        }
    
    def _remove_from_cache(self, key: str) -> None:
        """Remove item from cache."""
        if key in self._cache:
            del self._cache[key]
            del self._cache_metadata[key]
    
    def _should_cache(self, query: QueryPlan, result: Any) -> bool:
        """Determine if result should be cached."""
        # Implementation depends on caching strategy
        pass
    
    def _is_expired(self, metadata: Dict[str, Any]) -> bool:
        """Check if cached item is expired."""
        # Implementation depends on caching strategy
        pass
    
    def _get_cache_size(self) -> int:
        """Get total size of cached items."""
        return sum(
            metadata['size_bytes']
            for metadata in self._cache_metadata.values()
        )
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        # Implementation depends on value type
        pass
    
    def _evict_one(self) -> None:
        """Evict one item from cache."""
        if not self._cache:
            return
        
        # Find item to evict
        scores = {
            key: self._calculate_eviction_score(metadata)
            for key, metadata in self._cache_metadata.items()
        }
        
        key_to_evict = min(scores.items(), key=lambda x: x[1])[0]
        self._remove_from_cache(key_to_evict)
    
    def _calculate_eviction_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate score for cache eviction."""
        # Implementation depends on eviction strategy
        pass

class PostgreSQLAdapter(DataSourceAdapter):
    """Adapter for PostgreSQL databases."""
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.conn_params = connection_params
        self.connection = psycopg2.connect(**connection_params)
        
    def get_capabilities(self) -> Set[str]:
        """Get PostgreSQL capabilities."""
        return {
            'select', 'project', 'filter', 'join',
            'group', 'sort', 'limit', 'aggregate',
            'window', 'cte', 'materialized', 'partition'
        }
        
    def estimate_cost(self, plan: QueryPlan) -> float:
        """Estimate query cost using PostgreSQL's EXPLAIN."""
        sql = self.translate_plan(plan)
        with self.connection.cursor() as cursor:
            cursor.execute(f"EXPLAIN {sql}")
            explain_output = cursor.fetchall()
            # Parse cost from EXPLAIN output
            cost_line = explain_output[0][0]
            cost = float(cost_line.split('cost=')[1].split('..')[1].split(' ')[0])
            return cost
            
    def translate_plan(self, plan: QueryPlan) -> str:
        """Translate query plan to PostgreSQL SQL."""
        return self._plan_to_sql(plan)
        
    def execute_plan(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Execute PostgreSQL query."""
        sql = self.translate_plan(plan)
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
            
    def _plan_to_sql(self, plan: QueryPlan) -> str:
        """Convert query plan to PostgreSQL SQL."""
        node = plan.root
        
        if node.operation == 'select':
            parts = []
            # Handle WITH clause for CTEs
            if hasattr(node, 'ctes'):
                ctes = []
                for name, cte in node.ctes.items():
                    ctes.append(f"{name} AS ({self._plan_to_sql(cte)})")
                if ctes:
                    parts.append("WITH " + ",\n".join(ctes))
                    
            # Basic SELECT
            columns = node.columns if hasattr(node, 'columns') else ['*']
            parts.append(f"SELECT {', '.join(columns)}")
            
            # FROM clause
            tables = self._extract_tables(plan)
            parts.append(f"FROM {', '.join(tables)}")
            
            # WHERE clause
            if hasattr(node, 'condition'):
                parts.append(f"WHERE {node.condition}")
                
            # GROUP BY and HAVING
            if hasattr(node, 'group_by'):
                parts.append(f"GROUP BY {', '.join(node.group_by)}")
                if hasattr(node, 'having'):
                    parts.append(f"HAVING {node.having}")
                    
            # WINDOW functions
            if hasattr(node, 'windows'):
                window_clauses = []
                for name, spec in node.windows.items():
                    window_clauses.append(
                        f"{name} AS ({self._window_spec_to_sql(spec)})"
                    )
                if window_clauses:
                    parts.append("WINDOW " + ", ".join(window_clauses))
                    
            # ORDER BY
            if hasattr(node, 'order_by'):
                parts.append(f"ORDER BY {', '.join(node.order_by)}")
                
            # LIMIT and OFFSET
            if hasattr(node, 'limit'):
                parts.append(f"LIMIT {node.limit}")
            if hasattr(node, 'offset'):
                parts.append(f"OFFSET {node.offset}")
                
            return "\n".join(parts)
            
        raise NotImplementedError(f"Operation {node.operation} not supported")
        
    def _window_spec_to_sql(self, spec: Dict[str, Any]) -> str:
        """Convert window specification to SQL."""
        parts = []
        
        if 'partition_by' in spec:
            parts.append(f"PARTITION BY {', '.join(spec['partition_by'])}")
            
        if 'order_by' in spec:
            parts.append(f"ORDER BY {', '.join(spec['order_by'])}")
            
        if 'frame' in spec:
            parts.append(self._frame_to_sql(spec['frame']))
            
        return " ".join(parts)
        
    def _frame_to_sql(self, frame: Dict[str, Any]) -> str:
        """Convert frame specification to SQL."""
        unit = frame.get('unit', 'ROWS')
        start = frame.get('start', 'UNBOUNDED PRECEDING')
        end = frame.get('end', 'CURRENT ROW')
        return f"{unit} BETWEEN {start} AND {end}"

class ElasticsearchAdapter(DataSourceAdapter):
    """Adapter for Elasticsearch databases."""
    
    def __init__(self, hosts: List[str], **kwargs):
        self.client = Elasticsearch(hosts, **kwargs)
        
    def get_capabilities(self) -> Set[str]:
        """Get Elasticsearch capabilities."""
        return {
            'search', 'filter', 'aggregate', 'sort',
            'script', 'geo', 'terms', 'range', 'nested'
        }
        
    def estimate_cost(self, plan: QueryPlan) -> float:
        """Estimate query cost using Elasticsearch's _count."""
        query = self.translate_plan(plan)
        count = self.client.count(body=query)
        # Simple cost model based on document count
        return float(count['count'])
        
    def translate_plan(self, plan: QueryPlan) -> Dict[str, Any]:
        """Translate query plan to Elasticsearch query DSL."""
        return self._plan_to_query(plan)
        
    def execute_plan(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Execute Elasticsearch query."""
        query = self.translate_plan(plan)
        response = self.client.search(body=query)
        return [hit['_source'] for hit in response['hits']['hits']]
        
    def _plan_to_query(self, plan: QueryPlan) -> Dict[str, Any]:
        """Convert query plan to Elasticsearch query DSL."""
        node = plan.root
        query = {'query': {'bool': {'must': []}}}
        
        if node.operation == 'search':
            # Full-text search
            if hasattr(node, 'query_string'):
                query['query']['bool']['must'].append({
                    'query_string': {
                        'query': node.query_string
                    }
                })
                
            # Filters
            if hasattr(node, 'filters'):
                for field, value in node.filters.items():
                    if isinstance(value, dict):
                        # Range query
                        query['query']['bool']['must'].append({
                            'range': {
                                field: value
                            }
                        })
                    else:
                        # Term query
                        query['query']['bool']['must'].append({
                            'term': {
                                field: value
                            }
                        })
                        
            # Aggregations
            if hasattr(node, 'aggregations'):
                query['aggs'] = {}
                for name, agg in node.aggregations.items():
                    query['aggs'][name] = self._agg_to_query(agg)
                    
            # Sorting
            if hasattr(node, 'sort'):
                query['sort'] = []
                for field, order in node.sort:
                    query['sort'].append({field: order})
                    
            # Pagination
            if hasattr(node, 'size'):
                query['size'] = node.size
            if hasattr(node, 'from_'):
                query['from'] = node.from_
                
            return query
            
        raise NotImplementedError(f"Operation {node.operation} not supported")
        
    def _agg_to_query(self, agg: Dict[str, Any]) -> Dict[str, Any]:
        """Convert aggregation specification to Elasticsearch aggregation."""
        agg_type = agg['type']
        
        if agg_type == 'terms':
            return {
                'terms': {
                    'field': agg['field'],
                    'size': agg.get('size', 10)
                }
            }
            
        elif agg_type == 'date_histogram':
            return {
                'date_histogram': {
                    'field': agg['field'],
                    'interval': agg['interval']
                }
            }
            
        elif agg_type == 'nested':
            return {
                'nested': {
                    'path': agg['path']
                },
                'aggs': {
                    sub_name: self._agg_to_query(sub_agg)
                    for sub_name, sub_agg in agg['aggs'].items()
                }
            }
            
        raise NotImplementedError(f"Aggregation type {agg_type} not supported") 