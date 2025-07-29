#!/bin/bash

# Setup script for trade infrastructure
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_DIR="$INFRA_DIR/docker/compose"

echo "Trade Infrastructure Setup"
echo "========================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed (try both commands)
if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker with Compose plugin."
    exit 1
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p "$INFRA_DIR/docker/proxy/nginx/ssl"

# Copy environment file if not exists
if [ ! -f "$INFRA_DIR/configs/.env" ]; then
    echo "Creating .env file from template..."
    if [ -f "$INFRA_DIR/configs/.env.example" ]; then
        cp "$INFRA_DIR/configs/.env.example" "$INFRA_DIR/configs/.env"
        echo "Please edit $INFRA_DIR/configs/.env with your configuration"
    fi
fi

# Build images
echo "Building Docker images..."
cd "$COMPOSE_DIR"

if [ "$1" == "full" ]; then
    echo "Setting up full infrastructure with monitoring and logging..."
    docker compose -f docker-compose.full.yml build
else
    echo "Setting up basic infrastructure..."
    docker compose -f docker-compose.yml build
fi

echo "Setup complete!"
echo ""
echo "To start the services, run:"
if [ "$1" == "full" ]; then
    echo "  cd $COMPOSE_DIR && docker compose -f docker-compose.full.yml up -d"
else
    echo "  cd $COMPOSE_DIR && docker compose -f docker-compose.yml up -d"
fi