#!/bin/bash

# Test all services
echo "Running tests for all services..."

# Test Python services
echo "Testing Python services..."
cd trade_engine && python -m pytest tests/ && cd ..
cd trade_dashboard && python -m pytest tests/ && cd ..

# Test common libraries
echo "Testing common libraries..."
cd libs/common-py && python -m pytest tests/ && cd ../..
cd libs/common-rs && cargo test && cd ../..

# Test Java service  
echo "Testing Java service..."
cd trade_batch && ./gradlew test && cd ..

# Test frontend
echo "Testing frontend..."
cd trade_frontend && npm test && cd ..

echo "All tests completed!"