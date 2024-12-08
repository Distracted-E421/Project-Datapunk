from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
import hashlib
import json
import time
from datetime import datetime, timedelta
from .query_exec_core import ExecutionOperator, ExecutionContext
from ..parser.query_parser_core import QueryNode, QueryPlan

class QueryCache:
    """Cache for query results."""
    
    def __init__(self, max_size: int = 1000, ttl: timedelta = timedelta(hours=1)):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        self.dependencies: Dict[str, Set[str]] = {}
        
    def get(self, key: str) -> Optional[Iterator[Dict[str, Any]]]:
        """Get cached results for a query."""
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        access_time = self.access_times[key]
        
        # Check if entry has expired
        if datetime.now() - access_time > self.ttl:
            self._remove_entry(key)
            return None
            
        # Update access time
        self.access_times[key] = datetime.now()
        
        return iter(entry['results'])
        
    def set(self, key: str, results: List[Dict[str, Any]], 
            dependencies: Optional[Set[str]] = None) -> None:
        """Cache results for a query."""
        # Evict entries if cache is full
        while len(self.cache) >= self.max_size:
            self._evict_lru()
            
        # Store results and metadata
        self.cache[key] = {
            'results': results,
            'created_at': datetime.now()
        }
        self.access_times[key] = datetime.now()
        
        if dependencies:
            self.dependencies[key] = dependencies
            
    def invalidate(self, table_name: str) -> None:
        """Invalidate cache entries dependent on a table."""
        keys_to_remove = set()
        
        # Find all queries dependent on the table
        for key, deps in self.dependencies.items():
            if table_name in deps:
                keys_to_remove.add(key)
                
        # Remove invalidated entries
        for key in keys_to_remove:
            self._remove_entry(key)
            
    def _remove_entry(self, key: str) -> None:
        """Remove a cache entry and its metadata."""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.dependencies.pop(key, None)
        
    def _evict_lru(self) -> None:
        """Evict least recently used cache entry."""
        if not self.access_times:
            return
            
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        self._remove_entry(lru_key)

class CachingContext(ExecutionContext):
    """Extended context with query result caching."""
    
    def __init__(self):
        super().__init__()
        self.query_cache = QueryCache()
        
    def get_cache_key(self, node: QueryNode) -> str:
        """Generate cache key for a query node."""
        node_dict = {
            'operation': node.operation,
            'columns': getattr(node, 'columns', None),
            'table_name': getattr(node, 'table_name', None),
            'predicate': getattr(node, 'predicate', None),
            'join_condition': getattr(node, 'join_condition', None),
            'group_by': getattr(node, 'group_by', None),
            'aggregates': getattr(node, 'aggregates', None),
            'children': [self.get_cache_key(child) for child in node.children]
        }
        
        # Create deterministic JSON string
        json_str = json.dumps(node_dict, sort_keys=True)
        
        # Generate hash
        return hashlib.sha256(json_str.encode()).hexdigest()

class CachingOperator(ExecutionOperator):
    """Base operator with caching support."""
    
    def __init__(self, node: QueryNode, context: CachingContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        self.cache_key = context.get_cache_key(node)
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with caching support."""
        # Try to get cached results
        cached_results = self.context.query_cache.get(self.cache_key)
        if cached_results is not None:
            yield from cached_results
            return
            
        # Execute and cache results
        results = list(super().execute())
        self.context.query_cache.set(
            self.cache_key,
            results,
            self._get_dependencies()
        )
        
        yield from iter(results)
        
    def _get_dependencies(self) -> Set[str]:
        """Get table dependencies for this operator."""
        deps = set()
        
        if hasattr(self.node, 'table_name'):
            deps.add(self.node.table_name)
            
        for child in self.children:
            if isinstance(child, CachingOperator):
                deps.update(child._get_dependencies())
                
        return deps

class CachingExecutionEngine:
    """Execution engine with result caching."""
    
    def __init__(self):
        self.context = CachingContext()
        
    def execute_plan(self, plan: QueryPlan) -> Iterator[Dict[str, Any]]:
        """Execute a query plan with result caching."""
        # Build execution tree with caching
        root_operator = self._build_caching_tree(plan.root)
        
        # Execute and return results
        yield from root_operator.execute()
        
    def _build_caching_tree(self, node: QueryNode) -> ExecutionOperator:
        """Build an execution tree with caching operators."""
        operator = CachingOperator(node, self.context)
        
        # Recursively build children
        for child in node.children:
            child_operator = self._build_caching_tree(child)
            operator.add_child(child_operator)
            
        return operator
        
    def invalidate_cache(self, table_name: str) -> None:
        """Invalidate cache entries for a table."""
        self.context.query_cache.invalidate(table_name)
        
    def clear_cache(self) -> None:
        """Clear the entire query cache."""
        self.context.query_cache = QueryCache() 