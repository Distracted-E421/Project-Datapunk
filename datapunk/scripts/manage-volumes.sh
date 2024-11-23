#!/bin/bash

# Volume management script for Datapunk services

function create_volumes() {
    local service=$1
    
    echo "Creating volumes for $service..."
    
    # Create data directories
    mkdir -p data/$service
    mkdir -p backup/$service
    
    # Set permissions
    chown -R datapunk:datapunk data/$service
    chown -R datapunk:datapunk backup/$service
    chmod -R 755 data/$service
    chmod -R 755 backup/$service
}

function backup_volumes() {
    local service=$1
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    echo "Backing up volumes for $service..."
    
    # Create backup
    tar -czf backup/$service/${service}_${timestamp}.tar.gz data/$service/
}

function cleanup_volumes() {
    local service=$1
    
    echo "Cleaning up volumes for $service..."
    
    # Remove old backups (keep last 5)
    ls -t backup/$service/ | tail -n +6 | xargs -I {} rm backup/$service/{}
    
    # Clean cache
    find data/$service/cache -type f -atime +7 -delete
}

# Main script
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