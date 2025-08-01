# Trade System Monorepo Makefile
.PHONY: help install-all build-all test-all clean-all start-infra stop-infra

# Default target
help:
	@echo "Trade System Monorepo - Available Commands:"
	@echo "  make install-all    - Install dependencies for all services"
	@echo "  make build-all      - Build all services"
	@echo "  make test-all       - Run tests for all services"
	@echo "  make clean-all      - Clean build artifacts"
	@echo "  make start-infra    - Start infrastructure services"
	@echo "  make stop-infra     - Stop infrastructure services"
	@echo "  make dev            - Start all services in development mode"
	@echo "  make logs-<service> - Show logs for specific service"

# Install dependencies for all services
install-all: install-batch install-dashboard install-engine install-frontend

install-batch:
	@echo "Installing dependencies for trade_batch..."
	cd trade_batch && ./mvnw clean install -DskipTests

install-dashboard:
	@echo "Installing dependencies for trade_dashboard..."
	cd trade_dashboard && python -m pip install -r requirements.txt

install-engine:
	@echo "Installing dependencies for trade_engine..."
	cd trade_engine && python -m pip install -r requirements.txt

install-frontend:
	@echo "Installing dependencies for trade_frontend..."
	cd trade_frontend && npm install

# Build all services
build-all: build-batch build-dashboard build-engine build-frontend

build-batch:
	@echo "Building trade_batch..."
	cd trade_batch && ./mvnw clean package -DskipTests

build-dashboard:
	@echo "Building trade_dashboard..."
	cd trade_dashboard && python -m py_compile app/**/*.py

build-engine:
	@echo "Building trade_engine..."
	cd trade_engine && python -m py_compile src/**/*.py

build-frontend:
	@echo "Building trade_frontend..."
	cd trade_frontend && npm run build

# Run tests for all services
test-all: test-batch test-dashboard test-engine test-frontend

test-batch:
	@echo "Testing trade_batch..."
	cd trade_batch && ./mvnw test

test-dashboard:
	@echo "Testing trade_dashboard..."
	cd trade_dashboard && python -m pytest

test-engine:
	@echo "Testing trade_engine..."
	cd trade_engine && python -m pytest

test-frontend:
	@echo "Testing trade_frontend..."
	cd trade_frontend && npm test

# Clean build artifacts
clean-all: clean-batch clean-dashboard clean-engine clean-frontend

clean-batch:
	@echo "Cleaning trade_batch..."
	cd trade_batch && ./mvnw clean

clean-dashboard:
	@echo "Cleaning trade_dashboard..."
	find trade_dashboard -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find trade_dashboard -type f -name "*.pyc" -delete 2>/dev/null || true

clean-engine:
	@echo "Cleaning trade_engine..."
	find trade_engine -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find trade_engine -type f -name "*.pyc" -delete 2>/dev/null || true

clean-frontend:
	@echo "Cleaning trade_frontend..."
	cd trade_frontend && rm -rf dist .svelte-kit

# Infrastructure management
start-infra:
	@echo "Starting infrastructure services..."
	cd _platform/infra/docker/compose && docker-compose up -d

stop-infra:
	@echo "Stopping infrastructure services..."
	cd _platform/infra/docker/compose && docker-compose down

# Development mode - start all services
dev: start-infra
	@echo "Starting all services in development mode..."
	@echo "Note: This requires multiple terminal windows or a process manager"
	@echo ""
	@echo "Run these commands in separate terminals:"
	@echo "1. cd trade_batch && ./mvnw spring-boot:run"
	@echo "2. cd trade_dashboard && uvicorn app.main:app --reload"
	@echo "3. cd trade_engine && python main.py"
	@echo "4. cd trade_frontend && npm run dev"

# Service-specific logs
logs-infra:
	cd _platform/infra/docker/compose && docker-compose logs -f

logs-batch:
	tail -f trade_batch/logs/trade-batch.log

logs-dashboard:
	tail -f trade_dashboard/logs/app.log

logs-engine:
	tail -f trade_engine/logs/trade.log

# Docker operations
docker-build:
	@echo "Building Docker images for all services..."
	cd _platform/infra/docker/compose && docker-compose -f docker-compose.full.yml build

docker-up:
	@echo "Starting all services with Docker..."
	cd _platform/infra/docker/compose && docker-compose -f docker-compose.full.yml up -d

docker-down:
	@echo "Stopping all Docker services..."
	cd _platform/infra/docker/compose && docker-compose -f docker-compose.full.yml down

# Database operations
db-migrate:
	@echo "Running database migrations..."
	cd _platform/infra && ./scripts/migrate.sh

db-backup:
	@echo "Backing up database..."
	cd _platform/infra && ./scripts/backup.sh

db-restore:
	@echo "Restoring database..."
	@echo "Usage: make db-restore BACKUP_FILE=backup_20240101.sql"
	cd _platform/infra && ./scripts/restore.sh $(BACKUP_FILE)

# Utility commands
check-ports:
	@echo "Checking if required ports are available..."
	@echo "PostgreSQL (5432):" && lsof -i :5432 || echo "✓ Available"
	@echo "Redis (6379):" && lsof -i :6379 || echo "✓ Available"
	@echo "Batch API (8080):" && lsof -i :8080 || echo "✓ Available"
	@echo "Dashboard API (8000):" && lsof -i :8000 || echo "✓ Available"
	@echo "Frontend Dev (5173):" && lsof -i :5173 || echo "✓ Available"

health-check:
	@echo "Checking health of all services..."
	@curl -s http://localhost:8080/health || echo "❌ trade_batch not responding"
	@curl -s http://localhost:8000/health || echo "❌ trade_dashboard not responding"
	@curl -s http://localhost:5173 || echo "❌ trade_frontend not responding"

# Git operations
git-status:
	@echo "Checking git status for all projects..."
	@for dir in trade_batch trade_dashboard trade_engine trade_frontend _platform; do \
		echo "\n=== $$dir ==="; \
		git -C . status --porcelain | grep "$$dir/" || echo "✓ Clean"; \
	done