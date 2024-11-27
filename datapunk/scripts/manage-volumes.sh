#!/bin/bash

# Volume Management Script for Datapunk Services
# Handles creation, backup, and cleanup of service data volumes
# NOTE: Requires root or sudo access for permission management

function create_volumes() {
    local service=$1
    
    echo "Creating volumes for $service..."
    
    # Create directory structure for service data
    # NOTE: Separate directories for data and backups improve organization
    mkdir -p data/$service
    mkdir -p backup/$service
    
    # Set secure permissions
    # NOTE: datapunk user needs write access, others only read
    # TODO: Add configurable permission settings
    chown -R datapunk:datapunk data/$service
    chown -R datapunk:datapunk backup/$service
    chmod -R 755 data/$service
    chmod -R 755 backup/$service
}

function backup_volumes() {
    local service=$1
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    echo "Backing up volumes for $service..."
    
    # Create timestamped backup archive
    # NOTE: Using tar with gzip for efficient storage
    # FIXME: Add error handling for failed backups
    tar -czf backup/$service/${service}_${timestamp}.tar.gz data/$service/
}

function cleanup_volumes() {
    local service=$1
    
    echo "Cleaning up volumes for $service..."
    
    # Maintain backup rotation
    # NOTE: Keeps last 5 backups to balance history vs storage
    # TODO: Make backup retention count configurable
    ls -t backup/$service/ | tail -n +6 | xargs -I {} rm backup/$service/{}
    
    # Remove stale cache files
    # NOTE: 7-day cache retention prevents unbounded growth
    # TODO: Add configurable cache retention period
    find data/$service/cache -type f -atime +7 -delete
}

# Main script entry point
# NOTE: Requires service name as argument
case $1 in
    create)
        create_volumes $2
        ;;
    backup)
        backup_volumes $2
        ;;
    cleanup)
        cleanup_volumes $2
        ;;
    *)
        echo "Usage: $0 {create|backup|cleanup} service_name"
        exit 1
        ;;
esac 