from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..parser.core import QueryPlan, QueryNode

class OptimizationRule(ABC):
    """Base class for optimization rules that can be applied to query plans."""
    
    @abstractmethod
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Apply this optimization rule to the given query plan."""
        pass

    @abstractmethod
    def estimate_cost(self, query_plan: QueryPlan) -> float:
        """Estimate the cost of the query plan after applying this rule."""
        pass

class QueryOptimizer:
    """Core query optimizer that applies optimization rules to query plans."""
    
    def __init__(self, rules: Optional[List[OptimizationRule]] = None):
        self.rules = rules or []
        self.statistics_cache: Dict[str, Any] = {}
    
    def add_rule(self, rule: OptimizationRule) -> None:
        """Add a new optimization rule to the optimizer."""
        self.rules.append(rule)
    
    def optimize(self, query_plan: QueryPlan) -> QueryPlan:
        """
        Optimize the given query plan by applying all available rules
        in the most beneficial order.
        """
        current_plan = query_plan
        best_cost = float('inf')
        
        while True:
            improved = False
            for rule in self.rules:
                new_plan = rule.apply(current_plan)
                new_cost = rule.estimate_cost(new_plan)
                
                if new_cost < best_cost:
                    current_plan = new_plan
                    best_cost = new_cost
                    improved = True
            
            if not improved:
                break
                
        return current_plan
    
    def update_statistics(self, table_name: str, statistics: Dict[str, Any]) -> None:
        """Update the statistics cache with new information about a table."""
        self.statistics_cache[table_name] = statistics
    
    def get_statistics(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached statistics for a given table."""
        return self.statistics_cache.get(table_name)

class CostBasedOptimizer(QueryOptimizer):
    """Cost-based query optimizer that uses statistical information for optimization."""
    
    def __init__(self, rules: Optional[List[OptimizationRule]] = None):
        super().__init__(rules)
        self.cost_threshold = 1000.0  # Default cost threshold
    
    def set_cost_threshold(self, threshold: float) -> None:
        """Set the cost threshold for optimization decisions."""
        self.cost_threshold = threshold
    
    def optimize(self, query_plan: QueryPlan) -> QueryPlan:
        """
        Optimize the query plan using cost-based decisions and
        statistical information.
        """
        current_plan = query_plan
        current_cost = float('inf')
        
        for rule in self.rules:
            candidate_plan = rule.apply(current_plan)
            candidate_cost = rule.estimate_cost(candidate_plan)
            
            # Only apply the optimization if it provides significant improvement
            if candidate_cost < current_cost and \
               (current_cost - candidate_cost) > self.cost_threshold:
                current_plan = candidate_plan
                current_cost = candidate_cost
        
        return current_plan 