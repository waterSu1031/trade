#!/bin/bash

# Trade System Docker Build Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Parse arguments
BUILD_ENV="${1:-production}"
SERVICE="${2:-all}"

# Validate environment
if [[ "$BUILD_ENV" != "production" && "$BUILD_ENV" != "development" ]]; then
    print_color $RED "Error: Invalid environment. Use 'production' or 'development'"
    exit 1
fi

print_color $GREEN "=== Trade System Docker Build ==="
print_color $YELLOW "Environment: $BUILD_ENV"
print_color $YELLOW "Service: $SERVICE"

# Check prerequisites
if ! command_exists docker; then
    print_color $RED "Error: Docker is not installed"
    exit 1
fi

if ! command_exists docker-compose; then
    print_color $RED "Error: Docker Compose is not installed"
    exit 1
fi

# Navigate to project root
cd "$PROJECT_ROOT"

# Function to build a specific service
build_service() {
    local service=$1
    local dockerfile="Dockerfile"
    
    if [[ "$BUILD_ENV" == "development" ]]; then
        dockerfile="Dockerfile.dev"
    fi
    
    case $service in
        "backend"|"trade_dashboard")
            print_color $YELLOW "Building trade_dashboard..."
            docker build -t trade_dashboard:${BUILD_ENV} \
                -f trade_dashboard/${dockerfile} \
                trade_dashboard/
            ;;
        "frontend"|"trade_frontend")
            print_color $YELLOW "Building trade_frontend..."
            # For production, ensure build args are passed
            if [[ "$BUILD_ENV" == "production" ]]; then
                docker build -t trade_frontend:${BUILD_ENV} \
                    --build-arg VITE_API_URL=${VITE_API_URL:-http://localhost:8000} \
                    --build-arg VITE_WS_URL=${VITE_WS_URL:-ws://localhost:8000} \
                    -f trade_frontend/${dockerfile} \
                    trade_frontend/
            else
                docker build -t trade_frontend:${BUILD_ENV} \
                    -f trade_frontend/${dockerfile} \
                    trade_frontend/
            fi
            ;;
        "batch"|"trade_batch")
            print_color $YELLOW "Building trade_batch..."
            if [[ "$BUILD_ENV" == "production" ]]; then
                # Build JAR first
                cd trade_batch
                ./mvnw clean package -DskipTests
                cd ..
            fi
            docker build -t trade_batch:${BUILD_ENV} \
                -f trade_batch/${dockerfile} \
                trade_batch/
            ;;
        "engine"|"trade_engine")
            print_color $YELLOW "Building trade_engine..."
            docker build -t trade_engine:${BUILD_ENV} \
                -f trade_engine/${dockerfile} \
                trade_engine/
            ;;
        "nginx")
            print_color $YELLOW "Building nginx..."
            docker build -t trade_nginx:latest \
                -f trade_infra/docker/proxy/nginx/Dockerfile \
                trade_infra/docker/proxy/nginx/
            ;;
        *)
            print_color $RED "Unknown service: $service"
            exit 1
            ;;
    esac
}

# Build services
if [[ "$SERVICE" == "all" ]]; then
    # Build all services
    services=("backend" "frontend")
    
    if [[ "$BUILD_ENV" == "production" ]]; then
        services+=("nginx")
    fi
    
    for svc in "${services[@]}"; do
        build_service "$svc"
    done
else
    # Build specific service
    build_service "$SERVICE"
fi

print_color $GREEN "=== Build Complete ==="

# Show next steps
print_color $YELLOW "\nNext steps:"
if [[ "$BUILD_ENV" == "production" ]]; then
    echo "1. Run: cd trade_infra/docker/compose"
    echo "2. Run: docker-compose up -d"
else
    echo "1. Run: cd trade_infra/docker/compose"
    echo "2. Run: docker-compose -f docker-compose.dev.yml up -d"
fi