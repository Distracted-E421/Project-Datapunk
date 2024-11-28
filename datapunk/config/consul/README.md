# Consul Configuration Documentation

## Overview
This document explains the configuration choices in `config.json` for Consul service mesh integration. See `sys-arch.mmd` for the complete service mesh architecture.

## Configuration Sections

### Primary Configuration
- `datacenter`: Logical datacenter name (configurable per environment)
- `data_dir`: Persistent storage location for Consul data
- `log_level`: Current logging verbosity (needs integration with log aggregation)
- `node_name`: Unique identifier in service mesh topology

### Server Mode
- Currently configured for single-node development setup
- Production should use 3+ nodes for high availability
- `bootstrap_expect` must match number of server nodes

### UI Configuration
- Development-only feature for debugging
- Production deployment should:
  - Enable authentication
  - Restrict access to admin networks
  - Consider disabling if not needed

### Service Mesh Features
- Enables Connect for service-to-service communication
- Required for mTLS implementation
- Integrates with certificate management system

### Network Configuration
- DNS (8600): Service discovery endpoint
- HTTP (8500): API and UI access
- HTTPS (-1): Disabled for dev, required for production
- gRPC (8502): Service mesh communication

### Monitoring Integration
- Prometheus metrics collection
- 24-hour retention (adjustable based on storage)
- Hostname disabled to prevent mesh conflicts

## Production Considerations

### Security
- Enable HTTPS with valid certificates
- Implement access control for UI
- Configure mTLS for all services
- Review port exposure

### High Availability
- Deploy minimum 3 server nodes
- Configure proper quorum settings
- Implement backup strategy

### Monitoring
- Set up log aggregation
- Configure metrics retention
- Implement alerting

## TODOs

1. Environment-specific configurations
2. Multi-node production setup
3. HTTPS enablement
4. UI authentication
5. Log aggregation integration
6. Metrics retention optimization

## Related Documentation
- `sys-arch.mmd`: Service mesh architecture
- `project_status.md`: Implementation status
- `mtls-config.yaml`: Certificate configuration 