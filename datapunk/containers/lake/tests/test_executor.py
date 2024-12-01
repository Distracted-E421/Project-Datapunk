import unittest
from typing import Dict, List, Any
from ..src.query.executor.core import (
    ExecutionContext, ExecutionEngine, ExecutionOperator,
    TableScanOperator, FilterOperator, JoinOperator,
    ProjectOperator, AggregateOperator
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

class TestExecutionContext(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext()
        
    def test_variable_management(self):
        """Test context variable management."""
        self.context.set_variable('test_var', 42)
        self.assertEqual(self.context.get_variable('test_var'), 42)
        self.assertIsNone(self.context.get_variable('nonexistent'))
        
    def test_statistics_update(self):
        """Test statistics tracking."""
        self.context.update_statistics('rows_processed', 100)
        self.assertEqual(self.context.statistics['rows_processed'], 100)

class TestTableScanOperator(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            'test_table': [
                {'id': 1, 'name': 'Alice', 'age': 30},
                {'id': 2, 'name': 'Bob', 'age': 25},
            ]
        }
        self.cache_manager = MockCacheManager(self.test_data)
        
    def test_table_scan_with_cache(self):
        """Test table scan with cached data."""
        context = ExecutionContext()
        context.cache_manager = self.cache_manager
        
        node = QueryNode(operation='table_scan',
                        table_name='test_table',
                        columns=['id', 'name'])
                        
        operator = TableScanOperator(node, context)
        results = list(operator.execute())
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], 1)
        self.assertEqual(results[0]['name'], 'Alice')
        self.assertNotIn('age', results[0])

class TestFilterOperator(unittest.TestCase):
    def setUp(self):
        self.test_data = [
            {'id': 1, 'value': 10},
            {'id': 2, 'value': 20},
            {'id': 3, 'value': 30},
        ]
        
    def test_filter_greater_than(self):
        """Test filtering with greater than condition."""
        context = ExecutionContext()
        
        node = QueryNode(operation='filter',
                        predicate={'column': 'value', 'op': '>', 'value': 15})
                        
        class MockChildOperator(ExecutionOperator):
            def execute(self):
                return iter(self.context.get_variable('test_data'))
                
        operator = FilterOperator(node, context)
        child = MockChildOperator(QueryNode(operation='mock'), context)
        operator.add_child(child)
        
        context.set_variable('test_data', self.test_data)
        results = list(operator.execute())
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['value'] > 15 for r in results))

class TestJoinOperator(unittest.TestCase):
    def setUp(self):
        self.left_data = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'},
        ]
        self.right_data = [
            {'id': 1, 'age': 30},
            {'id': 2, 'age': 25},
        ]
        
    def test_inner_join(self):
        """Test inner join operation."""
        context = ExecutionContext()
        
        node = QueryNode(operation='join',
                        join_condition={'left': 'id', 'right': 'id'})
                        
        class MockLeftOperator(ExecutionOperator):
            def execute(self):
                return iter(self.context.get_variable('left_data'))
                
        class MockRightOperator(ExecutionOperator):
            def execute(self):
                return iter(self.context.get_variable('right_data'))
                
        operator = JoinOperator(node, context)
        operator.add_child(MockLeftOperator(QueryNode(operation='mock'), context))
        operator.add_child(MockRightOperator(QueryNode(operation='mock'), context))
        
        context.set_variable('left_data', self.left_data)
        context.set_variable('right_data', self.right_data)
        
        results = list(operator.execute())
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], 'Alice')
        self.assertEqual(results[0]['age'], 30)

class TestProjectOperator(unittest.TestCase):
    def setUp(self):
        self.test_data = [
            {'id': 1, 'name': 'Alice', 'age': 30, 'city': 'New York'},
            {'id': 2, 'name': 'Bob', 'age': 25, 'city': 'Boston'},
        ]
        
    def test_projection(self):
        """Test column projection."""
        context = ExecutionContext()
        
        node = QueryNode(operation='project',
                        columns=['name', 'age'])
                        
        class MockChildOperator(ExecutionOperator):
            def execute(self):
                return iter(self.context.get_variable('test_data'))
                
        operator = ProjectOperator(node, context)
        operator.add_child(MockChildOperator(QueryNode(operation='mock'), context))
        
        context.set_variable('test_data', self.test_data)
        results = list(operator.execute())
        
        self.assertEqual(len(results), 2)
        self.assertEqual(set(results[0].keys()), {'name', 'age'})
        self.assertNotIn('city', results[0])

class TestAggregateOperator(unittest.TestCase):
    def setUp(self):
        self.test_data = [
            {'category': 'A', 'value': 10},
            {'category': 'A', 'value': 20},
            {'category': 'B', 'value': 15},
            {'category': 'B', 'value': 25},
        ]
        
    def test_group_by_sum(self):
        """Test grouping and sum aggregation."""
        context = ExecutionContext()
        
        node = QueryNode(
            operation='aggregate',
            group_by=['category'],
            aggregates=[{
                'function': 'sum',
                'column': 'value',
                'alias': 'total'
            }]
        )
        
        class MockChildOperator(ExecutionOperator):
            def execute(self):
                return iter(self.context.get_variable('test_data'))
                
        operator = AggregateOperator(node, context)
        operator.add_child(MockChildOperator(QueryNode(operation='mock'), context))
        
        context.set_variable('test_data', self.test_data)
        results = list(operator.execute())
        
        self.assertEqual(len(results), 2)
        a_group = next(r for r in results if r['category'] == 'A')
        b_group = next(r for r in results if r['category'] == 'B')
        
        self.assertEqual(a_group['total'], 30)
        self.assertEqual(b_group['total'], 40)

class TestExecutionEngine(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            'employees': [
                {'id': 1, 'name': 'Alice', 'dept_id': 1},
                {'id': 2, 'name': 'Bob', 'dept_id': 1},
                {'id': 3, 'name': 'Charlie', 'dept_id': 2},
            ],
            'departments': [
                {'id': 1, 'name': 'Engineering'},
                {'id': 2, 'name': 'Sales'},
            ]
        }
        self.cache_manager = MockCacheManager(self.test_data)
        self.engine = ExecutionEngine(self.cache_manager)
        
    def test_complex_query_execution(self):
        """Test execution of a complex query plan."""
        # Build a plan: SELECT e.name, d.name 
        # FROM employees e JOIN departments d ON e.dept_id = d.id
        # WHERE e.id > 1
        
        # Project node
        root = QueryNode(operation='project',
                        columns=['e.name', 'd.name'])
                        
        # Join node
        join = QueryNode(operation='join',
                        join_condition={'left': 'dept_id', 'right': 'id'})
                        
        # Filter node
        filter_node = QueryNode(operation='filter',
                              predicate={'column': 'id', 'op': '>', 'value': 1})
                              
        # Table scan nodes
        employees_scan = QueryNode(operation='table_scan',
                                 table_name='employees',
                                 columns=['id', 'name', 'dept_id'])
                                 
        departments_scan = QueryNode(operation='table_scan',
                                   table_name='departments',
                                   columns=['id', 'name'])
                                   
        # Connect nodes
        filter_node.children = [employees_scan]
        join.children = [filter_node, departments_scan]
        root.children = [join]
        
        plan = QueryPlan(root)
        
        # Execute plan
        results = list(self.engine.execute_plan(plan))
        
        # Verify results
        self.assertEqual(len(results), 2)  # Bob and Charlie
        names = {r['e.name'] for r in results}
        self.assertEqual(names, {'Bob', 'Charlie'})

if __name__ == '__main__':
    unittest.main() 