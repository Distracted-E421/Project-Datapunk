from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from .planner import DataSourceType
from .executor import QueryResult

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