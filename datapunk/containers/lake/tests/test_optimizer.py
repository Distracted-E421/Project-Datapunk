import unittest
from typing import Dict, Any

from ..src.storage.index.optimizer import ConditionOptimizer
from ..src.storage.index.partial import (
    SimpleCondition,
    CompositeCondition,
    ExpressionCondition,
    Operator
)

class TestConditionOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = ConditionOptimizer()
        
    def test_remove_redundant(self):
        # Create condition with duplicates
        condition = CompositeCondition(
            "AND",
            [
                SimpleCondition("age", Operator.GT, 30),
                SimpleCondition("age", Operator.GT, 30),  # Duplicate
                SimpleCondition("status", Operator.EQ, "active")
            ]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        self.assertEqual(stats.removed_redundant, 1)
        self.assertEqual(len(optimized.conditions), 2)
        
    def test_remove_tautology(self):
        # Create condition with tautology
        condition = CompositeCondition(
            "AND",
            [
                SimpleCondition("status", Operator.EQ, "status"),  # Tautology
                SimpleCondition("age", Operator.GT, 30)
            ]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        self.assertEqual(stats.removed_redundant, 1)
        self.assertIsInstance(optimized, SimpleCondition)
        
    def test_simplify_expression(self):
        # Create expression that can be simplified
        condition = ExpressionCondition(
            "age > 30",
            ["age"]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        self.assertEqual(stats.simplified_expressions, 1)
        self.assertIsInstance(optimized, SimpleCondition)
        self.assertEqual(optimized.operator, Operator.GT)
        
    def test_merge_range_conditions(self):
        # Create conditions that can be merged
        condition = CompositeCondition(
            "AND",
            [
                SimpleCondition("age", Operator.GT, 30),
                SimpleCondition("age", Operator.LT, 50)
            ]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        self.assertEqual(stats.merged_conditions, 1)
        self.assertIsInstance(optimized, SimpleCondition)
        self.assertEqual(optimized.operator, Operator.BETWEEN)
        
    def test_merge_in_conditions(self):
        # Create conditions that can be merged
        condition = CompositeCondition(
            "AND",
            [
                SimpleCondition("status", Operator.EQ, "active"),
                SimpleCondition("status", Operator.IN, ["active", "pending"])
            ]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        self.assertEqual(stats.merged_conditions, 1)
        self.assertIsInstance(optimized, SimpleCondition)
        self.assertEqual(optimized.operator, Operator.EQ)
        
    def test_reorder_conditions(self):
        # Create conditions that should be reordered
        condition = CompositeCondition(
            "AND",
            [
                ExpressionCondition("price * quantity > 1000", ["price", "quantity"]),
                SimpleCondition("status", Operator.EQ, "active"),  # More selective
                CompositeCondition(
                    "OR",
                    [
                        SimpleCondition("type", Operator.EQ, "premium"),
                        SimpleCondition("type", Operator.EQ, "basic")
                    ]
                )
            ]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        conditions = optimized.conditions
        
        # Check that simple condition is first
        self.assertIsInstance(conditions[0], SimpleCondition)
        self.assertEqual(conditions[0].operator, Operator.EQ)
        
        # Check that expression is last
        self.assertIsInstance(conditions[-1], ExpressionCondition)
        
    def test_complex_optimization(self):
        # Create a complex condition
        condition = CompositeCondition(
            "AND",
            [
                SimpleCondition("age", Operator.GT, 30),
                SimpleCondition("age", Operator.LT, 50),
                SimpleCondition("status", Operator.EQ, "active"),
                SimpleCondition("status", Operator.EQ, "active"),  # Duplicate
                ExpressionCondition("age > 30", ["age"]),  # Redundant
                CompositeCondition(
                    "OR",
                    [
                        SimpleCondition("type", Operator.EQ, "premium"),
                        SimpleCondition("type", Operator.EQ, "premium")  # Duplicate
                    ]
                )
            ]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        
        # Verify optimizations
        self.assertTrue(stats.removed_redundant > 0)
        self.assertTrue(stats.simplified_expressions > 0)
        self.assertTrue(stats.merged_conditions > 0)
        self.assertTrue(stats.optimized_depth < stats.original_depth)
        
    def test_selectivity_estimation(self):
        conditions = [
            (SimpleCondition("id", Operator.EQ, 1), 0.1),  # Very selective
            (SimpleCondition("status", Operator.IN, ["a", "b"]), 0.3),  # Moderate
            (SimpleCondition("age", Operator.GT, 30), 0.5),  # Less selective
            (SimpleCondition("name", Operator.LIKE, "test%"), 0.7),  # Expensive
            (ExpressionCondition("price * qty > 1000", ["price", "qty"]), 0.8)  # Complex
        ]
        
        for condition, expected in conditions:
            selectivity = self.optimizer._estimate_selectivity(condition)
            self.assertEqual(selectivity, expected)
            
    def test_nested_optimization(self):
        # Create deeply nested condition
        condition = CompositeCondition(
            "OR",
            [
                CompositeCondition(
                    "AND",
                    [
                        SimpleCondition("age", Operator.GT, 30),
                        SimpleCondition("age", Operator.LT, 50),
                        SimpleCondition("status", Operator.EQ, "active")
                    ]
                ),
                CompositeCondition(
                    "AND",
                    [
                        SimpleCondition("premium", Operator.EQ, True),
                        ExpressionCondition("age >= 18", ["age"])
                    ]
                )
            ]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        
        # Verify the structure is simplified
        self.assertTrue(stats.optimized_depth < stats.original_depth)
        self.assertTrue(stats.simplified_expressions > 0)
        
    def test_invalid_conditions(self):
        # Test with invalid expression
        condition = ExpressionCondition(
            "invalid syntax >>>",
            ["column"]
        )
        
        optimized, stats = self.optimizer.optimize(condition)
        self.assertEqual(optimized, condition)  # Should return original
        
        # Test with empty composite
        condition = CompositeCondition("AND", [])
        optimized, stats = self.optimizer.optimize(condition)
        self.assertEqual(optimized, condition)
        
    def test_optimization_idempotency(self):
        # Create a condition that's already optimal
        condition = SimpleCondition("status", Operator.EQ, "active")
        
        # Optimize multiple times
        optimized1, stats1 = self.optimizer.optimize(condition)
        optimized2, stats2 = self.optimizer.optimize(optimized1)
        
        # Should be identical
        self.assertEqual(optimized1.to_string(), optimized2.to_string())
        self.assertEqual(stats2.removed_redundant, 0)
        self.assertEqual(stats2.simplified_expressions, 0)
        self.assertEqual(stats2.merged_conditions, 0) 