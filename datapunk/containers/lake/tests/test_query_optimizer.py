import unittest
from typing import List
from ..src.query.optimizer.optimizer_core import QueryOptimizer, CostBasedOptimizer, OptimizationRule
from ..src.query.optimizer.optimizer_rules import PushDownPredicates, JoinReordering, ColumnPruning
from ..src.query.parser.query_parser_core import QueryPlan, QueryNode

class MockRule(OptimizationRule):
    """Mock optimization rule for testing."""
    def __init__(self, cost_reduction: float = 0.5):
        self.cost_reduction = cost_reduction
        self.apply_called = False
        
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        self.apply_called = True
        return query_plan
        
    def estimate_cost(self, query_plan: QueryPlan) -> float:
        return 100.0 * self.cost_reduction

class TestQueryOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = QueryOptimizer()
        self.test_plan = self._create_test_plan()
        
    def _create_test_plan(self) -> QueryPlan:
        """Create a test query plan for optimization."""
        # Create a simple plan: SELECT col1, col2 FROM table WHERE col1 > 10
        root = QueryNode(operation='project', columns=['col1', 'col2'])
        filter_node = QueryNode(operation='filter', 
                              predicate={'column': 'col1', 'op': '>', 'value': 10})
        table_node = QueryNode(operation='table_scan', 
                             table_name='test_table',
                             columns=['col1', 'col2', 'col3'])
        
        filter_node.children = [table_node]
        root.children = [filter_node]
        
        return QueryPlan(root)
        
    def test_add_rule(self):
        """Test adding optimization rules."""
        rule = MockRule()
        self.optimizer.add_rule(rule)
        self.assertEqual(len(self.optimizer.rules), 1)
        self.assertIs(self.optimizer.rules[0], rule)
        
    def test_optimize_applies_rules(self):
        """Test that optimization applies all rules."""
        rules = [MockRule(0.8), MockRule(0.6), MockRule(0.7)]
        for rule in rules:
            self.optimizer.add_rule(rule)
            
        self.optimizer.optimize(self.test_plan)
        
        for rule in rules:
            self.assertTrue(rule.apply_called)
            
    def test_statistics_cache(self):
        """Test statistics cache operations."""
        stats = {'row_count': 1000, 'avg_row_size': 100}
        self.optimizer.update_statistics('test_table', stats)
        
        retrieved_stats = self.optimizer.get_statistics('test_table')
        self.assertEqual(retrieved_stats, stats)
        
        # Test non-existent table
        self.assertIsNone(self.optimizer.get_statistics('nonexistent_table'))

class TestCostBasedOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = CostBasedOptimizer()
        self.test_plan = self._create_complex_test_plan()
        
    def _create_complex_test_plan(self) -> QueryPlan:
        """Create a complex test plan with joins."""
        # SELECT t1.col1, t2.col2 
        # FROM table1 t1 
        # JOIN table2 t2 ON t1.id = t2.id 
        # WHERE t1.col1 > 10
        
        root = QueryNode(operation='project', 
                        columns=['t1.col1', 't2.col2'])
        
        join_node = QueryNode(operation='join',
                            join_condition={'left': 't1.id', 'right': 't2.id'})
        
        filter_node = QueryNode(operation='filter',
                              predicate={'column': 't1.col1', 'op': '>', 'value': 10})
        
        table1_node = QueryNode(operation='table_scan',
                              table_name='table1',
                              columns=['id', 'col1'])
        
        table2_node = QueryNode(operation='table_scan',
                              table_name='table2',
                              columns=['id', 'col2'])
        
        filter_node.children = [table1_node]
        join_node.children = [filter_node, table2_node]
        root.children = [join_node]
        
        return QueryPlan(root)
        
    def test_cost_threshold(self):
        """Test cost threshold behavior."""
        self.optimizer.set_cost_threshold(50.0)
        rule1 = MockRule(0.9)  # Small improvement
        rule2 = MockRule(0.4)  # Large improvement
        
        self.optimizer.add_rule(rule1)
        self.optimizer.add_rule(rule2)
        
        self.optimizer.optimize(self.test_plan)
        
        # Only rule2 should have been applied due to threshold
        self.assertFalse(rule1.apply_called)
        self.assertTrue(rule2.apply_called)

class TestOptimizationRules(unittest.TestCase):
    def setUp(self):
        self.test_plan = self._create_test_plan()
        
    def _create_test_plan(self) -> QueryPlan:
        """Create a test plan with multiple optimization opportunities."""
        # SELECT t1.col1, t2.col2 
        # FROM table1 t1 
        # JOIN table2 t2 ON t1.id = t2.id 
        # JOIN table3 t3 ON t2.id = t3.id
        # WHERE t1.col1 > 10 AND t2.col2 < 20
        
        root = QueryNode(operation='project',
                        columns=['t1.col1', 't2.col2'])
        
        filter1 = QueryNode(operation='filter',
                          predicate={'column': 't1.col1', 'op': '>', 'value': 10})
        
        filter2 = QueryNode(operation='filter',
                          predicate={'column': 't2.col2', 'op': '<', 'value': 20})
        
        join1 = QueryNode(operation='join',
                         join_condition={'left': 't1.id', 'right': 't2.id'})
        
        join2 = QueryNode(operation='join',
                         join_condition={'left': 't2.id', 'right': 't3.id'})
        
        table1 = QueryNode(operation='table_scan',
                          table_name='table1',
                          columns=['id', 'col1', 'col2'])
        
        table2 = QueryNode(operation='table_scan',
                          table_name='table2',
                          columns=['id', 'col1', 'col2'])
        
        table3 = QueryNode(operation='table_scan',
                          table_name='table3',
                          columns=['id', 'col1', 'col2'])
        
        filter1.children = [table1]
        filter2.children = [table2]
        join1.children = [filter1, filter2]
        join2.children = [join1, table3]
        root.children = [join2]
        
        return QueryPlan(root)
        
    def test_push_down_predicates(self):
        """Test predicate push-down optimization."""
        rule = PushDownPredicates()
        optimized_plan = rule.apply(self.test_plan)
        
        # Verify predicates were pushed down
        def find_filter_nodes(node: QueryNode) -> List[QueryNode]:
            filters = []
            if node.operation == 'filter':
                filters.append(node)
            for child in node.children:
                filters.extend(find_filter_nodes(child))
            return filters
            
        original_filters = find_filter_nodes(self.test_plan.root)
        optimized_filters = find_filter_nodes(optimized_plan.root)
        
        self.assertLess(len(optimized_filters), len(original_filters))
        
    def test_join_reordering(self):
        """Test join reordering optimization."""
        rule = JoinReordering()
        optimized_plan = rule.apply(self.test_plan)
        
        # Verify join order was changed
        def count_joins(node: QueryNode) -> int:
            if not node.children:
                return 0
            return sum(1 for child in node.children if child.operation == 'join')
            
        original_joins = count_joins(self.test_plan.root)
        optimized_joins = count_joins(optimized_plan.root)
        
        self.assertEqual(original_joins, optimized_joins)
        
    def test_column_pruning(self):
        """Test column pruning optimization."""
        rule = ColumnPruning()
        optimized_plan = rule.apply(self.test_plan)
        
        # Verify unused columns were removed
        def count_columns(node: QueryNode) -> int:
            if not node.children:
                return len(node.columns)
            return sum(count_columns(child) for child in node.children)
            
        original_columns = count_columns(self.test_plan.root)
        optimized_columns = count_columns(optimized_plan.root)
        
        self.assertLess(optimized_columns, original_columns)

if __name__ == '__main__':
    unittest.main() 