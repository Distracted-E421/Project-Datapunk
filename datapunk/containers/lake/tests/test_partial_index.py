import unittest
from datetime import datetime
from typing import Dict, Any
import threading
import random

from ..src.storage.index.partial import (
    Operator,
    SimpleCondition,
    CompositeCondition,
    ExpressionCondition,
    PartialIndex,
    PartialIndexMetadata,
    create_partial_index
)
from ..src.storage.index.core import IndexType

class TestSimpleCondition(unittest.TestCase):
    def test_equality_condition(self):
        condition = SimpleCondition("age", Operator.EQ, 30)
        
        # Test matching
        self.assertTrue(condition.evaluate({"age": 30}))
        self.assertFalse(condition.evaluate({"age": 25}))
        self.assertFalse(condition.evaluate({"name": "test"}))
        
    def test_comparison_conditions(self):
        conditions = [
            (SimpleCondition("age", Operator.LT, 30), {"age": 25}, True),
            (SimpleCondition("age", Operator.LT, 30), {"age": 35}, False),
            (SimpleCondition("age", Operator.LE, 30), {"age": 30}, True),
            (SimpleCondition("age", Operator.GT, 30), {"age": 35}, True),
            (SimpleCondition("age", Operator.GE, 30), {"age": 30}, True),
            (SimpleCondition("age", Operator.NE, 30), {"age": 25}, True)
        ]
        
        for condition, row, expected in conditions:
            self.assertEqual(condition.evaluate(row), expected)
            
    def test_null_conditions(self):
        conditions = [
            (SimpleCondition("status", Operator.IS_NULL, None), {"status": None}, True),
            (SimpleCondition("status", Operator.IS_NULL, None), {"status": "active"}, False),
            (SimpleCondition("status", Operator.IS_NOT_NULL, None), {"status": "active"}, True),
            (SimpleCondition("status", Operator.IS_NOT_NULL, None), {"status": None}, False)
        ]
        
        for condition, row, expected in conditions:
            self.assertEqual(condition.evaluate(row), expected)
            
    def test_in_conditions(self):
        condition = SimpleCondition("status", Operator.IN, ["active", "pending"])
        
        self.assertTrue(condition.evaluate({"status": "active"}))
        self.assertTrue(condition.evaluate({"status": "pending"}))
        self.assertFalse(condition.evaluate({"status": "inactive"}))
        
        # Test NOT IN
        condition = SimpleCondition("status", Operator.NOT_IN, ["active", "pending"])
        self.assertTrue(condition.evaluate({"status": "inactive"}))
        self.assertFalse(condition.evaluate({"status": "active"}))
        
    def test_like_conditions(self):
        conditions = [
            (SimpleCondition("name", Operator.LIKE, "test%"), {"name": "testing"}, True),
            (SimpleCondition("name", Operator.LIKE, "test%"), {"name": "best"}, False),
            (SimpleCondition("name", Operator.LIKE, "%ing"), {"name": "testing"}, True),
            (SimpleCondition("name", Operator.LIKE, "te_t"), {"name": "test"}, True),
            (SimpleCondition("name", Operator.NOT_LIKE, "test%"), {"name": "best"}, True)
        ]
        
        for condition, row, expected in conditions:
            self.assertEqual(condition.evaluate(row), expected)
            
    def test_between_condition(self):
        condition = SimpleCondition("age", Operator.BETWEEN, (20, 30))
        
        self.assertTrue(condition.evaluate({"age": 25}))
        self.assertTrue(condition.evaluate({"age": 20}))
        self.assertTrue(condition.evaluate({"age": 30}))
        self.assertFalse(condition.evaluate({"age": 15}))
        self.assertFalse(condition.evaluate({"age": 35}))
        
    def test_type_handling(self):
        # Test with incompatible types
        condition = SimpleCondition("age", Operator.LT, 30)
        self.assertFalse(condition.evaluate({"age": "not a number"}))
        
        # Test with missing column
        self.assertFalse(condition.evaluate({"name": "test"}))
        
        # Test with NULL value
        self.assertFalse(condition.evaluate({"age": None}))

class TestCompositeCondition(unittest.TestCase):
    def test_and_condition(self):
        condition = CompositeCondition(
            "AND",
            [
                SimpleCondition("age", Operator.GT, 30),
                SimpleCondition("status", Operator.EQ, "active")
            ]
        )
        
        # Test both conditions true
        self.assertTrue(condition.evaluate({"age": 35, "status": "active"}))
        
        # Test one condition false
        self.assertFalse(condition.evaluate({"age": 25, "status": "active"}))
        self.assertFalse(condition.evaluate({"age": 35, "status": "inactive"}))
        
        # Test both conditions false
        self.assertFalse(condition.evaluate({"age": 25, "status": "inactive"}))
        
    def test_or_condition(self):
        condition = CompositeCondition(
            "OR",
            [
                SimpleCondition("age", Operator.GT, 65),
                SimpleCondition("status", Operator.EQ, "premium")
            ]
        )
        
        # Test either condition true
        self.assertTrue(condition.evaluate({"age": 70, "status": "basic"}))
        self.assertTrue(condition.evaluate({"age": 30, "status": "premium"}))
        
        # Test both conditions true
        self.assertTrue(condition.evaluate({"age": 70, "status": "premium"}))
        
        # Test both conditions false
        self.assertFalse(condition.evaluate({"age": 30, "status": "basic"}))
        
    def test_nested_conditions(self):
        # (age > 30 AND status = 'active') OR (premium = true)
        condition = CompositeCondition(
            "OR",
            [
                CompositeCondition(
                    "AND",
                    [
                        SimpleCondition("age", Operator.GT, 30),
                        SimpleCondition("status", Operator.EQ, "active")
                    ]
                ),
                SimpleCondition("premium", Operator.EQ, True)
            ]
        )
        
        # Test nested AND true
        self.assertTrue(condition.evaluate({
            "age": 35,
            "status": "active",
            "premium": False
        }))
        
        # Test OR condition true
        self.assertTrue(condition.evaluate({
            "age": 25,
            "status": "inactive",
            "premium": True
        }))
        
        # Test all conditions false
        self.assertFalse(condition.evaluate({
            "age": 25,
            "status": "inactive",
            "premium": False
        }))
        
    def test_condition_string_representation(self):
        condition = CompositeCondition(
            "AND",
            [
                SimpleCondition("age", Operator.GT, 30),
                SimpleCondition("status", Operator.EQ, "active")
            ]
        )
        
        expected = "(age > 30) AND (status = active)"
        self.assertEqual(condition.to_string(), expected)

class TestExpressionCondition(unittest.TestCase):
    def test_simple_expression(self):
        condition = ExpressionCondition(
            "age > 30 and status == 'active'",
            ["age", "status"]
        )
        
        self.assertTrue(condition.evaluate({
            "age": 35,
            "status": "active"
        }))
        
        self.assertFalse(condition.evaluate({
            "age": 25,
            "status": "active"
        }))
        
    def test_arithmetic_expression(self):
        condition = ExpressionCondition(
            "price * quantity > 1000",
            ["price", "quantity"]
        )
        
        self.assertTrue(condition.evaluate({
            "price": 100,
            "quantity": 15
        }))
        
        self.assertFalse(condition.evaluate({
            "price": 50,
            "quantity": 10
        }))
        
    def test_missing_columns(self):
        condition = ExpressionCondition(
            "age > 30",
            ["age"]
        )
        
        self.assertFalse(condition.evaluate({"status": "active"}))
        
    def test_invalid_expression(self):
        condition = ExpressionCondition(
            "1/0",  # Division by zero
            []
        )
        
        self.assertFalse(condition.evaluate({}))
        
    def test_security(self):
        # Attempt to use built-in functions
        condition = ExpressionCondition(
            "__import__('os').system('echo hack')",
            []
        )
        
        self.assertFalse(condition.evaluate({}))

class TestPartialIndex(unittest.TestCase):
    def setUp(self):
        # Create a partial index with composite condition
        self.condition = CompositeCondition(
            "AND",
            [
                SimpleCondition("status", Operator.EQ, "active"),
                SimpleCondition("age", Operator.GT, 30)
            ]
        )
        
        self.index = create_partial_index(
            name="active_adult_users",
            table_name="users",
            columns=["id"],
            condition=self.condition,
            base_index_type=IndexType.BTREE
        )
        
        # Add test data
        self.test_data = [
            (1, "user1", {"id": 1, "status": "active", "age": 35}),
            (2, "user2", {"id": 2, "status": "active", "age": 25}),
            (3, "user3", {"id": 3, "status": "inactive", "age": 40}),
            (4, "user4", {"id": 4, "status": "active", "age": 45}),
            (5, "user5", {"id": 5, "status": "active", "age": 20})
        ]
        
        for id, name, row in self.test_data:
            self.index.insert(id, name, row)
            
    def test_reindex(self):
        # Initial state
        self.assertEqual(self.index.included_count, 2)  # Users 1 and 4
        
        # Modify some data
        modified_data = [
            (1, "user1", {"id": 1, "status": "inactive", "age": 35}),  # Now inactive
            (2, "user2", {"id": 2, "status": "active", "age": 35}),   # Now matches
            (3, "user3", {"id": 3, "status": "active", "age": 40}),   # Now matches
        ]
        
        # Reindex
        self.index.reindex(lambda: modified_data)
        
        # Verify new state
        self.assertEqual(self.index.included_count, 2)  # Users 2 and 3
        metadata = self.index.get_partial_metadata()
        self.assertIsNotNone(metadata.last_reindex)
        
    def test_performance_metrics(self):
        # Perform some operations
        for _ in range(10):
            self.index.search(None, {"status": "active", "age": 35})
            self.index.search(None, {"status": "inactive", "age": 25})
            
        metadata = self.index.get_partial_metadata()
        
        # Verify metrics
        self.assertTrue(metadata.avg_condition_evaluation_time > 0)
        self.assertTrue(0 <= metadata.false_positive_rate <= 1)
        
    def test_dict_condition_creation(self):
        # Create index using dict condition
        dict_condition = {
            "column": "status",
            "operator": "=",
            "value": "active"
        }
        
        index = create_partial_index(
            name="dict_condition_index",
            table_name="users",
            columns=["id"],
            condition=dict_condition,
            base_index_type=IndexType.BTREE
        )
        
        # Test the condition works
        self.assertTrue(index.condition.evaluate({"status": "active"}))
        self.assertFalse(index.condition.evaluate({"status": "inactive"})) 