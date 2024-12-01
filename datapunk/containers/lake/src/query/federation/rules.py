from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from ..optimizer.core import OptimizationRule, QueryPlan
from .core import DataSourceStats, FederationCost

@dataclass
class RuleMetrics:
    """Metrics for optimization rule application."""
    applications: int = 0
    successes: int = 0
    failures: int = 0
    avg_improvement: float = 0.0

class PushDownRule(OptimizationRule):
    """Push operations down to data sources."""
    
    def __init__(self):
        self.metrics = RuleMetrics()
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Apply push-down optimizations."""
        try:
            self.metrics.applications += 1
            modified_plan = self._push_filters(query_plan)
            modified_plan = self._push_projections(modified_plan)
            modified_plan = self._push_aggregates(modified_plan)
            
            if modified_plan != query_plan:
                self.metrics.successes += 1
            else:
                self.metrics.failures += 1
            
            return modified_plan
        except Exception as e:
            self.metrics.failures += 1
            raise
    
    def _push_filters(self, plan: QueryPlan) -> QueryPlan:
        """Push filter operations closer to data sources."""
        def can_push_filter(node: Any) -> bool:
            return (
                hasattr(node, 'operation_type') and
                node.operation_type.lower() == 'filter' and
                not self._has_volatile_functions(node)
            )
        
        def push_filter_down(node: Any) -> Any:
            if not node or not hasattr(node, 'children'):
                return node
            
            # Recursively process children
            node.children = [push_filter_down(child) for child in node.children]
            
            if can_push_filter(node):
                # Try to push filter below joins/unions
                for i, child in enumerate(node.children):
                    if hasattr(child, 'operation_type'):
                        if child.operation_type.lower() in ('join', 'union'):
                            # Create new filter nodes for each branch
                            node.children[i] = self._create_filter_node(
                                child,
                                node.condition
                            )
            
            return node
        
        new_plan = plan.copy()
        new_plan.root = push_filter_down(new_plan.root)
        return new_plan
    
    def _push_projections(self, plan: QueryPlan) -> QueryPlan:
        """Push projection operations closer to data sources."""
        def can_push_projection(node: Any) -> bool:
            return (
                hasattr(node, 'operation_type') and
                node.operation_type.lower() == 'project'
            )
        
        def push_projection_down(node: Any, required_columns: Set[str]) -> Any:
            if not node or not hasattr(node, 'children'):
                return node
            
            if can_push_projection(node):
                required_columns.update(node.columns)
            
            # Track columns needed by this node
            if hasattr(node, 'used_columns'):
                required_columns.update(node.used_columns)
            
            # Recursively process children with updated column requirements
            node.children = [
                push_projection_down(child, required_columns.copy())
                for child in node.children
            ]
            
            # Add projection if beneficial
            if (hasattr(node, 'available_columns') and
                len(node.available_columns) > len(required_columns)):
                node = self._create_projection_node(node, required_columns)
            
            return node
        
        new_plan = plan.copy()
        new_plan.root = push_projection_down(new_plan.root, set())
        return new_plan
    
    def _push_aggregates(self, plan: QueryPlan) -> QueryPlan:
        """Push aggregation operations closer to data sources."""
        def can_push_aggregate(node: Any) -> bool:
            return (
                hasattr(node, 'operation_type') and
                node.operation_type.lower() == 'aggregate' and
                not self._has_volatile_functions(node)
            )
        
        def push_aggregate_down(node: Any) -> Any:
            if not node or not hasattr(node, 'children'):
                return node
            
            # Recursively process children
            node.children = [push_aggregate_down(child) for child in node.children]
            
            if can_push_aggregate(node):
                # Try to push aggregates through joins
                for i, child in enumerate(node.children):
                    if (hasattr(child, 'operation_type') and
                        child.operation_type.lower() == 'join'):
                        # Check if aggregate can be pushed to either side
                        left_pushable = self._can_push_through_join(
                            node, child.left, 'left'
                        )
                        right_pushable = self._can_push_through_join(
                            node, child.right, 'right'
                        )
                        
                        if left_pushable or right_pushable:
                            node.children[i] = self._create_split_aggregate(
                                child,
                                node.group_by,
                                node.aggregations,
                                left_pushable,
                                right_pushable
                            )
            
            return node
        
        new_plan = plan.copy()
        new_plan.root = push_aggregate_down(new_plan.root)
        return new_plan
    
    def _has_volatile_functions(self, node: Any) -> bool:
        """Check if node contains volatile functions."""
        volatile_functions = {
            'random', 'now', 'current_timestamp',
            'current_user', 'session_user'
        }
        
        if hasattr(node, 'functions'):
            return any(
                func.lower() in volatile_functions
                for func in node.functions
            )
        return False
    
    def _can_push_through_join(self,
                              agg_node: Any,
                              join_branch: Any,
                              side: str) -> bool:
        """Check if aggregate can be pushed through join branch."""
        if not hasattr(agg_node, 'group_by') or not hasattr(join_branch, 'columns'):
            return False
        
        # Check if all group by columns come from this branch
        group_by_cols = set(agg_node.group_by)
        branch_cols = set(join_branch.columns)
        
        # Check if all aggregation inputs come from this branch
        agg_cols = set()
        for agg in agg_node.aggregations.values():
            if hasattr(agg, 'columns'):
                agg_cols.update(agg.columns)
        
        return (
            group_by_cols.issubset(branch_cols) and
            agg_cols.issubset(branch_cols)
        )
    
    def _create_filter_node(self, child: Any, condition: Any) -> Any:
        """Create a new filter node."""
        # Implementation depends on query plan node structure
        pass
    
    def _create_projection_node(self,
                              child: Any,
                              columns: Set[str]) -> Any:
        """Create a new projection node."""
        # Implementation depends on query plan node structure
        pass
    
    def _create_split_aggregate(self,
                              join_node: Any,
                              group_by: List[str],
                              aggregations: Dict[str, Any],
                              push_left: bool,
                              push_right: bool) -> Any:
        """Create split aggregate nodes around join."""
        # Implementation depends on query plan node structure
        pass

class JoinReorderRule(OptimizationRule):
    """Reorder joins for optimal execution."""
    
    def __init__(self):
        self.metrics = RuleMetrics()
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Apply join reordering optimizations."""
        try:
            self.metrics.applications += 1
            
            # Extract join graph
            joins = self._extract_joins(query_plan)
            if not joins:
                self.metrics.failures += 1
                return query_plan
            
            # Find optimal join order
            optimal_order = self._find_optimal_order(joins)
            
            # Create new plan with reordered joins
            new_plan = self._create_reordered_plan(query_plan, optimal_order)
            
            self.metrics.successes += 1
            return new_plan
        except Exception as e:
            self.metrics.failures += 1
            raise
    
    def _extract_joins(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Extract join operations from plan."""
        joins = []
        
        def extract_from_node(node: Any) -> None:
            if (hasattr(node, 'operation_type') and
                node.operation_type.lower() == 'join'):
                joins.append({
                    'node': node,
                    'left': node.left,
                    'right': node.right,
                    'condition': node.condition,
                    'type': node.join_type
                })
            
            if hasattr(node, 'children'):
                for child in node.children:
                    extract_from_node(child)
        
        extract_from_node(plan.root)
        return joins
    
    def _find_optimal_order(self,
                          joins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find optimal join order using dynamic programming."""
        if len(joins) <= 2:
            return joins
        
        # Build cost matrix
        costs = {}
        for i, join1 in enumerate(joins):
            for j, join2 in enumerate(joins):
                if i != j:
                    costs[(i, j)] = self._estimate_join_cost(join1, join2)
        
        # Find optimal order using dynamic programming
        n = len(joins)
        dp = {}
        
        def solve(mask: int) -> Tuple[float, List[int]]:
            if mask in dp:
                return dp[mask]
            
            if bin(mask).count('1') <= 2:
                return 0.0, []
            
            min_cost = float('inf')
            best_order = []
            
            for i in range(n):
                if not (mask & (1 << i)):
                    continue
                    
                for j in range(i + 1, n):
                    if not (mask & (1 << j)):
                        continue
                        
                    # Try joining these two
                    new_mask = mask & ~(1 << i) & ~(1 << j)
                    subcost, suborder = solve(new_mask)
                    total_cost = subcost + costs.get((i, j), float('inf'))
                    
                    if total_cost < min_cost:
                        min_cost = total_cost
                        best_order = suborder + [i, j]
            
            dp[mask] = (min_cost, best_order)
            return dp[mask]
        
        _, optimal_order = solve((1 << n) - 1)
        
        # Reconstruct join order
        return [joins[i] for i in optimal_order]
    
    def _estimate_join_cost(self,
                          join1: Dict[str, Any],
                          join2: Dict[str, Any]) -> float:
        """Estimate cost of joining two subplans."""
        # Estimate based on:
        # 1. Result sizes
        # 2. Join types
        # 3. Available indexes
        # 4. Network transfer costs
        
        # Basic implementation - can be enhanced
        cost = 1.0
        
        # Penalize cross joins
        if not join1.get('condition') or not join2.get('condition'):
            cost *= 10.0
        
        # Prefer inner joins
        if join1.get('type') != 'inner' or join2.get('type') != 'inner':
            cost *= 2.0
        
        return cost
    
    def _create_reordered_plan(self,
                             original_plan: QueryPlan,
                             join_order: List[Dict[str, Any]]) -> QueryPlan:
        """Create new plan with reordered joins."""
        # Implementation depends on query plan node structure
        pass

class DataLocalityRule(OptimizationRule):
    """Optimize for data locality and minimize data movement."""
    
    def __init__(self):
        self.metrics = RuleMetrics()
        self.source_stats: Dict[str, DataSourceStats] = {}
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Apply data locality optimizations."""
        try:
            self.metrics.applications += 1
            
            # Analyze data placement
            data_locations = self._analyze_data_placement(query_plan)
            
            # Find optimal execution locations
            execution_plan = self._optimize_execution_locations(
                query_plan,
                data_locations
            )
            
            # Update plan with optimized locations
            new_plan = self._update_execution_locations(
                query_plan,
                execution_plan
            )
            
            self.metrics.successes += 1
            return new_plan
        except Exception as e:
            self.metrics.failures += 1
            raise
    
    def _analyze_data_placement(self,
                              plan: QueryPlan) -> Dict[str, Set[str]]:
        """Analyze current data placement across sources."""
        placements = {}
        
        def analyze_node(node: Any) -> None:
            if hasattr(node, 'table_name') and hasattr(node, 'source_id'):
                if node.source_id not in placements:
                    placements[node.source_id] = set()
                placements[node.source_id].add(node.table_name)
            
            if hasattr(node, 'children'):
                for child in node.children:
                    analyze_node(child)
        
        analyze_node(plan.root)
        return placements
    
    def _optimize_execution_locations(self,
                                   plan: QueryPlan,
                                   data_locations: Dict[str, Set[str]]) -> Dict[str, str]:
        """Optimize operation execution locations."""
        execution_locations = {}
        
        def optimize_node(node: Any) -> str:
            """Determine optimal execution location for node."""
            if not node:
                return None
            
            # For leaf nodes (table scans)
            if hasattr(node, 'table_name') and hasattr(node, 'source_id'):
                execution_locations[node.id] = node.source_id
                return node.source_id
            
            # For internal nodes
            child_locations = []
            if hasattr(node, 'children'):
                for child in node.children:
                    loc = optimize_node(child)
                    if loc:
                        child_locations.append(loc)
            
            # Determine best location based on operation type and children
            best_location = self._find_best_location(
                node,
                child_locations,
                data_locations
            )
            
            execution_locations[node.id] = best_location
            return best_location
        
        optimize_node(plan.root)
        return execution_locations
    
    def _find_best_location(self,
                          node: Any,
                          child_locations: List[str],
                          data_locations: Dict[str, Set[str]]) -> str:
        """Find best execution location for an operation."""
        if not child_locations:
            return None
        
        # For single-source operations, use that source
        if len(set(child_locations)) == 1:
            return child_locations[0]
        
        # For multi-source operations, consider:
        # 1. Source capabilities
        # 2. Data sizes
        # 3. Network costs
        # 4. Processing power
        
        scores = {}
        for source_id in data_locations.keys():
            scores[source_id] = self._calculate_location_score(
                source_id,
                node,
                child_locations,
                data_locations
            )
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _calculate_location_score(self,
                                source_id: str,
                                node: Any,
                                child_locations: List[str],
                                data_locations: Dict[str, Set[str]]) -> float:
        """Calculate score for executing operation at a location."""
        score = 0.0
        
        # Check source capabilities
        stats = self.source_stats.get(source_id)
        if not stats:
            return float('-inf')
        
        # Base score on source capabilities
        if hasattr(node, 'operation_type'):
            if node.operation_type.lower() in stats.capabilities:
                score += 1.0
            else:
                return float('-inf')
        
        # Consider data locality
        local_data = len([
            loc for loc in child_locations
            if loc == source_id
        ])
        score += local_data / len(child_locations)
        
        # Consider source performance
        score += (1.0 / (stats.avg_query_time_ms + 1.0))
        
        # Penalize for error rate
        score *= (1.0 - stats.error_rate)
        
        return score
    
    def _update_execution_locations(self,
                                  plan: QueryPlan,
                                  execution_locations: Dict[str, str]) -> QueryPlan:
        """Update plan with optimized execution locations."""
        # Implementation depends on query plan node structure
        pass 