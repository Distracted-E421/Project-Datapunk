#!/bin/bash

# Wait for Elasticsearch to be ready
until curl -s "http://elasticsearch:9200/_cluster/health" | grep -q '"status":"green\|yellow"'; do
    echo "Waiting for Elasticsearch cluster to be ready..."
    sleep 10
done

# Create general alert rules
echo "Creating general alert rules..."
for rule in $(jq -c '.alert_rules[]' /usr/share/elasticsearch/config/alert-rules.json); do
    name=$(echo $rule | jq -r '.name')
    echo "Creating alert rule: $name"
    
    curl -X PUT "http://elasticsearch:9200/_watcher/watch/${name}" \
         -H "Content-Type: application/json" \
         -d "$rule"
done

# Create service-specific alert rules
echo "Creating service-specific alert rules..."
for rule in $(jq -c '.alert_rules[]' /usr/share/elasticsearch/config/service-alert-rules.json); do
    name=$(echo $rule | jq -r '.name')
    echo "Creating service alert rule: $name"
    
    curl -X PUT "http://elasticsearch:9200/_watcher/watch/${name}" \
         -H "Content-Type: application/json" \
         -d "$rule"
done

# Start watcher
curl -X POST "http://elasticsearch:9200/_watcher/_start"

echo "Alert rules initialized successfully" 