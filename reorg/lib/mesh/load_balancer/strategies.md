# Load Balancing Strategies

## Purpose

Defines the core load balancing algorithms and selection strategies used to distribute requests across service instances.

## Context

These strategies form the algorithmic foundation of the load balancer, each optimized for different workload patterns and service characteristics.

## Dependencies

- Load Balancer Core
- Metrics Collection System
- Health Monitoring System

## Available Strategies

### Weighted Round Robin

```python
class WeightedRoundRobin(LoadBalancingStrategy):
```

- Distributes requests in circular order considering instance weights
- Maintains separate weight counters per service
- Dynamically adjusts for instance health scores
- Best for predictable, uniform workloads

### Least Connections

```python
class LeastConnections(LoadBalancingStrategy):
```

- Selects instance with fewest active connections
- Weights selection by instance health score
- Prevents overload of degraded instances
- Best for variable connection duration workloads

### Power of Two Choices

```python
class PowerOfTwo(LoadBalancingStrategy):
```

- Randomly selects two instances and chooses the better one
- Uses health-weighted load scoring
- O(1) selection time complexity
- Particularly effective under high concurrency

### Adaptive Strategy

```python
class AdaptiveLoadBalancer:
```

- Automatically switches between strategies based on conditions
- Uses least connections when load variance > 30%
- Uses power of two under high load (>100 connections/instance)
- Falls back to weighted round-robin for normal conditions

## Implementation Details

### Base Strategy Interface

```python
class LoadBalancingStrategy(ABC):
    @abstractmethod
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        pass
```

All strategies implement this interface for consistent integration.

### Health Filtering

```python
def _filter_healthy(self, instances: List[ServiceInstance]) -> List[ServiceInstance]:
    return [i for i in instances if i.health_score > 0.5]
```

- Filters instances based on health score
- Default threshold of 0.5 (configurable)
- Prevents selection of degraded instances

### Load Scoring

Various strategies implement load scoring differently:

```python
# Least Connections
load_score = connections / health_score

# Power of Two
load_score = connections * (1 / health_score)

# Adaptive
load_score = base_score + health_bonus / (1 + error_penalty)
```

## Performance Considerations

- Strategy switching adds minimal overhead
- Health filtering occurs on every selection
- Load score calculations are O(1)
- Power of Two provides good balance of performance and distribution

## Security Considerations

- Strategies rely on accurate health reporting
- Load metrics should be protected from tampering
- Strategy selection could be exploited for targeted instance overload

## Known Issues

- Strategy switching may cause temporary load imbalances
- Health score threshold is not dynamically adjusted
- Load variance calculation may be CPU intensive

## Future Improvements

- Dynamic health score thresholds based on load
- Machine learning for strategy selection
- Custom strategy plugins
- Geographic awareness for multi-region deployments
