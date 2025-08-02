#!/bin/bash

# Build all services
echo "Building all services..."

# Build Python services
echo "Building Python services..."
cd trade_engine && pip install -r requirements.txt && cd ..
cd trade_dashboard && pip install -r requirements.txt && cd ..
cd trade_batch && pip install -r requirements.txt && cd ..

# Build common libraries
echo "Building common libraries..."
cd libs/common-py && pip install -e . && cd ../..
cd libs/common-rs && cargo build --release && cd ../..

# Build Java service
echo "Building Java service..."
cd trade_batch && ./gradlew build && cd ..

# Build frontend
echo "Building frontend..."
cd trade_frontend && npm install && npm run build && cd ..

echo "All services built successfully!"