from typing import Any, Dict, List, Set, Tuple
from dataclasses import dataclass
from .core import QueryPlan, QueryNode

@dataclass
class SplitCost:
    """Cost information for a query split."""
    execution_cost: float
    transfer_cost: float
    total_cost: float

@dataclass
class SplitPoint:
    """Represents a point where a query can be split."""
    node: QueryNode
    parent: QueryNode
    source: str
    cost: SplitCost

class QuerySplitter:
    """Advanced query splitting system."""
    
    def __init__(self):
        self.cost_weights = {
            'execution': 0.7,
            'transfer': 0.3
        }
        
    def find_split_points(
        self, 
        plan: QueryPlan,
        source_capabilities: Dict[str, Set[str]]
    ) -> List[SplitPoint]:
        """Find all possible split points in a query plan."""
        split_points = []
        
        def traverse(node: QueryNode, parent: QueryNode = None):
            # Check each source's capability to handle this node
            for source, capabilities in source_capabilities.items():
                if node.operation in capabilities:
                    # Calculate costs
                    exec_cost = self._estimate_execution_cost(node, source)
                    transfer_cost = self._estimate_transfer_cost(node)
                    total_cost = (
                        self.cost_weights['execution'] * exec_cost +
                        self.cost_weights['transfer'] * transfer_cost
                    )
                    
                    cost = SplitCost(exec_cost, transfer_cost, total_cost)
                    
                    split_points.append(SplitPoint(
                        node=node,
                        parent=parent,
                        source=source,
                        cost=cost
                    ))
                    
            # Recurse into children
            for child in node.children:
                traverse(child, node)
                
        traverse(plan.root)
        return split_points
        
    def split_plan(
        self,
        plan: QueryPlan,
        source_capabilities: Dict[str, Set[str]]
    ) -> Dict[str, QueryPlan]:
        """Split a query plan optimally among data sources."""
        # Find all possible split points
        split_points = self.find_split_points(plan, source_capabilities)
        
        # Group split points by source
        source_splits = self._group_splits_by_source(split_points)
        
        # Find optimal splits using dynamic programming
        optimal_splits = self._find_optimal_splits(
            plan.root,
            source_splits
        )
        
        # Create subplans from optimal splits
        return self._create_subplans(optimal_splits)
        
    def _estimate_execution_cost(
        self,
        node: QueryNode,
        source: str
    ) -> float:
        """Estimate cost of executing a node on a source."""
        # Basic cost model based on operation type
        base_costs = {
            'select': 1.0,
            'project': 1.0,
            'filter': 1.2,
            'join': 2.0,
            'aggregate': 1.5,
            'sort': 1.3,
            'limit': 1.0
        }
        
        cost = base_costs.get(node.operation, 1.0)
        
        # Adjust for data size if available
        if hasattr(node, 'data_size'):
            cost *= node.data_size
            
        return cost
        
    def _estimate_transfer_cost(self, node: QueryNode) -> float:
        """Estimate cost of transferring data between sources."""
        # Basic cost model based on result size
        if hasattr(node, 'result_size'):
            return node.result_size
            
        # Default cost based on operation type
        transfer_costs = {
            'select': 1.0,
            'project': 0.8,
            'filter': 0.6,
            'join': 1.5,
            'aggregate': 0.4
        }
        
        return transfer_costs.get(node.operation, 1.0)
        
    def _group_splits_by_source(
        self,
        split_points: List[SplitPoint]
    ) -> Dict[str, List[SplitPoint]]:
        """Group split points by data source."""
        grouped = {}
        for split in split_points:
            if split.source not in grouped:
                grouped[split.source] = []
            grouped[split.source].append(split)
        return grouped
        
    def _find_optimal_splits(
        self,
        root: QueryNode,
        source_splits: Dict[str, List[SplitPoint]]
    ) -> Dict[str, List[QueryNode]]:
        """Find optimal split points using dynamic programming."""
        # Initialize DP table
        dp: Dict[Tuple[QueryNode, str], float] = {}
        choices: Dict[Tuple[QueryNode, str], str] = {}
        
        def get_cost(node: QueryNode, source: str) -> float:
            key = (node, source)
            if key in dp:
                return dp[key]
                
            # Find split points for this node
            node_splits = [
                s for s in source_splits.get(source, [])
                if s.node == node
            ]
            
            if not node_splits:
                return float('inf')
                
            # Calculate minimum cost including children
            min_cost = float('inf')
            best_source = None
            
            for split in node_splits:
                cost = split.cost.total_cost
                
                # Add costs from children
                for child in node.children:
                    child_costs = [
                        get_cost(child, s)
                        for s in source_splits.keys()
                    ]
                    cost += min(child_costs)
                    
                if cost < min_cost:
                    min_cost = cost
                    best_source = source
                    
            dp[key] = min_cost
            choices[key] = best_source
            return min_cost
            
        # Calculate optimal splits
        source_costs = [
            get_cost(root, source)
            for source in source_splits.keys()
        ]
        best_cost = min(source_costs)
        best_source = list(source_splits.keys())[
            source_costs.index(best_cost)
        ]
        
        # Build result from choices
        result = {source: [] for source in source_splits.keys()}
        
        def assign_nodes(node: QueryNode, source: str):
            result[source].append(node)
            for child in node.children:
                child_source = choices.get((child, source), source)
                assign_nodes(child, child_source)
                
        assign_nodes(root, best_source)
        return result
        
    def _create_subplans(
        self,
        splits: Dict[str, List[QueryNode]]
    ) -> Dict[str, QueryPlan]:
        """Create query subplans from split points."""
        subplans = {}
        
        for source, nodes in splits.items():
            if not nodes:
                continue
                
            # Create a new plan for each source
            root = nodes[0]
            subplans[source] = QueryPlan(root)
            
        return subplans 