#!/bin/bash

# Production deployment script
echo "Deploying to production..."

# Build all services
./scripts/build-all.sh

# Run tests
./scripts/test-all.sh

# Build Docker images
echo "Building Docker images..."
docker build -t trade-engine:latest trade_engine/
docker build -t trade-dashboard:latest trade_dashboard/
docker build -t trade-batch:latest trade_batch/
docker build -t trade-frontend:latest trade_frontend/

# Deploy using production configuration
echo "Deploying with production configuration..."
docker-compose -f docker-compose.prod.yml up -d

echo "Production deployment completed!"