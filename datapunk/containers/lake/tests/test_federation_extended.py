import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any
from elasticsearch import Elasticsearch
from ..src.query.federation.adapters_extended import (
    PostgreSQLAdapter,
    ElasticsearchAdapter
)
from ..src.query.federation.splitter import (
    QuerySplitter,
    SplitPoint,
    SplitCost
)
from ..src.query.federation.merger import (
    QueryMerger,
    HashMergeStrategy,
    SortMergeStrategy,
    StreamingMergeStrategy,
    AggregationMergeStrategy
)
from ..src.query.parser.core import QueryNode, QueryPlan

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    # Create PostgreSQL test data
    pg_data = {
        'users': [
            {'id': 1, 'name': 'Alice', 'age': 30},
            {'id': 2, 'name': 'Bob', 'age': 25},
            {'id': 3, 'name': 'Charlie', 'age': 35}
        ],
        'orders': [
            {'id': 1, 'user_id': 1, 'amount': 100},
            {'id': 2, 'user_id': 1, 'amount': 200},
            {'id': 3, 'user_id': 2, 'amount': 150}
        ]
    }
    
    # Create Elasticsearch test data
    es_data = {
        'products': [
            {'id': 'A', 'name': 'Widget', 'category': 'Tools'},
            {'id': 'B', 'name': 'Gadget', 'category': 'Electronics'},
            {'id': 'C', 'name': 'Device', 'category': 'Electronics'}
        ]
    }
    
    return {
        'postgresql': pg_data,
        'elasticsearch': es_data
    }

class TestPostgreSQLAdapter:
    """Test cases for PostgreSQL adapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create PostgreSQL adapter instance."""
        return PostgreSQLAdapter({
            'dbname': 'test',
            'user': 'test',
            'password': 'test',
            'host': 'localhost'
        })
        
    def test_capabilities(self, adapter):
        """Test capability reporting."""
        capabilities = adapter.get_capabilities()
        assert 'window' in capabilities
        assert 'cte' in capabilities
        assert 'materialized' in capabilities
        
    def test_complex_query_translation(self, adapter):
        """Test translation of complex queries."""
        # Create a complex query plan with window functions
        plan = QueryPlan(
            QueryNode(
                operation='select',
                columns=['name', 'amount', 'rank'],
                ctes={
                    'ranked_orders': QueryPlan(
                        QueryNode(
                            operation='window',
                            source='orders',
                            windows={
                                'order_rank': {
                                    'partition_by': ['user_id'],
                                    'order_by': ['amount DESC']
                                }
                            }
                        )
                    )
                }
            )
        )
        
        sql = adapter.translate_plan(plan)
        assert 'WITH' in sql
        assert 'WINDOW' in sql
        assert 'PARTITION BY' in sql
        
    def test_cost_estimation(self, adapter):
        """Test query cost estimation."""
        plan = QueryPlan(
            QueryNode(
                operation='select',
                table='users',
                columns=['name'],
                condition='age > 25'
            )
        )
        
        cost = adapter.estimate_cost(plan)
        assert isinstance(cost, float)
        assert cost > 0

class TestElasticsearchAdapter:
    """Test cases for Elasticsearch adapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create Elasticsearch adapter instance."""
        return ElasticsearchAdapter(['localhost:9200'])
        
    def test_capabilities(self, adapter):
        """Test capability reporting."""
        capabilities = adapter.get_capabilities()
        assert 'search' in capabilities
        assert 'geo' in capabilities
        assert 'nested' in capabilities
        
    def test_fulltext_query_translation(self, adapter):
        """Test translation of full-text search queries."""
        plan = QueryPlan(
            QueryNode(
                operation='search',
                query_string='electronics OR tools',
                filters={'category': 'Electronics'}
            )
        )
        
        query = adapter.translate_plan(plan)
        assert 'query' in query
        assert 'bool' in query['query']
        assert 'must' in query['query']['bool']
        
    def test_aggregation_translation(self, adapter):
        """Test translation of aggregation queries."""
        plan = QueryPlan(
            QueryNode(
                operation='search',
                aggregations={
                    'categories': {
                        'type': 'terms',
                        'field': 'category',
                        'size': 10
                    }
                }
            )
        )
        
        query = adapter.translate_plan(plan)
        assert 'aggs' in query
        assert 'categories' in query['aggs']
        assert query['aggs']['categories']['terms']['field'] == 'category'

class TestQuerySplitter:
    """Test cases for query splitting."""
    
    @pytest.fixture
    def splitter(self):
        """Create query splitter instance."""
        return QuerySplitter()
        
    def test_split_point_identification(self, splitter):
        """Test identification of split points."""
        plan = QueryPlan(
            QueryNode(
                operation='join',
                left=QueryNode(
                    operation='select',
                    table='users'
                ),
                right=QueryNode(
                    operation='select',
                    table='orders'
                )
            )
        )
        
        capabilities = {
            'source1': {'select', 'join'},
            'source2': {'select'}
        }
        
        points = splitter.find_split_points(plan, capabilities)
        assert len(points) > 0
        assert isinstance(points[0], SplitPoint)
        
    def test_cost_based_splitting(self, splitter):
        """Test cost-based query splitting."""
        plan = QueryPlan(
            QueryNode(
                operation='join',
                left=QueryNode(
                    operation='select',
                    table='users',
                    data_size=1000
                ),
                right=QueryNode(
                    operation='select',
                    table='orders',
                    data_size=5000
                )
            )
        )
        
        capabilities = {
            'source1': {'select', 'join'},
            'source2': {'select', 'join'}
        }
        
        subplans = splitter.split_plan(plan, capabilities)
        assert len(subplans) > 0
        assert all(isinstance(p, QueryPlan) for p in subplans.values())

class TestQueryMerger:
    """Test cases for query merging."""
    
    @pytest.fixture
    def merger(self):
        """Create query merger instance."""
        return QueryMerger()
        
    def test_hash_merge_strategy(self, merger):
        """Test hash-based merge strategy."""
        left_data = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ]
        right_data = [
            {'id': 1, 'value': 100},
            {'id': 2, 'value': 200}
        ]
        
        strategy = HashMergeStrategy(['id'])
        result = strategy.merge(left_data, right_data)
        
        assert len(result) == 2
        assert all('name' in r and 'value' in r for r in result)
        
    def test_streaming_merge_strategy(self, merger):
        """Test streaming merge strategy."""
        # Create large datasets
        left_data = [
            {'id': i, 'name': f'User{i}'}
            for i in range(2000)
        ]
        right_data = [
            {'id': i, 'value': i * 100}
            for i in range(2000)
        ]
        
        strategy = StreamingMergeStrategy(['id'], chunk_size=500)
        result = strategy.merge(left_data, right_data)
        
        assert len(result) == 2000
        assert all('name' in r and 'value' in r for r in result)
        
    def test_aggregation_merge_strategy(self, merger):
        """Test aggregation merge strategy."""
        datasets = [
            [
                {'group': 'A', 'value': 100},
                {'group': 'B', 'value': 200}
            ],
            [
                {'group': 'A', 'value': 300},
                {'group': 'B', 'value': 400}
            ]
        ]
        
        strategy = AggregationMergeStrategy(
            group_columns=['group'],
            agg_columns={'value': 'sum'}
        )
        result = strategy.merge(datasets)
        
        assert len(result) == 2
        assert result[0]['value'] == 400  # A: 100 + 300
        assert result[1]['value'] == 600  # B: 200 + 400
        
    def test_merge_strategy_selection(self, merger):
        """Test automatic merge strategy selection."""
        subplans = {
            'source1': QueryPlan(
                QueryNode(
                    operation='aggregate',
                    group_by=['category'],
                    aggregates={'amount': 'sum'}
                )
            ),
            'source2': QueryPlan(
                QueryNode(
                    operation='aggregate',
                    group_by=['category'],
                    aggregates={'amount': 'sum'}
                )
            )
        }
        
        strategy = merger.create_merge_plan(subplans, available_memory=1000.0)
        assert isinstance(strategy, AggregationMergeStrategy)
        
    def test_memory_aware_merging(self, merger):
        """Test memory-aware merge strategy selection."""
        subplans = {
            'source1': QueryPlan(
                QueryNode(
                    operation='select',
                    result_size=1000.0
                )
            ),
            'source2': QueryPlan(
                QueryNode(
                    operation='select',
                    result_size=2000.0
                )
            )
        }
        
        # Test with limited memory
        strategy1 = merger.create_merge_plan(subplans, available_memory=1000.0)
        assert isinstance(strategy1, StreamingMergeStrategy)
        
        # Test with ample memory
        strategy2 = merger.create_merge_plan(subplans, available_memory=5000.0)
        assert isinstance(strategy2, HashMergeStrategy) 