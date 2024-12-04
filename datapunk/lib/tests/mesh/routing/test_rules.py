import pytest
from datapunk_shared.mesh.routing.rules import (
    RouteMatchType,
    RouteMatch,
    RouteDestination,
    RouteRule,
    RoutingRuleManager,
    TrafficSplitter
)

@pytest.fixture
def rule_manager():
    return RoutingRuleManager()

@pytest.fixture
def traffic_splitter():
    return TrafficSplitter()

@pytest.mark.asyncio
async def test_path_based_routing(rule_manager):
    """Test path-based routing rules"""
    # Create test rule
    rule = RouteRule(
        name="test_path_rule",
        matches=[
            RouteMatch(
                match_type=RouteMatchType.PATH,
                pattern=r"^/api/v1/.*"
            )
        ],
        destinations=[
            RouteDestination(
                service_name="api-v1-service",
                weight=100
            )
        ]
    )
    
    await rule_manager.add_rule(rule)
    
    # Test matching path
    destinations = await rule_manager.get_destinations(
        path="/api/v1/users",
        headers={},
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 1
    assert destinations[0].service_name == "api-v1-service"
    
    # Test non-matching path
    destinations = await rule_manager.get_destinations(
        path="/api/v2/users",
        headers={},
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 0

@pytest.mark.asyncio
async def test_header_based_routing(rule_manager):
    """Test header-based routing rules"""
    # Create test rule
    rule = RouteRule(
        name="test_header_rule",
        matches=[
            RouteMatch(
                match_type=RouteMatchType.HEADER,
                pattern="x-version",
                value="v2"
            )
        ],
        destinations=[
            RouteDestination(
                service_name="v2-service",
                weight=100
            )
        ]
    )
    
    await rule_manager.add_rule(rule)
    
    # Test matching header
    destinations = await rule_manager.get_destinations(
        path="/api/users",
        headers={"x-version": "v2"},
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 1
    assert destinations[0].service_name == "v2-service"
    
    # Test non-matching header
    destinations = await rule_manager.get_destinations(
        path="/api/users",
        headers={"x-version": "v1"},
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 0

@pytest.mark.asyncio
async def test_method_based_routing(rule_manager):
    """Test HTTP method-based routing"""
    # Create test rule
    rule = RouteRule(
        name="test_method_rule",
        matches=[
            RouteMatch(
                match_type=RouteMatchType.METHOD,
                pattern="POST"
            )
        ],
        destinations=[
            RouteDestination(
                service_name="write-service",
                weight=100
            )
        ]
    )
    
    await rule_manager.add_rule(rule)
    
    # Test matching method
    destinations = await rule_manager.get_destinations(
        path="/api/users",
        headers={},
        method="POST",
        query_params={}
    )
    
    assert len(destinations) == 1
    assert destinations[0].service_name == "write-service"
    
    # Test non-matching method
    destinations = await rule_manager.get_destinations(
        path="/api/users",
        headers={},
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 0

@pytest.mark.asyncio
async def test_query_based_routing(rule_manager):
    """Test query parameter-based routing"""
    # Create test rule
    rule = RouteRule(
        name="test_query_rule",
        matches=[
            RouteMatch(
                match_type=RouteMatchType.QUERY,
                pattern="version",
                value="beta"
            )
        ],
        destinations=[
            RouteDestination(
                service_name="beta-service",
                weight=100
            )
        ]
    )
    
    await rule_manager.add_rule(rule)
    
    # Test matching query
    destinations = await rule_manager.get_destinations(
        path="/api/users",
        headers={},
        method="GET",
        query_params={"version": "beta"}
    )
    
    assert len(destinations) == 1
    assert destinations[0].service_name == "beta-service"
    
    # Test non-matching query
    destinations = await rule_manager.get_destinations(
        path="/api/users",
        headers={},
        method="GET",
        query_params={"version": "stable"}
    )
    
    assert len(destinations) == 0

@pytest.mark.asyncio
async def test_traffic_splitting(traffic_splitter):
    """Test traffic splitting between services"""
    destinations = [
        RouteDestination(
            service_name="service-a",
            weight=75
        ),
        RouteDestination(
            service_name="service-b",
            weight=25
        )
    ]
    
    # Test distribution over multiple iterations
    results = {"service-a": 0, "service-b": 0}
    iterations = 1000
    
    for _ in range(iterations):
        dest = await traffic_splitter.select_destination(destinations)
        results[dest.service_name] += 1
    
    # Check approximate distribution (allowing for some variance)
    assert 700 < results["service-a"] < 800  # ~75%
    assert 200 < results["service-b"] < 300  # ~25%

@pytest.mark.asyncio
async def test_rule_priority(rule_manager):
    """Test rule priority ordering"""
    # Create lower priority rule
    low_priority = RouteRule(
        name="low_priority",
        matches=[
            RouteMatch(
                match_type=RouteMatchType.PATH,
                pattern=r"^/api/.*"
            )
        ],
        destinations=[
            RouteDestination(
                service_name="default-service",
                weight=100
            )
        ],
        priority=0
    )
    
    # Create higher priority rule
    high_priority = RouteRule(
        name="high_priority",
        matches=[
            RouteMatch(
                match_type=RouteMatchType.PATH,
                pattern=r"^/api/special/.*"
            )
        ],
        destinations=[
            RouteDestination(
                service_name="special-service",
                weight=100
            )
        ],
        priority=10
    )
    
    await rule_manager.add_rule(low_priority)
    await rule_manager.add_rule(high_priority)
    
    # Test path matching high priority rule
    destinations = await rule_manager.get_destinations(
        path="/api/special/endpoint",
        headers={},
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 1
    assert destinations[0].service_name == "special-service"
    
    # Test path matching only low priority rule
    destinations = await rule_manager.get_destinations(
        path="/api/regular/endpoint",
        headers={},
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 1
    assert destinations[0].service_name == "default-service"

@pytest.mark.asyncio
async def test_multiple_match_conditions(rule_manager):
    """Test rules with multiple match conditions"""
    rule = RouteRule(
        name="multi_condition",
        matches=[
            RouteMatch(
                match_type=RouteMatchType.PATH,
                pattern=r"^/api/v1/.*"
            ),
            RouteMatch(
                match_type=RouteMatchType.HEADER,
                pattern="x-region",
                value="us-west"
            ),
            RouteMatch(
                match_type=RouteMatchType.METHOD,
                pattern="GET"
            )
        ],
        destinations=[
            RouteDestination(
                service_name="region-specific-service",
                weight=100
            )
        ]
    )
    
    await rule_manager.add_rule(rule)
    
    # Test all conditions matching
    destinations = await rule_manager.get_destinations(
        path="/api/v1/users",
        headers={"x-region": "us-west"},
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 1
    assert destinations[0].service_name == "region-specific-service"
    
    # Test one condition not matching
    destinations = await rule_manager.get_destinations(
        path="/api/v1/users",
        headers={"x-region": "us-east"},  # Different region
        method="GET",
        query_params={}
    )
    
    assert len(destinations) == 0 