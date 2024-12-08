from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from .query_parser_nosql_advanced import AdvancedNoSQLParser
from .query_parser_core import QueryNode, QueryPlan

@dataclass
class MapReduceSpec:
    """Specification for Map-Reduce operation."""
    map_function: str
    reduce_function: str
    finalize_function: Optional[str] = None
    scope: Optional[Dict[str, Any]] = None

@dataclass
class TimeSeriesSpec:
    """Specification for Time Series operations."""
    time_field: str
    value_field: str
    granularity: str
    operation: str
    window: Optional[int] = None
    groupby_fields: Optional[List[str]] = None

class ExtendedNoSQLParser(AdvancedNoSQLParser):
    """Extended NoSQL parser with additional advanced features."""
    
    def parse_query(self, query: Dict[str, Any]) -> QueryPlan:
        """Parse an extended NoSQL query."""
        # Check for MapReduce
        if 'mapReduce' in query:
            return self._parse_mapreduce_query(query)
            
        # Check for Time Series
        if 'timeseries' in query:
            return self._parse_timeseries_query(query)
            
        return super().parse_query(query)
        
    def _parse_mapreduce_query(self, query: Dict[str, Any]) -> QueryPlan:
        """Parse a MapReduce query."""
        map_func = query['map']
        reduce_func = query['reduce']
        finalize_func = query.get('finalize')
        scope = query.get('scope', {})
        
        # Create MapReduce specification
        mr_spec = MapReduceSpec(
            map_function=map_func,
            reduce_function=reduce_func,
            finalize_function=finalize_func,
            scope=scope
        )
        
        # Create MapReduce node
        root = QueryNode(
            operation='mapreduce',
            mr_spec=mr_spec
        )
        
        return QueryPlan(root)
        
    def _parse_timeseries_query(self, query: Dict[str, Any]) -> QueryPlan:
        """Parse a Time Series query."""
        ts_spec = TimeSeriesSpec(
            time_field=query['timeseries']['timeField'],
            value_field=query['timeseries']['valueField'],
            granularity=query['timeseries']['granularity'],
            operation=query['timeseries']['operation'],
            window=query['timeseries'].get('window'),
            groupby_fields=query['timeseries'].get('groupBy', [])
        )
        
        # Create Time Series node
        root = QueryNode(
            operation='timeseries',
            ts_spec=ts_spec
        )
        
        # Handle additional pipeline stages
        if 'pipeline' in query:
            pipeline_plan = super().parse_query({'pipeline': query['pipeline']})
            root.children.append(pipeline_plan.root)
            
        return QueryPlan(root)
        
    def parse_mapreduce_function(self, func_str: str) -> Dict[str, Any]:
        """Parse a MapReduce function string into an AST."""
        # Basic function parsing - could be enhanced with full JS parsing
        return {
            'type': 'function',
            'body': func_str
        }
        
    def parse_window_spec(self, window_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a time window specification."""
        return {
            'unit': window_spec.get('unit', 'hours'),
            'value': window_spec.get('value', 1),
            'sliding': window_spec.get('sliding', False)
        }
        
    def parse_granularity(self, granularity: str) -> Dict[str, Any]:
        """Parse a time granularity specification."""
        # Handle both simple string and complex object specs
        if isinstance(granularity, str):
            return {'unit': granularity}
            
        return {
            'unit': granularity.get('unit', 'hour'),
            'value': granularity.get('value', 1),
            'timezone': granularity.get('timezone', 'UTC')
        }
        
    def parse_time_operation(self, operation: str) -> Dict[str, Any]:
        """Parse a time series operation specification."""
        # Handle both simple aggregations and complex operations
        if operation in ['sum', 'avg', 'min', 'max', 'count']:
            return {'type': 'simple_agg', 'function': operation}
            
        return {
            'type': 'complex',
            'function': operation,
            'params': {}  # Could be extended for complex operations
        } 