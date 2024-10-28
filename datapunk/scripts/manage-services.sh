#!/bin/bash

function start_service() {
    local service=$1
    echo "Starting $service..."
    docker-compose -f ./$service/docker-compose.yml up -d
}

function stop_service() {
    local service=$1
    echo "Stopping $service..."
    docker-compose -f ./$service/docker-compose.yml down
}

case "$1" in
    "start")
        case "$2" in
            "all")
                docker-compose up -d
                ;;
            "frontend"|"backend"|"db")
                start_service $2
                ;;
            *)
                echo "Invalid service. Use: frontend, backend, db, or all"
                exit 1
                ;;
        esac
        ;;
    "stop")
        case "$2" in
            "all")
                docker-compose down
                ;;
            "frontend"|"backend"|"db")
                stop_service $2
                ;;
            *)
                echo "Invalid service. Use: frontend, backend, db, or all"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "Usage: $0 {start|stop} {frontend|backend|db|all}"
        exit 1
        ;;
esac
