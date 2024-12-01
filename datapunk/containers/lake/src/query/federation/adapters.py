from typing import Any, Dict, List, Set
from .core import DataSourceAdapter, QueryPlan
import sqlite3
import pymongo
import pandas as pd

class SQLiteAdapter(DataSourceAdapter):
    """Adapter for SQLite databases."""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.connection = sqlite3.connect(database_path)
        
    def get_capabilities(self) -> Set[str]:
        """Get SQLite capabilities."""
        return {
            'select', 'project', 'filter', 'join',
            'group', 'sort', 'limit', 'aggregate'
        }
        
    def estimate_cost(self, plan: QueryPlan) -> float:
        """Estimate query cost based on SQLite statistics."""
        # Get table statistics
        cursor = self.connection.cursor()
        stats = {}
        
        for table in self._extract_tables(plan):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
            
        # Simple cost model based on table sizes
        return sum(stats.values())
        
    def translate_plan(self, plan: QueryPlan) -> str:
        """Translate query plan to SQL."""
        return self._plan_to_sql(plan)
        
    def execute_plan(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        sql = self.translate_plan(plan)
        df = pd.read_sql_query(sql, self.connection)
        return df.to_dict('records')
        
    def _plan_to_sql(self, plan: QueryPlan) -> str:
        """Convert query plan to SQL string."""
        # Basic implementation - could be enhanced
        node = plan.root
        if node.operation == 'select':
            tables = self._extract_tables(plan)
            columns = node.columns if hasattr(node, 'columns') else ['*']
            where = node.condition if hasattr(node, 'condition') else ''
            
            sql = f"SELECT {', '.join(columns)} FROM {', '.join(tables)}"
            if where:
                sql += f" WHERE {where}"
                
            return sql
            
        raise NotImplementedError(f"Operation {node.operation} not supported")
        
    def _extract_tables(self, plan: QueryPlan) -> List[str]:
        """Extract table names from plan."""
        tables = []
        
        def extract(node):
            if hasattr(node, 'table'):
                tables.append(node.table)
            for child in node.children:
                extract(child)
                
        extract(plan.root)
        return tables

class MongoDBAdapter(DataSourceAdapter):
    """Adapter for MongoDB databases."""
    
    def __init__(self, connection_string: str, database: str):
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client[database]
        
    def get_capabilities(self) -> Set[str]:
        """Get MongoDB capabilities."""
        return {
            'find', 'aggregate', 'mapreduce', 'filter',
            'project', 'group', 'sort', 'limit'
        }
        
    def estimate_cost(self, plan: QueryPlan) -> float:
        """Estimate query cost based on MongoDB statistics."""
        # Get collection statistics
        stats = {}
        
        for collection in self._extract_collections(plan):
            stats[collection] = self.db[collection].estimated_document_count()
            
        # Simple cost model based on collection sizes
        return sum(stats.values())
        
    def translate_plan(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Translate query plan to MongoDB pipeline."""
        return self._plan_to_pipeline(plan)
        
    def execute_plan(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Execute MongoDB query."""
        pipeline = self.translate_plan(plan)
        collection = self._extract_collections(plan)[0]
        return list(self.db[collection].aggregate(pipeline))
        
    def _plan_to_pipeline(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Convert query plan to MongoDB pipeline."""
        pipeline = []
        node = plan.root
        
        if node.operation == 'find':
            if hasattr(node, 'filter'):
                pipeline.append({'$match': node.filter})
                
            if hasattr(node, 'projection'):
                pipeline.append({'$project': node.projection})
                
        elif node.operation == 'aggregate':
            if hasattr(node, 'group'):
                pipeline.append({'$group': node.group})
                
            if hasattr(node, 'sort'):
                pipeline.append({'$sort': node.sort})
                
        return pipeline
        
    def _extract_collections(self, plan: QueryPlan) -> List[str]:
        """Extract collection names from plan."""
        collections = []
        
        def extract(node):
            if hasattr(node, 'collection'):
                collections.append(node.collection)
            for child in node.children:
                extract(child)
                
        extract(plan.root)
        return collections

class PandasAdapter(DataSourceAdapter):
    """Adapter for Pandas DataFrames."""
    
    def __init__(self, dataframes: Dict[str, pd.DataFrame]):
        self.dataframes = dataframes
        
    def get_capabilities(self) -> Set[str]:
        """Get Pandas capabilities."""
        return {
            'select', 'filter', 'join', 'group',
            'sort', 'limit', 'aggregate', 'window'
        }
        
    def estimate_cost(self, plan: QueryPlan) -> float:
        """Estimate query cost based on DataFrame sizes."""
        stats = {}
        
        for name, df in self.dataframes.items():
            stats[name] = len(df)
            
        return sum(stats.values())
        
    def translate_plan(self, plan: QueryPlan) -> Dict[str, Any]:
        """Translate query plan to Pandas operations."""
        return self._plan_to_ops(plan)
        
    def execute_plan(self, plan: QueryPlan) -> pd.DataFrame:
        """Execute Pandas operations."""
        ops = self.translate_plan(plan)
        result = self._execute_ops(ops)
        return result.to_dict('records')
        
    def _plan_to_ops(self, plan: QueryPlan) -> Dict[str, Any]:
        """Convert query plan to Pandas operations."""
        ops = {'type': plan.root.operation}
        
        if plan.root.operation == 'select':
            if hasattr(plan.root, 'columns'):
                ops['columns'] = plan.root.columns
            if hasattr(plan.root, 'condition'):
                ops['condition'] = plan.root.condition
                
        elif plan.root.operation == 'join':
            ops.update({
                'left': plan.root.left_table,
                'right': plan.root.right_table,
                'how': plan.root.join_type,
                'on': plan.root.join_columns
            })
            
        return ops
        
    def _execute_ops(self, ops: Dict[str, Any]) -> pd.DataFrame:
        """Execute Pandas operations."""
        if ops['type'] == 'select':
            df = self.dataframes[ops.get('table', list(self.dataframes.keys())[0])]
            if 'columns' in ops:
                df = df[ops['columns']]
            if 'condition' in ops:
                df = df.query(ops['condition'])
            return df
            
        elif ops['type'] == 'join':
            left_df = self.dataframes[ops['left']]
            right_df = self.dataframes[ops['right']]
            return pd.merge(
                left_df,
                right_df,
                how=ops['how'],
                on=ops['on']
            )
            
        return pd.DataFrame() 