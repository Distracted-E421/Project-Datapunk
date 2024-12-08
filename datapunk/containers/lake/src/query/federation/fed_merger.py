from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from .fed_planner import DataSourceType
from .query_fed_executor import QueryResult
from datetime import datetime
import asyncio
import logging
from ..parser.query_parser_core import QueryPlan, QueryNode
from .fed_splitter import SubQuery

class MergeStrategy(Enum):
    """Available merge strategies."""
    UNION = "union"           # Combine all results
    INTERSECTION = "intersect"  # Only matching records
    LEFT_JOIN = "left_join"   # Keep all left records
    RIGHT_JOIN = "right_join" # Keep all right records
    OUTER_JOIN = "outer_join" # Keep all records
    CONCAT = "concat"         # Simple concatenation

@dataclass
class MergeConfig:
    """Configuration for result merging."""
    strategy: MergeStrategy
    key_columns: Optional[List[str]] = None
    aggregations: Optional[Dict[str, str]] = None
    filters: Optional[Dict[str, Callable]] = None
    sort_columns: Optional[List[str]] = None
    dedup_columns: Optional[List[str]] = None

class ResultMerger:
    """Handles merging of query results from different sources."""
    
    def __init__(self):
        self._type_handlers = {
            DataSourceType.RELATIONAL: self._handle_relational,
            DataSourceType.DOCUMENT: self._handle_document,
            DataSourceType.GRAPH: self._handle_graph,
            DataSourceType.OBJECT_STORE: self._handle_object_store,
            DataSourceType.TIME_SERIES: self._handle_time_series
        }
        
    def merge_results(self, results: List[QueryResult],
                     config: MergeConfig) -> List[Dict[str, Any]]:
        """Merge query results according to configuration."""
        if not results:
            return []
            
        # Group results by source type
        by_type = self._group_by_type(results)
        
        # Merge within each type first
        intermediate_results = []
        for source_type, type_results in by_type.items():
            handler = self._type_handlers.get(source_type)
            if handler:
                merged = handler(type_results, config)
                intermediate_results.append(merged)
                
        # Final merge across types
        return self._merge_dataframes(intermediate_results, config)
        
    def _group_by_type(self, 
                      results: List[QueryResult]) -> Dict[DataSourceType, List[QueryResult]]:
        """Group results by source type."""
        grouped = {}
        for result in results:
            source_type = result.source.type
            if source_type not in grouped:
                grouped[source_type] = []
            grouped[source_type].append(result)
        return grouped
        
    def _handle_relational(self, results: List[QueryResult],
                          config: MergeConfig) -> pd.DataFrame:
        """Handle relational database results."""
        # Convert to dataframes
        dfs = [pd.DataFrame(r.data) for r in results]
        
        # Apply merge strategy
        if config.strategy == MergeStrategy.UNION:
            return pd.concat(dfs, ignore_index=True)
        elif config.strategy in (MergeStrategy.INTERSECTION, 
                               MergeStrategy.LEFT_JOIN,
                               MergeStrategy.RIGHT_JOIN,
                               MergeStrategy.OUTER_JOIN):
            return self._merge_relational(dfs, config)
        else:
            return pd.concat(dfs, ignore_index=True)
            
    def _handle_document(self, results: List[QueryResult],
                        config: MergeConfig) -> pd.DataFrame:
        """Handle document database results."""
        # Flatten nested documents
        flat_results = []
        for result in results:
            flat_results.extend(self._flatten_documents(result.data))
            
        # Convert to dataframe
        df = pd.DataFrame(flat_results)
        
        # Handle arrays and nested objects
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                df[col] = df[col].apply(str)
                
        return df
        
    def _handle_graph(self, results: List[QueryResult],
                     config: MergeConfig) -> pd.DataFrame:
        """Handle graph database results."""
        # Convert graph results to tabular format
        tabular_results = []
        for result in results:
            tabular_results.extend(self._graph_to_tabular(result.data))
            
        return pd.DataFrame(tabular_results)
        
    def _handle_object_store(self, results: List[QueryResult],
                           config: MergeConfig) -> pd.DataFrame:
        """Handle object store results."""
        # Combine metadata and content
        combined_results = []
        for result in results:
            combined_results.extend(self._combine_object_metadata(result.data))
            
        return pd.DataFrame(combined_results)
        
    def _handle_time_series(self, results: List[QueryResult],
                          config: MergeConfig) -> pd.DataFrame:
        """Handle time series results."""
        # Convert to time-indexed dataframes
        dfs = []
        for result in results:
            df = pd.DataFrame(result.data)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df.set_index("timestamp", inplace=True)
            dfs.append(df)
            
        # Merge time series
        return self._merge_time_series(dfs, config)
        
    def _merge_relational(self, dfs: List[pd.DataFrame],
                         config: MergeConfig) -> pd.DataFrame:
        """Merge relational dataframes."""
        if not config.key_columns:
            return pd.concat(dfs, ignore_index=True)
            
        result = dfs[0]
        for df in dfs[1:]:
            how = config.strategy.value.replace("_", " ")
            result = pd.merge(result, df, on=config.key_columns, how=how)
            
        return result
        
    def _merge_time_series(self, dfs: List[pd.DataFrame],
                          config: MergeConfig) -> pd.DataFrame:
        """Merge time series dataframes."""
        # Combine all time series
        result = pd.concat(dfs, axis=1)
        
        # Handle duplicates in column names
        result.columns = [f"{col}_{i}" if result.columns.tolist().count(col) > 1
                         else col for i, col in enumerate(result.columns)]
                         
        # Apply aggregations if specified
        if config.aggregations:
            result = result.resample("1min").agg(config.aggregations)
            
        return result
        
    def _flatten_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Flatten nested documents."""
        flattened = []
        for doc in documents:
            flat_doc = {}
            self._flatten_dict(doc, "", flat_doc)
            flattened.append(flat_doc)
        return flattened
        
    def _flatten_dict(self, d: Dict[str, Any], prefix: str,
                     result: Dict[str, Any]) -> None:
        """Recursively flatten a dictionary."""
        for key, value in d.items():
            new_key = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_dict(value, f"{new_key}.", result)
            else:
                result[new_key] = value
                
    def _graph_to_tabular(self, graph_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert graph results to tabular format."""
        tabular = []
        for item in graph_data:
            if "nodes" in item:
                # Handle node results
                for node in item["nodes"]:
                    row = {"type": "node", "id": node.get("id")}
                    row.update(node.get("properties", {}))
                    tabular.append(row)
            if "relationships" in item:
                # Handle relationship results
                for rel in item["relationships"]:
                    row = {
                        "type": "relationship",
                        "start_id": rel.get("start"),
                        "end_id": rel.get("end"),
                        "relationship_type": rel.get("type")
                    }
                    row.update(rel.get("properties", {}))
                    tabular.append(row)
        return tabular
        
    def _combine_object_metadata(self, 
                               objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine object content with metadata."""
        combined = []
        for obj in objects:
            metadata = obj.get("metadata", {})
            content = obj.get("content", {})
            row = {**metadata, **content}
            combined.append(row)
        return combined
        
    def _merge_dataframes(self, dfs: List[pd.DataFrame],
                         config: MergeConfig) -> List[Dict[str, Any]]:
        """Merge dataframes and apply final processing."""
        if not dfs:
            return []
            
        # Merge all dataframes
        result = pd.concat(dfs, ignore_index=True)
        
        # Apply filters
        if config.filters:
            for column, filter_func in config.filters.items():
                if column in result.columns:
                    result = result[result[column].apply(filter_func)]
                    
        # Sort if requested
        if config.sort_columns:
            result.sort_values(config.sort_columns, inplace=True)
            
        # Remove duplicates if requested
        if config.dedup_columns:
            result.drop_duplicates(subset=config.dedup_columns, inplace=True)
            
        # Convert to list of dictionaries
        return result.to_dict("records")

@dataclass
class MergeStrategy:
    """Strategy for merging query results."""
    operation: str  # 'union', 'join', 'aggregate', etc.
    parameters: Dict[str, Any]
    estimated_memory: int  # bytes
    parallelizable: bool

class QueryMerger:
    """Merges results from federated query execution."""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.logger = logging.getLogger(__name__)
    
    async def merge_results(self,
                          results: List[Any],
                          subqueries: List[SubQuery],
                          original_plan: QueryPlan) -> Any:
        """Merge results from multiple subqueries."""
        try:
            # Convert results to DataFrames for easier manipulation
            dfs = [self._to_dataframe(result) for result in results]
            
            # Determine merge strategy
            strategy = self._determine_merge_strategy(
                subqueries, original_plan, dfs
            )
            
            # Check memory requirements
            self._check_memory_requirements(strategy, dfs)
            
            # Execute merge based on strategy
            if strategy.operation == 'union':
                return await self._merge_union(dfs, strategy)
            elif strategy.operation == 'join':
                return await self._merge_join(dfs, strategy)
            elif strategy.operation == 'aggregate':
                return await self._merge_aggregate(dfs, strategy)
            else:
                raise ValueError(f"Unsupported merge operation: {strategy.operation}")
        except Exception as e:
            self.logger.error(f"Error merging results: {e}")
            raise
    
    def _to_dataframe(self, result: Any) -> pd.DataFrame:
        """Convert query result to DataFrame."""
        if isinstance(result, pd.DataFrame):
            return result
        elif isinstance(result, list):
            return pd.DataFrame(result)
        elif isinstance(result, dict):
            return pd.DataFrame([result])
        else:
            raise ValueError(f"Unsupported result type: {type(result)}")
    
    def _determine_merge_strategy(self,
                                subqueries: List[SubQuery],
                                original_plan: QueryPlan,
                                dfs: List[pd.DataFrame]) -> MergeStrategy:
        """Determine how to merge the results."""
        # Check for joins in original plan
        if self._has_joins(original_plan):
            return MergeStrategy(
                operation='join',
                parameters=self._extract_join_params(original_plan),
                estimated_memory=self._estimate_join_memory(dfs),
                parallelizable=True
            )
        
        # Check for aggregations
        elif self._has_aggregates(original_plan):
            return MergeStrategy(
                operation='aggregate',
                parameters=self._extract_aggregate_params(original_plan),
                estimated_memory=self._estimate_aggregate_memory(dfs),
                parallelizable=True
            )
        
        # Default to union
        else:
            return MergeStrategy(
                operation='union',
                parameters={},
                estimated_memory=sum(df.memory_usage(deep=True).sum() for df in dfs),
                parallelizable=True
            )
    
    def _check_memory_requirements(self,
                                 strategy: MergeStrategy,
                                 dfs: List[pd.DataFrame]) -> None:
        """Check if merge operation fits in memory."""
        if strategy.estimated_memory > self.max_memory_bytes:
            # Try to optimize memory usage
            if strategy.operation == 'join':
                self._optimize_join_memory(dfs, strategy)
            elif strategy.operation == 'aggregate':
                self._optimize_aggregate_memory(dfs, strategy)
            
            # Recheck after optimization
            if strategy.estimated_memory > self.max_memory_bytes:
                raise MemoryError(
                    f"Merge operation requires {strategy.estimated_memory / 1024 / 1024}MB, "
                    f"but only {self.max_memory_bytes / 1024 / 1024}MB available"
                )
    
    async def _merge_union(self,
                          dfs: List[pd.DataFrame],
                          strategy: MergeStrategy) -> pd.DataFrame:
        """Merge results using union operation."""
        try:
            # Ensure consistent column names
            columns = set()
            for df in dfs:
                columns.update(df.columns)
            
            # Add missing columns with NaN values
            aligned_dfs = []
            for df in dfs:
                missing_cols = columns - set(df.columns)
                if missing_cols:
                    df = df.copy()
                    for col in missing_cols:
                        df[col] = np.nan
                aligned_dfs.append(df[sorted(columns)])
            
            # Perform union
            if strategy.parallelizable and len(aligned_dfs) > 2:
                # Parallel union for multiple DataFrames
                chunk_size = max(2, len(aligned_dfs) // asyncio.get_event_loop().get_default_executor()._max_workers)
                chunks = [aligned_dfs[i:i + chunk_size] for i in range(0, len(aligned_dfs), chunk_size)]
                
                async def union_chunk(chunk: List[pd.DataFrame]) -> pd.DataFrame:
                    return pd.concat(chunk, ignore_index=True)
                
                tasks = [union_chunk(chunk) for chunk in chunks]
                chunk_results = await asyncio.gather(*tasks)
                return pd.concat(chunk_results, ignore_index=True)
            else:
                # Sequential union for small number of DataFrames
                return pd.concat(aligned_dfs, ignore_index=True)
        except Exception as e:
            self.logger.error(f"Error in union merge: {e}")
            raise
    
    async def _merge_join(self,
                         dfs: List[pd.DataFrame],
                         strategy: MergeStrategy) -> pd.DataFrame:
        """Merge results using join operation."""
        try:
            join_keys = strategy.parameters.get('keys', [])
            join_type = strategy.parameters.get('type', 'inner')
            
            if not join_keys:
                raise ValueError("Join keys not specified in strategy")
            
            result = dfs[0]
            remaining_dfs = dfs[1:]
            
            if strategy.parallelizable and len(remaining_dfs) > 1:
                # Parallel joins
                async def join_pair(left: pd.DataFrame,
                                  right: pd.DataFrame) -> pd.DataFrame:
                    return pd.merge(
                        left, right,
                        on=join_keys,
                        how=join_type
                    )
                
                while len(remaining_dfs) > 0:
                    # Join in pairs
                    pair_tasks = []
                    for i in range(0, len(remaining_dfs), 2):
                        if i + 1 < len(remaining_dfs):
                            pair_tasks.append(
                                join_pair(remaining_dfs[i], remaining_dfs[i + 1])
                            )
                        else:
                            remaining_dfs[i] = remaining_dfs[i]
                    
                    if pair_tasks:
                        pair_results = await asyncio.gather(*pair_tasks)
                        remaining_dfs = list(pair_results)
                    
                    if len(remaining_dfs) == 1:
                        result = await join_pair(result, remaining_dfs[0])
                        break
            else:
                # Sequential joins
                for df in remaining_dfs:
                    result = pd.merge(
                        result, df,
                        on=join_keys,
                        how=join_type
                    )
            
            return result
        except Exception as e:
            self.logger.error(f"Error in join merge: {e}")
            raise
    
    async def _merge_aggregate(self,
                             dfs: List[pd.DataFrame],
                             strategy: MergeStrategy) -> pd.DataFrame:
        """Merge results using aggregation."""
        try:
            group_by = strategy.parameters.get('group_by', [])
            aggregations = strategy.parameters.get('aggregations', {})
            
            if not aggregations:
                raise ValueError("Aggregations not specified in strategy")
            
            if strategy.parallelizable and len(dfs) > 2:
                # Parallel aggregation
                chunk_size = max(2, len(dfs) // asyncio.get_event_loop().get_default_executor()._max_workers)
                chunks = [dfs[i:i + chunk_size] for i in range(0, len(dfs), chunk_size)]
                
                async def aggregate_chunk(chunk: List[pd.DataFrame]) -> pd.DataFrame:
                    combined = pd.concat(chunk, ignore_index=True)
                    return combined.groupby(group_by).agg(aggregations)
                
                # Aggregate chunks in parallel
                tasks = [aggregate_chunk(chunk) for chunk in chunks]
                chunk_results = await asyncio.gather(*tasks)
                
                # Final aggregation of chunk results
                final_df = pd.concat(chunk_results, ignore_index=True)
                return final_df.groupby(group_by).agg(aggregations)
            else:
                # Sequential aggregation
                combined = pd.concat(dfs, ignore_index=True)
                return combined.groupby(group_by).agg(aggregations)
        except Exception as e:
            self.logger.error(f"Error in aggregate merge: {e}")
            raise
    
    def _has_joins(self, plan: QueryPlan) -> bool:
        """Check if plan contains join operations."""
        def check_node(node: QueryNode) -> bool:
            if node.operation_type.lower() == 'join':
                return True
            return any(check_node(child) for child in node.children)
        return check_node(plan.root)
    
    def _has_aggregates(self, plan: QueryPlan) -> bool:
        """Check if plan contains aggregate operations."""
        def check_node(node: QueryNode) -> bool:
            if node.operation_type.lower() == 'aggregate':
                return True
            return any(check_node(child) for child in node.children)
        return check_node(plan.root)
    
    def _extract_join_params(self, plan: QueryPlan) -> Dict[str, Any]:
        """Extract join parameters from query plan."""
        params = {
            'keys': [],
            'type': 'inner'
        }
        
        def extract_from_node(node: QueryNode) -> None:
            if node.operation_type.lower() == 'join':
                params['keys'].extend(node.join_keys)
                params['type'] = node.join_type or 'inner'
            for child in node.children:
                extract_from_node(child)
        
        extract_from_node(plan.root)
        return params
    
    def _extract_aggregate_params(self, plan: QueryPlan) -> Dict[str, Any]:
        """Extract aggregation parameters from query plan."""
        params = {
            'group_by': [],
            'aggregations': {}
        }
        
        def extract_from_node(node: QueryNode) -> None:
            if node.operation_type.lower() == 'aggregate':
                params['group_by'].extend(node.group_by or [])
                params['aggregations'].update(node.aggregations or {})
            for child in node.children:
                extract_from_node(child)
        
        extract_from_node(plan.root)
        return params
    
    def _estimate_join_memory(self, dfs: List[pd.DataFrame]) -> int:
        """Estimate memory required for join operation."""
        total_rows = sum(len(df) for df in dfs)
        avg_row_size = np.mean([
            df.memory_usage(deep=True).sum() / len(df)
            for df in dfs
            if len(df) > 0
        ])
        # Assume worst case of cartesian product
        return int(total_rows * total_rows * avg_row_size)
    
    def _estimate_aggregate_memory(self, dfs: List[pd.DataFrame]) -> int:
        """Estimate memory required for aggregation."""
        total_size = sum(df.memory_usage(deep=True).sum() for df in dfs)
        # Assume aggregation reduces size by 90%
        return int(total_size * 0.1)
    
    def _optimize_join_memory(self,
                            dfs: List[pd.DataFrame],
                            strategy: MergeStrategy) -> None:
        """Optimize memory usage for join operation."""
        # Convert object columns to categories where beneficial
        for df in dfs:
            for col in df.select_dtypes(include=['object']):
                if df[col].nunique() / len(df) < 0.1:  # Less than 10% unique values
                    df[col] = df[col].astype('category')
        
        # Update memory estimate
        strategy.estimated_memory = self._estimate_join_memory(dfs)
    
    def _optimize_aggregate_memory(self,
                                 dfs: List[pd.DataFrame],
                                 strategy: MergeStrategy) -> None:
        """Optimize memory usage for aggregation."""
        # Convert numeric columns to smaller types where possible
        for df in dfs:
            for col in df.select_dtypes(include=['int64', 'float64']):
                if df[col].min() >= np.iinfo(np.int32).min and \
                   df[col].max() <= np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
        
        # Update memory estimate
        strategy.estimated_memory = self._estimate_aggregate_memory(dfs)