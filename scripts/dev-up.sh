#!/bin/bash

# Start development environment
echo "Starting development environment..."

# Start infrastructure
echo "Starting infrastructure services..."
docker-compose -f infra/docker/docker-compose.base.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check health
echo "Checking service health..."
docker ps

echo "Development environment is ready!"
echo "PostgreSQL: localhost:5432"
echo "Redis: localhost:6379"
echo "Portainer: http://localhost:9000"