from typing import Dict, List, Optional, Pattern
from dataclasses import dataclass
import re
from enum import Enum
import structlog
from ..discovery.registry import ServiceRegistration

logger = structlog.get_logger()

class RouteMatchType(Enum):
    """Types of route matching criteria"""
    PATH = "path"
    HEADER = "header"
    QUERY = "query"
    METHOD = "method"

@dataclass
class RouteMatch:
    """Route matching criteria configuration"""
    match_type: RouteMatchType
    pattern: str
    value: Optional[str] = None  # For header/query matches
    regex: Optional[Pattern] = None  # Compiled regex for path matching

    def __post_init__(self):
        """Compile regex patterns after initialization"""
        if self.match_type == RouteMatchType.PATH and self.pattern:
            self.regex = re.compile(self.pattern)

@dataclass
class RouteDestination:
    """Route destination with traffic weight"""
    service_name: str
    weight: int = 100  # Percentage of traffic (0-100)
    version: Optional[str] = None
    subset: Optional[str] = None

@dataclass
class RouteRule:
    """Complete routing rule definition"""
    name: str
    matches: List[RouteMatch]
    destinations: List[RouteDestination]
    priority: int = 0  # Higher priority rules are evaluated first
    enabled: bool = True

class RoutingRuleManager:
    """
    Manages dynamic routing rules for service mesh.
    
    Features:
    - Traffic splitting
    - Header-based routing
    - Path-based routing
    - Version-based routing
    - Subset routing
    """
    
    def __init__(self):
        self.rules: Dict[str, RouteRule] = {}
        self.logger = logger.bind(component="routing_rules")
        
    async def add_rule(self, rule: RouteRule) -> None:
        """Add or update routing rule"""
        self.rules[rule.name] = rule
        self.logger.info("route_rule_added", 
                        rule_name=rule.name,
                        priority=rule.priority)
        
    async def remove_rule(self, rule_name: str) -> None:
        """Remove routing rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.logger.info("route_rule_removed", rule_name=rule_name)
            
    async def get_destinations(
        self,
        path: str,
        headers: Dict[str, str],
        method: str,
        query_params: Dict[str, str]
    ) -> List[RouteDestination]:
        """
        Get matching destinations for request.
        
        Evaluates rules in priority order and returns
        matching destinations with weights.
        """
        matching_rules = []
        
        # Evaluate all matching rules
        for rule in sorted(
            self.rules.values(),
            key=lambda x: x.priority,
            reverse=True
        ):
            if not rule.enabled:
                continue
                
            matches = True
            for match in rule.matches:
                if not self._evaluate_match(
                    match, path, headers, method, query_params
                ):
                    matches = False
                    break
                    
            if matches:
                matching_rules.append(rule)
                
        # Return destinations from highest priority matching rule
        if matching_rules:
            return matching_rules[0].destinations
            
        return []
        
    def _evaluate_match(
        self,
        match: RouteMatch,
        path: str,
        headers: Dict[str, str],
        method: str,
        query_params: Dict[str, str]
    ) -> bool:
        """Evaluate single route match condition"""
        try:
            if match.match_type == RouteMatchType.PATH:
                return bool(match.regex.match(path))
                
            elif match.match_type == RouteMatchType.HEADER:
                return headers.get(match.pattern) == match.value
                
            elif match.match_type == RouteMatchType.QUERY:
                return query_params.get(match.pattern) == match.value
                
            elif match.match_type == RouteMatchType.METHOD:
                return method.upper() == match.pattern.upper()
                
        except Exception as e:
            self.logger.error("route_match_error",
                            error=str(e),
                            match_type=match.match_type.value)
            return False
            
        return False

class TrafficSplitter:
    """
    Manages traffic splitting across service versions/subsets.
    
    Features:
    - Percentage-based traffic splitting
    - Gradual rollout support
    - A/B testing capability
    - Canary deployment support
    """
    
    def __init__(self):
        self.logger = logger.bind(component="traffic_splitter")
        
    async def select_destination(
        self,
        destinations: List[RouteDestination]
    ) -> Optional[RouteDestination]:
        """
        Select destination based on traffic weights.
        
        Uses weighted random selection to distribute
        traffic according to configured percentages.
        """
        if not destinations:
            return None
            
        # Normalize weights
        total_weight = sum(d.weight for d in destinations)
        if total_weight == 0:
            return destinations[0]
            
        import random
        r = random.randint(1, total_weight)
        
        # Select based on weight
        cumulative = 0
        for dest in destinations:
            cumulative += dest.weight
            if r <= cumulative:
                return dest
                
        return destinations[-1] 