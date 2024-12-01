from typing import Dict, List, Optional, Any, Set, Tuple
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

class MaterializationRule(OptimizationRule):
    """Optimize materialization points in federated queries."""
    
    def __init__(self):
        self.materialized_views: Dict[str, Any] = {}
        self.materialization_threshold = 0.7  # Cost reduction threshold
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Apply materialization optimizations."""
        # Find potential materialization points
        candidates = self._find_materialization_candidates(query_plan)
        
        # Evaluate benefits
        beneficial = [
            candidate for candidate in candidates
            if self._evaluate_materialization_benefit(candidate) > self.materialization_threshold
        ]
        
        # Apply materializations
        if beneficial:
            return self._apply_materializations(query_plan, beneficial)
        
        return query_plan
    
    def _find_materialization_candidates(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Find subqueries that are candidates for materialization."""
        candidates = []
        
        def analyze_node(node: Any, context: Dict[str, Any]) -> None:
            if not node:
                return
            
            # Check if node is a materialization candidate
            if self._is_materialization_candidate(node, context):
                candidates.append({
                    'node': node,
                    'context': context.copy(),
                    'cost': self._estimate_materialization_cost(node)
                })
            
            # Update context for children
            child_context = self._update_context(context, node)
            
            # Process children
            if hasattr(node, 'children'):
                for child in node.children:
                    analyze_node(child, child_context)
        
        analyze_node(plan.root, {})
        return candidates
    
    def _is_materialization_candidate(self,
                                    node: Any,
                                    context: Dict[str, Any]) -> bool:
        """Check if a node is a candidate for materialization."""
        if not hasattr(node, 'operation_type'):
            return False
        
        # Consider materializing:
        # 1. Expensive joins
        # 2. Complex aggregations
        # 3. Frequently reused subqueries
        return (
            self._is_expensive_join(node) or
            self._is_complex_aggregation(node) or
            self._is_frequently_reused(node, context)
        )
    
    def _is_expensive_join(self, node: Any) -> bool:
        """Check if node is an expensive join operation."""
        return (
            hasattr(node, 'operation_type') and
            node.operation_type.lower() == 'join' and
            hasattr(node, 'estimated_cost') and
            node.estimated_cost > 1000  # Threshold
        )
    
    def _is_complex_aggregation(self, node: Any) -> bool:
        """Check if node is a complex aggregation."""
        return (
            hasattr(node, 'operation_type') and
            node.operation_type.lower() == 'aggregate' and
            hasattr(node, 'aggregations') and
            len(node.aggregations) > 2
        )
    
    def _is_frequently_reused(self,
                            node: Any,
                            context: Dict[str, Any]) -> bool:
        """Check if node represents a frequently reused subquery."""
        if not hasattr(node, 'query_hash'):
            return False
        
        reuse_count = context.get('reuse_counts', {}).get(node.query_hash, 0)
        return reuse_count > 2  # Threshold

class PartitionPruningRule(OptimizationRule):
    """Optimize partition access in federated queries."""
    
    def __init__(self):
        self.partition_metadata: Dict[str, Dict[str, Any]] = {}
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Apply partition pruning optimizations."""
        # Analyze partition predicates
        predicates = self._extract_partition_predicates(query_plan)
        
        # Determine prunable partitions
        prunable = self._identify_prunable_partitions(predicates)
        
        # Apply pruning
        if prunable:
            return self._apply_partition_pruning(query_plan, prunable)
        
        return query_plan
    
    def _extract_partition_predicates(self,
                                    plan: QueryPlan) -> Dict[str, List[Dict[str, Any]]]:
        """Extract predicates relevant to partitioning."""
        predicates = {}
        
        def extract_from_node(node: Any) -> None:
            if hasattr(node, 'operation_type') and node.operation_type.lower() == 'filter':
                if hasattr(node, 'condition'):
                    table_name = self._get_table_name(node)
                    if table_name:
                        if table_name not in predicates:
                            predicates[table_name] = []
                        predicates[table_name].append({
                            'condition': node.condition,
                            'node': node
                        })
            
            if hasattr(node, 'children'):
                for child in node.children:
                    extract_from_node(child)
        
        extract_from_node(plan.root)
        return predicates
    
    def _identify_prunable_partitions(self,
                                    predicates: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Set[str]]:
        """Identify partitions that can be pruned."""
        prunable = {}
        
        for table_name, table_predicates in predicates.items():
            if table_name in self.partition_metadata:
                partition_info = self.partition_metadata[table_name]
                prunable[table_name] = self._evaluate_partition_predicates(
                    table_predicates,
                    partition_info
                )
        
        return prunable
    
    def _evaluate_partition_predicates(self,
                                     predicates: List[Dict[str, Any]],
                                     partition_info: Dict[str, Any]) -> Set[str]:
        """Evaluate predicates against partition information."""
        # Implementation depends on partition scheme
        pass

class FederatedIndexRule(OptimizationRule):
    """Optimize index usage across federated sources."""
    
    def __init__(self):
        self.source_indexes: Dict[str, Dict[str, Any]] = {}
        self.index_stats: Dict[str, Dict[str, Any]] = {}
    
    def apply(self, query_plan: QueryPlan) -> QueryPlan:
        """Apply federated index optimizations."""
        # Analyze index opportunities
        opportunities = self._find_index_opportunities(query_plan)
        
        # Select best indexes
        selected = self._select_best_indexes(opportunities)
        
        # Apply index selections
        if selected:
            return self._apply_index_selections(query_plan, selected)
        
        return query_plan
    
    def _find_index_opportunities(self,
                                plan: QueryPlan) -> List[Dict[str, Any]]:
        """Find opportunities for index usage."""
        opportunities = []
        
        def analyze_node(node: Any) -> None:
            if self._can_use_index(node):
                opportunities.append({
                    'node': node,
                    'indexes': self._find_applicable_indexes(node),
                    'estimated_benefit': self._estimate_index_benefit(node)
                })
            
            if hasattr(node, 'children'):
                for child in node.children:
                    analyze_node(child)
        
        analyze_node(plan.root)
        return opportunities
    
    def _can_use_index(self, node: Any) -> bool:
        """Check if node can benefit from index usage."""
        if not hasattr(node, 'operation_type'):
            return False
        
        indexable_ops = {'filter', 'join', 'aggregate', 'sort'}
        return node.operation_type.lower() in indexable_ops
    
    def _find_applicable_indexes(self, node: Any) -> List[Dict[str, Any]]:
        """Find indexes applicable to a node."""
        if not hasattr(node, 'table_name') or not hasattr(node, 'columns'):
            return []
        
        table_indexes = self.source_indexes.get(node.table_name, {})
        return [
            index for index in table_indexes.values()
            if self._is_index_applicable(index, node)
        ]
    
    def _is_index_applicable(self,
                           index: Dict[str, Any],
                           node: Any) -> bool:
        """Check if an index is applicable to a node."""
        if not hasattr(node, 'columns'):
            return False
        
        # Check if index columns match node columns
        index_cols = set(index['columns'])
        node_cols = set(node.columns)
        
        # Index is applicable if it covers any needed columns
        return bool(index_cols & node_cols)
    
    def _estimate_index_benefit(self, node: Any) -> float:
        """Estimate benefit of using an index."""
        if not hasattr(node, 'estimated_cost'):
            return 0.0
        
        # Basic cost model
        base_cost = node.estimated_cost
        
        # Estimate reduction from index
        if hasattr(node, 'operation_type'):
            if node.operation_type.lower() == 'filter':
                return base_cost * 0.8  # 80% reduction
            elif node.operation_type.lower() == 'join':
                return base_cost * 0.6  # 60% reduction
            elif node.operation_type.lower() in ('aggregate', 'sort'):
                return base_cost * 0.4  # 40% reduction
        
        return 0.0
    
    def _select_best_indexes(self,
                           opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select best indexes to use."""
        selections = {}
        
        for opportunity in opportunities:
            node_id = opportunity['node'].id
            indexes = opportunity['indexes']
            
            if indexes:
                # Score each index
                scores = [
                    (index, self._score_index(index, opportunity))
                    for index in indexes
                ]
                
                # Select best scoring index
                best_index = max(scores, key=lambda x: x[1])[0]
                selections[node_id] = best_index
        
        return selections
    
    def _score_index(self,
                    index: Dict[str, Any],
                    opportunity: Dict[str, Any]) -> float:
        """Score an index for an opportunity."""
        # Consider:
        # 1. Index selectivity
        # 2. Index size
        # 3. Maintenance cost
        # 4. Usage statistics
        
        stats = self.index_stats.get(index['id'], {})
        
        selectivity_score = stats.get('selectivity', 0.5)
        size_score = 1.0 / (1 + stats.get('size_mb', 1000))
        maintenance_score = 1.0 - stats.get('maintenance_cost', 0.5)
        usage_score = min(stats.get('usage_count', 0) / 100, 1.0)
        
        return (
            0.4 * selectivity_score +
            0.2 * size_score +
            0.2 * maintenance_score +
            0.2 * usage_score
        )
    
    def _apply_index_selections(self,
                              plan: QueryPlan,
                              selections: Dict[str, Any]) -> QueryPlan:
        """Apply selected indexes to query plan."""
        def apply_to_node(node: Any) -> Any:
            if hasattr(node, 'id') and node.id in selections:
                # Add index hint to node
                node.hints = {
                    'use_index': selections[node.id]['name'],
                    'index_type': selections[node.id]['type']
                }
            
            if hasattr(node, 'children'):
                node.children = [apply_to_node(child) for child in node.children]
            
            return node
        
        new_plan = plan.copy()
        new_plan.root = apply_to_node(new_plan.root)
        return new_plan 