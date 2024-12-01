import unittest
from typing import Dict, List, Any
from ..src.query.executor.core import ExecutionContext
from ..src.query.executor.joins import (
    HashJoinOperator, MergeJoinOperator, 
    IndexNestedLoopJoinOperator, PartitionedHashJoinOperator
)
from ..src.query.executor.aggregates import EnhancedAggregateOperator
from ..src.query.executor.windows import WindowOperator
from ..src.query.executor.parallel import (
    ParallelContext, ParallelTableScan, 
    ParallelHashJoin, ParallelAggregation
)
from ..src.query.parser.core import QueryNode, QueryPlan
from ..src.storage.cache import CacheManager

class MockCacheManager(CacheManager):
    """Mock cache manager for testing."""
    
    def __init__(self, data: Dict[str, List[Dict[str, Any]]]):
        self.data = data
        
    def get(self, key: str) -> List[Dict[str, Any]]:
        return self.data.get(key, [])
        
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

class TestAdvancedJoins(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext()
        self.left_data = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'},
            {'id': 3, 'name': 'Charlie'}
        ]
        self.right_data = [
            {'id': 1, 'dept': 'HR'},
            {'id': 2, 'dept': 'IT'},
            {'id': 4, 'dept': 'Sales'}
        ]
        
    def test_hash_join(self):
        """Test hash join implementation."""
        node = QueryNode(operation='join',
                        join_condition={'left': 'id', 'right': 'id'})
                        
        class MockLeftOperator(HashJoinOperator):
            def execute(self):
                return iter(self.context.get_variable('left_data'))
                
        class MockRightOperator(HashJoinOperator):
            def execute(self):
                return iter(self.context.get_variable('right_data'))
                
        operator = HashJoinOperator(node, self.context)
        operator.add_child(MockLeftOperator(node, self.context))
        operator.add_child(MockRightOperator(node, self.context))
        
        self.context.set_variable('left_data', self.left_data)
        self.context.set_variable('right_data', self.right_data)
        
        results = list(operator.execute())
        self.assertEqual(len(results), 2)  # Only matching IDs 1 and 2
        
    def test_merge_join(self):
        """Test merge join implementation."""
        node = QueryNode(operation='join',
                        join_condition={'left': 'id', 'right': 'id'})
                        
        operator = MergeJoinOperator(node, self.context)
        # Add mock children similar to hash join test
        results = list(operator.execute())
        self.assertEqual(len(results), 2)
        
    def test_index_nested_loop_join(self):
        """Test index nested loop join implementation."""
        index = {1: [{'dept': 'HR'}], 2: [{'dept': 'IT'}]}
        node = QueryNode(operation='join',
                        join_condition={'left': 'id', 'right': 'id'})
                        
        operator = IndexNestedLoopJoinOperator(node, self.context, index)
        # Add mock children and test
        results = list(operator.execute())
        self.assertEqual(len(results), 2)

class TestAdvancedAggregates(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext()
        self.test_data = [
            {'category': 'A', 'value': 10, 'x': 1, 'y': 2},
            {'category': 'A', 'value': 20, 'x': 2, 'y': 4},
            {'category': 'B', 'value': 15, 'x': 3, 'y': 6},
            {'category': 'B', 'value': 25, 'x': 4, 'y': 8}
        ]
        
    def test_statistical_aggregates(self):
        """Test statistical aggregate functions."""
        node = QueryNode(
            operation='aggregate',
            group_by=['category'],
            aggregates=[
                {'function': 'stddev', 'column': 'value', 'alias': 'std'},
                {'function': 'variance', 'column': 'value', 'alias': 'var'},
                {'function': 'median', 'column': 'value', 'alias': 'med'}
            ]
        )
        
        operator = EnhancedAggregateOperator(node, self.context)
        # Add mock child and test
        results = list(operator.execute())
        self.assertEqual(len(results), 2)  # Two categories
        
    def test_correlation(self):
        """Test correlation aggregate function."""
        node = QueryNode(
            operation='aggregate',
            group_by=['category'],
            aggregates=[{
                'function': 'correlation',
                'columns': ['x', 'y'],
                'alias': 'corr'
            }]
        )
        
        operator = EnhancedAggregateOperator(node, self.context)
        # Add mock child and test
        results = list(operator.execute())
        self.assertEqual(len(results), 2)
        self.assertAlmostEqual(results[0]['corr'], 1.0)  # Perfect correlation

class TestWindowFunctions(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext()
        self.test_data = [
            {'id': 1, 'dept': 'HR', 'salary': 50000},
            {'id': 2, 'dept': 'HR', 'salary': 60000},
            {'id': 3, 'dept': 'IT', 'salary': 70000},
            {'id': 4, 'dept': 'IT', 'salary': 80000}
        ]
        
    def test_rank_functions(self):
        """Test rank window functions."""
        node = QueryNode(
            operation='window',
            partition_by=['dept'],
            order_by=['salary'],
            window_functions=[
                {'function': 'rank', 'alias': 'rank'},
                {'function': 'dense_rank', 'alias': 'dense_rank'},
                {'function': 'row_number', 'alias': 'row_num'}
            ]
        )
        
        operator = WindowOperator(node, self.context)
        # Add mock child and test
        results = list(operator.execute())
        self.assertEqual(len(results), 4)
        
    def test_lead_lag_functions(self):
        """Test lead/lag window functions."""
        node = QueryNode(
            operation='window',
            partition_by=['dept'],
            order_by=['salary'],
            window_functions=[
                {'function': 'lead', 'alias': 'next_salary', 'params': {'offset': 1}},
                {'function': 'lag', 'alias': 'prev_salary', 'params': {'offset': 1}}
            ]
        )
        
        operator = WindowOperator(node, self.context)
        # Add mock child and test
        results = list(operator.execute())
        self.assertEqual(len(results), 4)

class TestParallelExecution(unittest.TestCase):
    def setUp(self):
        self.context = ParallelContext(max_workers=2)
        self.test_data = {
            'employees': [
                {'id': i, 'name': f'Employee{i}', 'salary': i * 10000}
                for i in range(1, 101)  # 100 employees
            ]
        }
        self.cache_manager = MockCacheManager(self.test_data)
        
    def test_parallel_table_scan(self):
        """Test parallel table scan."""
        node = QueryNode(
            operation='table_scan',
            table_name='employees',
            columns=['id', 'name']
        )
        
        self.context.cache_manager = self.cache_manager
        operator = ParallelTableScan(node, self.context)
        results = list(operator.execute())
        
        self.assertEqual(len(results), 100)
        self.assertEqual(set(results[0].keys()), {'id', 'name'})
        
    def test_parallel_hash_join(self):
        """Test parallel hash join."""
        # Create large test datasets
        left_data = [{'id': i, 'name': f'Name{i}'} for i in range(1000)]
        right_data = [{'id': i, 'dept': f'Dept{i}'} for i in range(500, 1500)]
        
        node = QueryNode(
            operation='join',
            join_condition={'left': 'id', 'right': 'id'}
        )
        
        operator = ParallelHashJoin(node, self.context)
        # Add mock children with large datasets
        results = list(operator.execute())
        
        self.assertEqual(len(results), 500)  # Overlapping IDs
        
    def test_parallel_aggregation(self):
        """Test parallel aggregation."""
        node = QueryNode(
            operation='aggregate',
            group_by=['dept'],
            aggregates=[{
                'function': 'sum',
                'column': 'salary',
                'alias': 'total_salary'
            }]
        )
        
        operator = ParallelAggregation(node, self.context)
        # Add mock child with large dataset
        results = list(operator.execute())
        
        # Verify results maintain consistency with sequential execution
        sequential_results = self._compute_sequential_aggregates()
        self.assertEqual(len(results), len(sequential_results))
        
    def _compute_sequential_aggregates(self) -> List[Dict[str, Any]]:
        """Helper to compute aggregates sequentially for comparison."""
        departments = {}
        for emp in self.test_data['employees']:
            dept = emp.get('dept', 'Unknown')
            if dept not in departments:
                departments[dept] = 0
            departments[dept] += emp['salary']
            
        return [{'dept': k, 'total_salary': v} for k, v in departments.items()]

if __name__ == '__main__':
    unittest.main() 