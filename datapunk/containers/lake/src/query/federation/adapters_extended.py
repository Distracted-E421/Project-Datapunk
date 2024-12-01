from typing import Any, Dict, List, Set
import psycopg2
from elasticsearch import Elasticsearch
from .adapters import DataSourceAdapter
from ..parser.core import QueryPlan, QueryNode

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