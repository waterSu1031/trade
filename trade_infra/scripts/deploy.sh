#!/bin/bash

# Deploy script for trade infrastructure
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_DIR="$INFRA_DIR/docker/compose"

# Default to production compose file
COMPOSE_FILE="docker-compose.yml"
ENVIRONMENT="production"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            COMPOSE_FILE="docker-compose.dev.yml"
            ENVIRONMENT="development"
            shift
            ;;
        --full)
            COMPOSE_FILE="docker-compose.full.yml"
            ENVIRONMENT="production-full"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --dev   Deploy development environment"
            echo "  --full  Deploy full infrastructure with monitoring"
            echo "  --help  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Deploying Trade Infrastructure ($ENVIRONMENT)"
echo "==========================================="

cd "$COMPOSE_DIR"

# Pull latest images
echo "Pulling latest images..."
docker compose -f "$COMPOSE_FILE" pull

# Build custom images
echo "Building custom images..."
docker compose -f "$COMPOSE_FILE" build

# Start services
echo "Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Show status
echo ""
echo "Deployment complete! Service status:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "Access points:"
echo "  - Frontend: http://localhost"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"

if [ "$COMPOSE_FILE" == "docker-compose.full.yml" ]; then
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3001 (admin/admin)"
    echo "  - Elasticsearch: http://localhost:9200"
fi