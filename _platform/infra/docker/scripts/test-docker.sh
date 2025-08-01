#!/bin/bash

# Docker Services Test Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check service health
check_service() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1
    
    print_color $YELLOW "Checking $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            print_color $GREEN "✓ $service_name is healthy"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_color $RED "✗ $service_name failed to respond"
    return 1
}

# Function to check Docker container status
check_container() {
    local container_name=$1
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        local status=$(docker inspect -f '{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-health-check")
        
        if [[ "$status" == "healthy" ]] || [[ "$status" == "no-health-check" ]]; then
            print_color $GREEN "✓ Container $container_name is running"
            return 0
        else
            print_color $YELLOW "⚠ Container $container_name is running but not healthy (status: $status)"
            return 1
        fi
    else
        print_color $RED "✗ Container $container_name is not running"
        return 1
    fi
}

print_color $BLUE "=== Trade System Docker Test ==="
print_color $YELLOW "Testing Docker services and connectivity..."

# Change to compose directory
cd "$PROJECT_ROOT/trade_infra/docker/compose"

# Check if services are running
print_color $BLUE "\n1. Checking Docker containers..."
services=("trade_db" "trade_redis" "trade_backend" "trade_frontend")
all_running=true

for service in "${services[@]}"; do
    if ! check_container "$service"; then
        all_running=false
    fi
done

if ! $all_running; then
    print_color $RED "\nSome services are not running. Starting them..."
    docker-compose up -d
    sleep 10
fi

# Test database connection
print_color $BLUE "\n2. Testing PostgreSQL connection..."
if docker exec trade_db psql -U trade_user -d trade_db -c "SELECT 1;" > /dev/null 2>&1; then
    print_color $GREEN "✓ PostgreSQL is accessible"
else
    print_color $RED "✗ PostgreSQL connection failed"
fi

# Test Redis connection
print_color $BLUE "\n3. Testing Redis connection..."
if docker exec trade_redis redis-cli ping | grep -q "PONG"; then
    print_color $GREEN "✓ Redis is accessible"
else
    print_color $RED "✗ Redis connection failed"
fi

# Test backend API
print_color $BLUE "\n4. Testing backend API..."
check_service "Backend API" "http://localhost:8000/health"

# Test frontend
print_color $BLUE "\n5. Testing frontend..."
check_service "Frontend" "http://localhost:3000"

# Test WebSocket connection
print_color $BLUE "\n6. Testing WebSocket endpoint..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ws | grep -q "426"; then
    print_color $GREEN "✓ WebSocket endpoint is available (upgrade required)"
else
    print_color $YELLOW "⚠ WebSocket endpoint may not be configured"
fi

# Show logs if requested
if [[ "$1" == "--logs" ]]; then
    print_color $BLUE "\n7. Recent logs..."
    for service in "${services[@]}"; do
        print_color $YELLOW "\n--- $service logs ---"
        docker logs --tail 10 "$service" 2>&1
    done
fi

# Summary
print_color $BLUE "\n=== Test Summary ==="
print_color $YELLOW "All critical services should be running and healthy."
print_color $YELLOW "If any service failed, check logs with: docker-compose logs <service-name>"

# Show useful commands
print_color $BLUE "\nUseful commands:"
echo "- View all logs: docker-compose logs -f"
echo "- Restart services: docker-compose restart"
echo "- Stop services: docker-compose down"
echo "- Remove volumes: docker-compose down -v"