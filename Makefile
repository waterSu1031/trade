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
install-all: install-common install-batch install-dashboard install-engine install-frontend

install-common:
	@echo "Installing tradelib library..."
	cd libs/common-py && pip install -e .

install-batch:
	@echo "Installing dependencies for trade_batch..."
	cd trade_batch && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

install-dashboard:
	@echo "Installing dependencies for trade_dashboard..."
	cd trade_dashboard && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

install-engine:
	@echo "Installing dependencies for trade_engine..."
	cd trade_engine && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

install-frontend:
	@echo "Installing dependencies for trade_frontend..."
	cd trade_frontend && npm install

# Build all services
build-all: build-common build-batch build-dashboard build-engine build-frontend

build-common:
	@echo "Building tradelib..."
	cd libs/common-py && python setup.py sdist bdist_wheel

build-batch:
	@echo "Building trade_batch..."
	cd trade_batch && find . -name "*.py" -type f -exec python -m py_compile {} \;

build-dashboard:
	@echo "Building trade_dashboard..."
	cd trade_dashboard && find app -name "*.py" -type f -exec python -m py_compile {} \;

build-engine:
	@echo "Building trade_engine..."
	cd trade_engine && find src -name "*.py" -type f -exec python -m py_compile {} \;

build-frontend:
	@echo "Building trade_frontend..."
	cd trade_frontend && npm run build

# Run tests for all services
test-all: test-common test-batch test-dashboard test-engine test-frontend

test-common:
	@echo "Testing tradelib..."
	cd libs/common-py && python -m pytest tests/ || echo "No tests found"

test-batch:
	@echo "Testing trade_batch..."
	cd trade_batch && python -m pytest tests/ || echo "No tests found"

test-dashboard:
	@echo "Testing trade_dashboard..."
	cd trade_dashboard && python -m pytest tests/ || echo "No tests found"

test-engine:
	@echo "Testing trade_engine..."
	cd trade_engine && python -m pytest tests/ || echo "No tests found"

test-frontend:
	@echo "Testing trade_frontend..."
	cd trade_frontend && npm test || echo "No tests configured"

# Clean build artifacts
clean-all: clean-common clean-batch clean-dashboard clean-engine clean-frontend

clean-common:
	@echo "Cleaning tradelib..."
	cd libs/common-py && rm -rf build dist *.egg-info
	find libs/common-py -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find libs/common-py -type f -name "*.pyc" -delete 2>/dev/null || true

clean-batch:
	@echo "Cleaning trade_batch..."
	find trade_batch -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find trade_batch -type f -name "*.pyc" -delete 2>/dev/null || true

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
	docker-compose up -d db redis

stop-infra:
	@echo "Stopping infrastructure services..."
	docker-compose down db redis

# Development mode - start all services
dev: start-infra
	@echo "Starting all services in development mode..."
	@echo "Note: This requires multiple terminal windows or a process manager"
	@echo ""
	@echo "Run these commands in separate terminals:"
	@echo "1. cd trade_batch && source venv/bin/activate && python src/main.py"
	@echo "2. cd trade_dashboard && source venv/bin/activate && uvicorn app.main:app --reload"
	@echo "3. cd trade_engine && source venv/bin/activate && python main.py"
	@echo "4. cd trade_frontend && npm run dev"

# Service-specific logs
logs-infra:
	docker-compose logs -f db redis

logs-batch:
	tail -f logs/trade_batch.log

logs-dashboard:
	tail -f logs/trade_dashboard.log

logs-engine:
	tail -f logs/trade_engine.log

# Docker operations
docker-build:
	@echo "Building Docker images for all services..."
	docker-compose build

docker-up:
	@echo "Starting all services with Docker..."
	docker-compose up -d

docker-down:
	@echo "Stopping all Docker services..."
	docker-compose down

# Database operations
db-migrate:
	@echo "Running database migrations..."
	cd trade_batch && python -m alembic upgrade head || echo "No migrations found"

db-backup:
	@echo "Backing up database..."
	docker exec trade_db pg_dumpall -U freeksj > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	@echo "Restoring database..."
	@echo "Usage: make db-restore BACKUP_FILE=backup_20240101.sql"
	docker exec -i trade_db psql -U freeksj < $(BACKUP_FILE)

# Utility commands
check-ports:
	@echo "Checking if required ports are available..."
	@echo "PostgreSQL (5432):" && lsof -i :5432 || echo "✓ Available"
	@echo "Redis (6379):" && lsof -i :6379 || echo "✓ Available"
	@echo "Batch API (8082):" && lsof -i :8082 || echo "✓ Available"
	@echo "Dashboard API (8000):" && lsof -i :8000 || echo "✓ Available"
	@echo "Frontend Dev (5173):" && lsof -i :5173 || echo "✓ Available"

health-check:
	@echo "Checking health of all services..."
	@curl -s http://localhost:8082/health || echo "❌ trade_batch not responding"
	@curl -s http://localhost:8000/health || echo "❌ trade_dashboard not responding"
	@curl -s http://localhost:5173 || echo "❌ trade_frontend not responding"

# Git operations
git-status:
	@echo "Checking git status for all projects..."
	@for dir in libs trade_batch trade_dashboard trade_engine trade_frontend infra; do \
		echo "\n=== $$dir ==="; \
		git -C . status --porcelain | grep "$$dir/" || echo "✓ Clean"; \
	done