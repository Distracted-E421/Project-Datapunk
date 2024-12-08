import unittest
from typing import Dict, Any
from ..src.query.parser.query_parser_sql_advanced import (
    AdvancedSQLParser, WindowFrame, WindowFrameType, WindowSpec
)
from ..src.query.parser.query_parser_nosql_advanced import (
    AdvancedNoSQLParser, AggregationStage, GeoPoint, GeoShape
)

class TestAdvancedSQLParser(unittest.TestCase):
    def setUp(self):
        self.parser = AdvancedSQLParser()
        
    def test_cte_query(self):
        """Test parsing Common Table Expression queries."""
        query = """
        WITH revenue AS (
            SELECT department_id, SUM(amount) as total_revenue
            FROM sales
            GROUP BY department_id
        )
        SELECT d.name, r.total_revenue
        FROM departments d
        JOIN revenue r ON d.id = r.department_id
        """
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'project')
        join_node = plan.root.children[0]
        self.assertEqual(join_node.operation, 'join')
        
    def test_set_operations(self):
        """Test parsing set operation queries."""
        query = """
        SELECT name FROM employees
        UNION
        SELECT name FROM contractors
        """
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'union')
        self.assertEqual(len(plan.root.children), 2)
        
    def test_merge_statement(self):
        """Test parsing MERGE statements."""
        query = """
        MERGE INTO customers c
        USING new_customers n
        ON c.id = n.id
        WHEN MATCHED THEN
            UPDATE SET name = n.name
        WHEN NOT MATCHED THEN
            INSERT (id, name) VALUES (n.id, n.name)
        """
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'merge')
        self.assertEqual(plan.root.target_table, 'customers')
        
    def test_window_function(self):
        """Test parsing window function expressions."""
        expr = """
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC
            ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
        )
        """
        
        result = self.parser.parse_window_function(expr)
        
        self.assertEqual(result['function'].strip(), 'ROW_NUMBER()')
        self.assertIsInstance(result['window'], WindowSpec)
        self.assertIsInstance(result['window'].frame, WindowFrame)
        
    def test_complex_subquery(self):
        """Test parsing complex subqueries."""
        query = """
        SELECT name
        FROM employees e
        WHERE salary > (
            SELECT AVG(salary)
            FROM employees
            WHERE department_id = e.department_id
        )
        """
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'project')
        filter_node = plan.root.children[0]
        self.assertEqual(filter_node.operation, 'filter')
        subquery = filter_node.conditions['subquery']
        self.assertEqual(subquery.operation, 'scalar_subquery')

class TestAdvancedNoSQLParser(unittest.TestCase):
    def setUp(self):
        self.parser = AdvancedNoSQLParser()
        
    def test_aggregation_pipeline(self):
        """Test parsing aggregation pipeline queries."""
        query = {
            'pipeline': [
                {'$match': {'status': 'active'}},
                {'$group': {
                    '_id': '$department',
                    'total_salary': {'$sum': '$salary'}
                }},
                {'$sort': {'total_salary': -1}}
            ]
        }
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'sort')
        group_node = plan.root.children[0]
        self.assertEqual(group_node.operation, 'aggregate')
        match_node = group_node.children[0]
        self.assertEqual(match_node.operation, 'filter')
        
    def test_graph_traversal(self):
        """Test parsing graph traversal queries."""
        query = {
            'start': {
                'collection': 'users',
                'conditions': {'name': 'Alice'}
            },
            'traversal': [
                {
                    'edge_collection': 'friendships',
                    'direction': 'outbound',
                    'depth': 2
                }
            ]
        }
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'graph_lookup')
        traverse_node = plan.root.children[0]
        self.assertEqual(traverse_node.operation, 'graph_traverse')
        self.assertEqual(traverse_node.depth, 2)
        
    def test_geospatial_query(self):
        """Test parsing geospatial queries."""
        query = {
            'geometry': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [-73.9667, 40.78]
                    },
                    '$maxDistance': 1000
                }
            }
        }
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'geo_near')
        self.assertIsInstance(plan.root.near, GeoPoint)
        self.assertEqual(plan.root.max_distance, 1000)
        
    def test_text_search(self):
        """Test parsing text search queries."""
        query = {
            '$text': {
                '$search': 'coffee shop',
                '$language': 'english',
                '$caseSensitive': False
            }
        }
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'text_search')
        self.assertEqual(plan.root.search_text, 'coffee shop')
        self.assertEqual(plan.root.language, 'english')
        
    def test_complex_aggregation(self):
        """Test parsing complex aggregation pipelines."""
        query = {
            'pipeline': [
                {'$match': {'type': 'restaurant'}},
                {'$geoNear': {
                    'near': {'type': 'Point', 'coordinates': [-73.9667, 40.78]},
                    'distanceField': 'distance',
                    'maxDistance': 1000,
                    'spherical': True
                }},
                {'$lookup': {
                    'from': 'reviews',
                    'localField': '_id',
                    'foreignField': 'restaurant_id',
                    'as': 'reviews'
                }},
                {'$unwind': '$reviews'},
                {'$group': {
                    '_id': '$_id',
                    'avg_rating': {'$avg': '$reviews.rating'},
                    'review_count': {'$sum': 1}
                }},
                {'$sort': {'avg_rating': -1}},
                {'$limit': 10}
            ]
        }
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'limit')
        sort_node = plan.root.children[0]
        self.assertEqual(sort_node.operation, 'sort')
        group_node = sort_node.children[0]
        self.assertEqual(group_node.operation, 'aggregate')
        
    def test_faceted_aggregation(self):
        """Test parsing faceted aggregation queries."""
        query = {
            'pipeline': [
                {'$facet': {
                    'categorized': [
                        {'$group': {
                            '_id': '$category',
                            'count': {'$sum': 1}
                        }}
                    ],
                    'priced': [
                        {'$group': {
                            '_id': '$price_range',
                            'count': {'$sum': 1}
                        }}
                    ]
                }}
            ]
        }
        
        plan = self.parser.parse_query(query)
        
        self.assertEqual(plan.root.operation, 'facet')
        self.assertIn('categorized', plan.root.facets)
        self.assertIn('priced', plan.root.facets)

if __name__ == '__main__':
    unittest.main() 