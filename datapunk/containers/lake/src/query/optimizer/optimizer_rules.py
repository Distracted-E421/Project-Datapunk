from typing import List, Optional, Set
from .optimizer_core import OptimizationRule
from ..parser.query_parser_core import QueryPlan, QueryNode

class PushDownPredicates(OptimizationRule):
    """Optimization rule that pushes predicates down the query tree."""
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Push predicates as close to the leaf nodes as possible."""
        def push_predicate(node: QueryNode) -> QueryNode:
            if not node.children:
                return node
                
            # Recursively process children
            node.children = [push_predicate(child) for child in node.children]
            
            # If this is a filter node, try to push it down
            if node.operation == 'filter':
                for i, child in enumerate(node.children):
                    if self._can_push_predicate(node.predicate, child):
                        child.predicates.append(node.predicate)
                        # Remove this filter node
                        return child
                        
            return node
            
        new_plan = query_plan.clone()
        new_plan.root = push_predicate(new_plan.root)
        return new_plan
    
    def estimate_cost(self, query_plan: QueryPlan) -> float:
        """Estimate the cost after pushing down predicates."""
        def estimate_node_cost(node: QueryNode) -> float:
            if not node.children:
                return 1.0
            
            child_costs = sum(estimate_node_cost(child) for child in node.children)
            # Filtering early reduces data volume
            if node.operation == 'filter':
                return child_costs * 0.5
            return child_costs
            
        return estimate_node_cost(query_plan.root)
    
    def _can_push_predicate(self, predicate: dict, node: QueryNode) -> bool:
        """Check if a predicate can be pushed down to a node."""
        # Implementation depends on predicate and node types
        return True  # Simplified for now

class JoinReordering(OptimizationRule):
    """Optimization rule that reorders joins for better performance."""
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Reorder joins based on table sizes and join conditions."""
        def find_join_groups(node: QueryNode) -> List[QueryNode]:
            if not node.children:
                return [node]
            if node.operation != 'join':
                return sum((find_join_groups(child) for child in node.children), [])
            return [node]
        
        new_plan = query_plan.clone()
        joins = find_join_groups(new_plan.root)
        
        # Reorder based on estimated sizes (simplified)
        joins.sort(key=lambda x: self._estimate_join_cost(x))
        
        # Rebuild the plan with reordered joins
        if joins:
            new_plan.root = self._build_join_tree(joins)
            
        return new_plan
    
    def estimate_cost(self, query_plan: QueryPlan) -> float:
        """Estimate the cost of the join order."""
        def estimate_join_cost(node: QueryNode) -> float:
            if not node.children:
                return 1.0
            if node.operation != 'join':
                return sum(estimate_join_cost(child) for child in node.children)
            
            # Cost model: product of children's costs * join selectivity
            child_costs = [estimate_join_cost(child) for child in node.children]
            return sum(child_costs) * 0.8  # Assuming 80% selectivity
            
        return estimate_join_cost(query_plan.root)
    
    def _estimate_join_cost(self, node: QueryNode) -> float:
        """Estimate cost of a specific join node."""
        return self.estimate_cost(QueryPlan(node))
    
    def _build_join_tree(self, joins: List[QueryNode]) -> QueryNode:
        """Build an optimal join tree from a list of joins."""
        if not joins:
            return None
        if len(joins) == 1:
            return joins[0]
            
        # Build left-deep join tree
        root = joins[0]
        for join in joins[1:]:
            new_root = QueryNode(operation='join')
            new_root.children = [root, join]
            root = new_root
            
        return root

class ColumnPruning(OptimizationRule):
    """Optimization rule that removes unused columns early in the query plan."""
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Remove unused columns from the query plan."""
        new_plan = query_plan.clone()
        required_columns = self._find_required_columns(new_plan.root)
        
        def prune_columns(node: QueryNode) -> QueryNode:
            if not node.children:
                # Leaf node: keep only required columns
                node.columns = [col for col in node.columns 
                              if col in required_columns]
                return node
                
            # Recursively process children
            node.children = [prune_columns(child) for child in node.children]
            return node
            
        new_plan.root = prune_columns(new_plan.root)
        return new_plan
    
    def estimate_cost(self, query_plan: QueryPlan) -> float:
        """Estimate the cost after column pruning."""
        def count_columns(node: QueryNode) -> int:
            if not node.children:
                return len(node.columns)
            return sum(count_columns(child) for child in node.children)
            
        # Cost is proportional to number of columns
        return count_columns(query_plan.root) * 1.0
    
    def _find_required_columns(self, node: QueryNode) -> Set[str]:
        """Find all columns required by the query."""
        required = set()
        
        if node.operation == 'project':
            required.update(node.columns)
        elif node.operation == 'filter':
            required.update(self._extract_columns_from_predicate(node.predicate))
            
        for child in node.children:
            required.update(self._find_required_columns(child))
            
        return required
    
    def _extract_columns_from_predicate(self, predicate: dict) -> Set[str]:
        """Extract column names from a predicate."""
        # Implementation depends on predicate format
        return set()  # Simplified for now 