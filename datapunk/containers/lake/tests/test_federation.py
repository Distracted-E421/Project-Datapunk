import unittest
from typing import Dict, List, Any, Set
import asyncio
from ..src.query.federation.fed_planner import (
    DataSource, DataSourceType, SubQuery, DistributedQueryPlanner
)
from ..src.query.federation.query_fed_executor import (
    FederatedQueryExecutor, QueryResult
)
from ..src.query.parser.query_parser_core import QueryNode, QueryType
from ..src.query.executor.query_exec_core import QueryExecutor

class MockQueryExecutor(QueryExecutor):
    """Mock executor for testing."""
    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self.executed_queries = []
        
    def execute(self, query: QueryNode) -> List[Dict[str, Any]]:
        self.executed_queries.append(query)
        return self.results

class TestDistributedQueryPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = DistributedQueryPlanner()
        
        # Set up test data sources
        self.sql_source = DataSource(
            name="sql_db",
            type=DataSourceType.RELATIONAL,
            capabilities={"select", "join", "group", "order"},
            cost_factors={"select": 1.0, "join": 2.0},
            statistics={"data_size": 1000000}
        )
        
        self.doc_source = DataSource(
            name="mongo_db",
            type=DataSourceType.DOCUMENT,
            capabilities={"select", "text_search"},
            cost_factors={"select": 1.5, "text_search": 2.0},
            statistics={"data_size": 500000}
        )
        
        self.planner.register_data_source(self.sql_source)
        self.planner.register_data_source(self.doc_source)
        
    def test_analyze_requirements(self):
        query = QueryNode(
            query_type=QueryType.SELECT,
            tables=["users"],
            conditions=[{"op": "like", "value": "%test%"}],
            joins=["orders"],
            group_by=["status"]
        )
        
        requirements = self.planner._analyze_requirements(query)
        
        self.assertIn("select", requirements)
        self.assertIn("join", requirements)
        self.assertIn("group", requirements)
        self.assertIn("text_search", requirements)
        
    def test_find_capable_sources(self):
        requirements = {"select", "join"}
        sources = self.planner._find_capable_sources(requirements)
        
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].name, "sql_db")
        
    def test_split_query(self):
        query = QueryNode(
            query_type=QueryType.SELECT,
            tables=["users", "orders"],
            conditions=[]
        )
        
        sub_queries = self.planner._split_query(
            query, [self.sql_source])
            
        self.assertEqual(len(sub_queries), 1)
        self.assertEqual(sub_queries[0].source.name, "sql_db")
        
    def test_cost_estimation(self):
        query = QueryNode(
            query_type=QueryType.SELECT,
            tables=["users"],
            conditions=[]
        )
        
        sub_query = SubQuery(
            source=self.sql_source,
            query=query,
            estimated_cost=0.0,
            dependencies=[],
            result_size=0
        )
        
        cost = self.planner._estimate_cost(sub_query)
        self.assertGreater(cost, 0)
        
class TestFederatedQueryExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = FederatedQueryExecutor(max_workers=2)
        
        # Set up test data sources and executors
        self.sql_source = DataSource(
            name="sql_db",
            type=DataSourceType.RELATIONAL,
            capabilities={"select"},
            cost_factors={},
            statistics={}
        )
        
        self.sql_executor = MockQueryExecutor([
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"}
        ])
        
        self.executor.register_executor("sql_db", self.sql_executor)
        
    def test_group_by_level(self):
        # Create test plan with dependencies
        query1 = SubQuery(
            source=self.sql_source,
            query=QueryNode(query_type=QueryType.SELECT, tables=["table1"]),
            estimated_cost=1.0,
            dependencies=[],
            result_size=100
        )
        
        query2 = SubQuery(
            source=self.sql_source,
            query=QueryNode(query_type=QueryType.SELECT, tables=["table2"]),
            estimated_cost=1.0,
            dependencies=[query1],
            result_size=50
        )
        
        plan = [query1, query2]
        levels = self.executor._group_by_level(plan)
        
        self.assertEqual(len(levels), 2)
        self.assertEqual(len(levels[0]), 1)  # First level: independent query
        self.assertEqual(len(levels[1]), 1)  # Second level: dependent query
        
    async def test_execute_plan(self):
        # Create simple test plan
        query = SubQuery(
            source=self.sql_source,
            query=QueryNode(query_type=QueryType.SELECT, tables=["users"]),
            estimated_cost=1.0,
            dependencies=[],
            result_size=100
        )
        
        results = [r async for r in await self.executor.execute_plan([query])]
        
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].data), 2)  # Two test records
        self.assertFalse(results[0].error)
        
    def test_execute_single_query(self):
        query = SubQuery(
            source=self.sql_source,
            query=QueryNode(query_type=QueryType.SELECT, tables=["users"]),
            estimated_cost=1.0,
            dependencies=[],
            result_size=100
        )
        
        result = self.executor._execute_single_query(query)
        
        self.assertEqual(len(result.data), 2)  # Two test records
        self.assertFalse(result.error)
        self.assertFalse(result.metadata["cached"])
        
    def test_error_handling(self):
        # Register executor that raises an exception
        def failing_execute(*args):
            raise Exception("Test error")
            
        self.sql_executor.execute = failing_execute
        
        query = SubQuery(
            source=self.sql_source,
            query=QueryNode(query_type=QueryType.SELECT, tables=["users"]),
            estimated_cost=1.0,
            dependencies=[],
            result_size=100
        )
        
        result = self.executor._execute_single_query(query)
        
        self.assertTrue(result.error)
        self.assertEqual(len(result.data), 0)
        
def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
    return wrapper
    
if __name__ == '__main__':
    unittest.main() 