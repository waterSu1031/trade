#!/bin/bash

# Stop development environment
echo "Stopping development environment..."

# Stop all containers
docker-compose -f infra/docker/docker-compose.base.yml down

echo "Development environment stopped!"