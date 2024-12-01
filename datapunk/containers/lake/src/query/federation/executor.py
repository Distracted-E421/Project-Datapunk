from typing import Dict, List, Optional, Any, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from dataclasses import dataclass
from .planner import SubQuery, DataSource
from ..executor.core import QueryExecutor
from ...storage.cache import CacheManager

@dataclass
class QueryResult:
    """Represents results from a sub-query execution."""
    source: DataSource
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class FederatedQueryExecutor:
    """Executes distributed queries across multiple data sources."""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executors: Dict[str, QueryExecutor] = {}
        self.cache_manager = CacheManager()
        
    def register_executor(self, source_name: str, executor: QueryExecutor) -> None:
        """Register an executor for a data source."""
        self.executors[source_name] = executor
        
    async def execute_plan(self, plan: List[SubQuery]) -> Iterator[QueryResult]:
        """Execute a distributed query plan."""
        # Group queries by execution level (based on dependencies)
        levels = self._group_by_level(plan)
        
        results = []
        for level in levels:
            # Execute queries at this level in parallel
            level_results = await self._execute_level(level)
            results.extend(level_results)
            
            # Update dependent queries with intermediate results
            self._update_dependencies(plan, level_results)
            
        # Merge and process results
        final_results = self._process_results(results)
        
        return final_results
        
    def _group_by_level(self, plan: List[SubQuery]) -> List[List[SubQuery]]:
        """Group queries by their dependency level."""
        levels: List[List[SubQuery]] = []
        remaining = plan.copy()
        
        while remaining:
            # Find queries with no remaining dependencies
            current_level = [
                query for query in remaining
                if not any(dep in remaining for dep in query.dependencies)
            ]
            
            if not current_level:
                # Circular dependency or other error
                raise ValueError("Invalid query plan: circular dependencies detected")
                
            levels.append(current_level)
            for query in current_level:
                remaining.remove(query)
                
        return levels
        
    async def _execute_level(self, queries: List[SubQuery]) -> List[QueryResult]:
        """Execute a group of independent queries in parallel."""
        loop = asyncio.get_event_loop()
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create futures for each query
            futures = [
                loop.run_in_executor(
                    executor,
                    self._execute_single_query,
                    query
                )
                for query in queries
            ]
            
            # Wait for all queries to complete
            completed_results = await asyncio.gather(*futures)
            results.extend(completed_results)
            
        return results
        
    def _execute_single_query(self, query: SubQuery) -> QueryResult:
        """Execute a single sub-query."""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query)
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                return QueryResult(
                    source=query.source,
                    data=cached_result,
                    metadata={"cached": True}
                )
                
            # Get appropriate executor
            executor = self.executors.get(query.source.name)
            if not executor:
                raise ValueError(f"No executor found for source {query.source.name}")
                
            # Execute query
            start_time = asyncio.get_event_loop().time()
            result_data = executor.execute(query.query)
            end_time = asyncio.get_event_loop().time()
            
            # Cache results if appropriate
            if self._should_cache(query, result_data):
                self.cache_manager.set(cache_key, result_data)
                
            return QueryResult(
                source=query.source,
                data=result_data,
                metadata={
                    "execution_time": end_time - start_time,
                    "cached": False
                }
            )
            
        except Exception as e:
            return QueryResult(
                source=query.source,
                data=[],
                metadata={},
                error=str(e)
            )
            
    def _update_dependencies(self, plan: List[SubQuery],
                           results: List[QueryResult]) -> None:
        """Update dependent queries with intermediate results."""
        # Create mapping of completed queries
        completed = {
            str(result.source.name): result.data
            for result in results
            if not result.error
        }
        
        # Update dependent queries
        for query in plan:
            self._update_query_with_results(query, completed)
            
    def _update_query_with_results(self, query: SubQuery,
                                 completed_results: Dict[str, List[Dict[str, Any]]]) -> None:
        """Update a query with results from its dependencies."""
        # This would modify the query to include results from dependencies
        # Implementation depends on how queries handle intermediate results
        pass
        
    def _process_results(self, results: List[QueryResult]) -> Iterator[QueryResult]:
        """Process and merge query results."""
        # Filter out errors
        valid_results = [r for r in results if not r.error]
        
        # Group by source type for appropriate merging
        by_type = {}
        for result in valid_results:
            source_type = result.source.type
            if source_type not in by_type:
                by_type[source_type] = []
            by_type[source_type].append(result)
            
        # Process each type appropriately
        for source_type, type_results in by_type.items():
            yield from self._merge_results(type_results)
            
    def _merge_results(self, results: List[QueryResult]) -> Iterator[QueryResult]:
        """Merge results from similar sources."""
        # This is a simple concatenation - actual implementation would
        # handle more complex merging scenarios
        for result in results:
            yield result
            
    def _generate_cache_key(self, query: SubQuery) -> str:
        """Generate a cache key for a query."""
        # This would implement a more sophisticated cache key generation
        return f"{query.source.name}:{hash(str(query.query))}"
        
    def _should_cache(self, query: SubQuery, 
                     results: List[Dict[str, Any]]) -> bool:
        """Determine if results should be cached."""
        # Implement caching policy based on:
        # - Query characteristics
        # - Result size
        # - Data source type
        # - Update frequency
        return len(results) > 0  # Simple policy for now 