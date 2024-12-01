import pytest
from typing import Dict, Any
from ..src.query.parser.sql_extensions import ExtendedSQLParser, PivotSpec, UnpivotSpec, PatternSpec
from ..src.query.parser.nosql_extensions import ExtendedNoSQLParser, MapReduceSpec, TimeSeriesSpec
from ..src.query.parser.core import QueryPlan

class TestSQLExtensions:
    """Test cases for extended SQL parser features."""
    
    @pytest.fixture
    def parser(self):
        return ExtendedSQLParser()
        
    def test_pivot_query(self, parser):
        """Test PIVOT query parsing."""
        query = """
        SELECT *
        FROM sales
        PIVOT (
            SUM(amount) FOR quarter IN ('Q1', 'Q2', 'Q3', 'Q4')
        )
        """
        plan = parser.parse_query(query)
        
        assert isinstance(plan, QueryPlan)
        assert plan.root.operation == 'pivot'
        assert isinstance(plan.root.pivot_spec, PivotSpec)
        assert plan.root.pivot_spec.pivot_values == ['Q1', 'Q2', 'Q3', 'Q4']
        assert plan.root.pivot_spec.aggregate_function == 'SUM'
        assert plan.root.pivot_spec.value_column == 'amount'
        assert plan.root.pivot_spec.pivot_column == 'quarter'
        
    def test_unpivot_query(self, parser):
        """Test UNPIVOT query parsing."""
        query = """
        SELECT *
        FROM quarterly_sales
        UNPIVOT (
            amount FOR quarter IN (Q1, Q2, Q3, Q4)
        )
        """
        plan = parser.parse_query(query)
        
        assert isinstance(plan, QueryPlan)
        assert plan.root.operation == 'unpivot'
        assert isinstance(plan.root.unpivot_spec, UnpivotSpec)
        assert plan.root.unpivot_spec.value_column == 'amount'
        assert plan.root.unpivot_spec.name_column == 'quarter'
        assert plan.root.unpivot_spec.unpivot_columns == ['Q1', 'Q2', 'Q3', 'Q4']
        
    def test_pattern_query(self, parser):
        """Test MATCH_RECOGNIZE query parsing."""
        query = """
        SELECT *
        FROM stock_data
        MATCH_RECOGNIZE (
            PARTITION BY symbol
            ORDER BY trade_time
            MEASURES
                START_PRICE AS start_price,
                TOP_PRICE AS top_price,
                BOTTOM_PRICE AS bottom_price
            PATTERN (RISE+ TOP+ FALL+ BOTTOM)
            DEFINE
                RISE AS PRICE > PREV(PRICE),
                TOP AS PRICE >= PREV(PRICE),
                FALL AS PRICE < PREV(PRICE),
                BOTTOM AS PRICE <= PREV(PRICE)
        )
        """
        plan = parser.parse_query(query)
        
        assert isinstance(plan, QueryPlan)
        assert plan.root.operation == 'pattern_match'
        assert isinstance(plan.root.pattern_spec, PatternSpec)
        assert 'RISE+ TOP+ FALL+ BOTTOM' in plan.root.pattern_spec.pattern
        assert len(plan.root.pattern_spec.measures) == 3
        assert len(plan.root.pattern_spec.defines) == 4
        
    def test_model_query(self, parser):
        """Test MODEL clause parsing."""
        query = """
        SELECT *
        FROM sales
        MODEL
            DIMENSION BY (product, year)
            MEASURES (sales_amount)
            RULES (
                sales_amount[product, year] = 
                    sales_amount[product, year-1] * 1.1
            )
        """
        plan = parser.parse_query(query)
        
        assert isinstance(plan, QueryPlan)
        assert plan.root.operation == 'model'
        assert plan.root.dimensions == ['product', 'year']
        assert plan.root.measures == ['sales_amount']
        assert len(plan.root.rules) == 1

class TestNoSQLExtensions:
    """Test cases for extended NoSQL parser features."""
    
    @pytest.fixture
    def parser(self):
        return ExtendedNoSQLParser()
        
    def test_mapreduce_query(self, parser):
        """Test MapReduce query parsing."""
        query = {
            'mapReduce': 'sales',
            'map': '''
                function() {
                    emit(this.product, this.amount);
                }
            ''',
            'reduce': '''
                function(key, values) {
                    return Array.sum(values);
                }
            ''',
            'finalize': '''
                function(key, value) {
                    return { product: key, total: value };
                }
            ''',
            'scope': {'rate': 1.1}
        }
        
        plan = parser.parse_query(query)
        
        assert isinstance(plan, QueryPlan)
        assert plan.root.operation == 'mapreduce'
        assert isinstance(plan.root.mr_spec, MapReduceSpec)
        assert plan.root.mr_spec.map_function == query['map']
        assert plan.root.mr_spec.reduce_function == query['reduce']
        assert plan.root.mr_spec.finalize_function == query['finalize']
        assert plan.root.mr_spec.scope == query['scope']
        
    def test_timeseries_query(self, parser):
        """Test Time Series query parsing."""
        query = {
            'timeseries': {
                'timeField': 'timestamp',
                'valueField': 'temperature',
                'granularity': 'hour',
                'operation': 'avg',
                'window': 24,
                'groupBy': ['sensor_id']
            },
            'pipeline': [
                {'$match': {'location': 'warehouse'}}
            ]
        }
        
        plan = parser.parse_query(query)
        
        assert isinstance(plan, QueryPlan)
        assert plan.root.operation == 'timeseries'
        assert isinstance(plan.root.ts_spec, TimeSeriesSpec)
        assert plan.root.ts_spec.time_field == 'timestamp'
        assert plan.root.ts_spec.value_field == 'temperature'
        assert plan.root.ts_spec.granularity == 'hour'
        assert plan.root.ts_spec.operation == 'avg'
        assert plan.root.ts_spec.window == 24
        assert plan.root.ts_spec.groupby_fields == ['sensor_id']
        assert len(plan.root.children) == 1
        
    def test_window_spec_parsing(self, parser):
        """Test window specification parsing."""
        window_spec = {
            'unit': 'minutes',
            'value': 30,
            'sliding': True
        }
        
        result = parser.parse_window_spec(window_spec)
        
        assert result['unit'] == 'minutes'
        assert result['value'] == 30
        assert result['sliding'] is True
        
    def test_granularity_parsing(self, parser):
        """Test granularity specification parsing."""
        # Test simple string
        result1 = parser.parse_granularity('day')
        assert result1['unit'] == 'day'
        
        # Test complex object
        granularity = {
            'unit': 'hour',
            'value': 2,
            'timezone': 'PST'
        }
        result2 = parser.parse_granularity(granularity)
        assert result2['unit'] == 'hour'
        assert result2['value'] == 2
        assert result2['timezone'] == 'PST'
        
    def test_time_operation_parsing(self, parser):
        """Test time operation specification parsing."""
        # Test simple aggregation
        result1 = parser.parse_time_operation('avg')
        assert result1['type'] == 'simple_agg'
        assert result1['function'] == 'avg'
        
        # Test complex operation
        result2 = parser.parse_time_operation('moving_average')
        assert result2['type'] == 'complex'
        assert result2['function'] == 'moving_average' 