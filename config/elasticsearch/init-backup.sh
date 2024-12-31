#!/bin/bash

# Wait for Elasticsearch to be ready
until curl -s "http://elasticsearch:9200/_cluster/health" | grep -q '"status":"green\|yellow"'; do
    echo "Waiting for Elasticsearch cluster to be ready..."
    sleep 10
done

# Create backup repository
curl -X PUT "http://elasticsearch:9200/_snapshot/datapunk_backup" \
     -H "Content-Type: application/json" \
     -d @/usr/share/elasticsearch/config/backup-policy.json

# Create snapshot lifecycle policy
curl -X PUT "http://elasticsearch:9200/_slm/policy/daily_backup" \
     -H "Content-Type: application/json" \
     -d @/usr/share/elasticsearch/config/backup-policy.json

# Start snapshot lifecycle management
curl -X POST "http://elasticsearch:9200/_slm/start"

echo "Backup configuration initialized successfully" 