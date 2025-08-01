# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive automated trading system consisting of multiple microservices that support both backtesting and live trading through Interactive Brokers (IBKR). The system uses a modular architecture with separate services for different functions.

## System Architecture

### Microservices

1. **Trade Engine** (`trade_engine/`)
   - Python-based algorithmic trading engine
   - Supports both backtesting and live trading through IBKR
   - Core components: data handling, strategy execution, order management
   - Main entry: `python main.py`

2. **Trade Dashboard** (`trade_dashboard/`)
   - FastAPI-based backend service for monitoring and analytics
   - SQLAlchemy ORM for database operations
   - WebSocket support for real-time updates
   - Main entry: `uvicorn main:app`

3. **Trade Batch** (`trade_batch/`)
   - Spring Batch application for scheduled trading jobs
   - Handles batch data processing and strategy execution
   - Java/Spring Boot based
   - Main entry: `./gradlew bootRun`

4. **Trade Frontend** (`trade_frontend/`)
   - SvelteKit-based web application
   - Real-time trading status monitoring
   - Backtesting interface and statistics visualization
   - Main entry: `npm run dev`

### Infrastructure (`_platform/`)

- **Docker**: Containerized deployment with Docker Compose
- **PostgreSQL**: Primary database for trade data
- **Redis**: Caching and real-time data
- **IBKR Gateway**: Connection to Interactive Brokers

## Development Commands

### Running Individual Services

```bash
# Infrastructure
make infra-up       # Start PostgreSQL and Redis
make infra-down     # Stop infrastructure

# Trade Engine
cd trade_engine
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python main.py

# Trade Dashboard
cd trade_dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Trade Batch
cd trade_batch
./gradlew bootRun

# Trade Frontend
cd trade_frontend
npm install
npm run dev
```

### Common Commands

- `make lint` - Run linting for all services
- `make test` - Run tests for all services
- `make build` - Build all services
- `make clean` - Clean build artifacts

## Configuration

### Environment Variables

All services use environment variables from the root `.env` file. Key variables:

- **IBKR Settings**: `IBKR_HOST`, `IBKR_PORT`, `IBKR_USERNAME`, `IBKR_PASSWORD`
- **Database**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Redis**: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- **Service Ports**: `DASHBOARD_PORT`, `ENGINE_PORT`, `BATCH_PORT`, `FRONTEND_PORT`

### Trading Modes

1. **Paper Trading**: Uses IBKR port 4002 (default)
2. **Live Trading**: Uses IBKR port 4001
3. **Backtesting**: Historical data analysis without broker connection

## Key Technologies

### Backend
- **Python**: FastAPI, SQLAlchemy, ib-insync, vectorbtpro
- **Java**: Spring Boot, Spring Batch, Gradle
- **Databases**: PostgreSQL (primary), SQLite (trade engine local cache)
- **Messaging**: Redis for caching and pub/sub

### Frontend
- **Framework**: SvelteKit with TypeScript
- **Styling**: Tailwind CSS with DaisyUI
- **State Management**: Svelte stores
- **Real-time**: WebSocket connections

## Architecture Patterns

### Data Flow
1. IBKR Gateway → Trade Engine → Database
2. Trade Engine → Order Execution → IBKR
3. Database → Dashboard API → Frontend
4. Batch Jobs → Database → Analytics

### Key Design Decisions
- Microservices architecture for scalability
- Event-driven communication via Redis
- Hybrid deployment (Docker for infra, native for services during development)
- Type-safe interfaces across all services

## Testing Strategy

- Unit tests for individual components
- Integration tests for service interactions
- Backtesting framework for strategy validation
- Manual testing with IBKR paper trading account

## Security Considerations

- Environment-based configuration (no hardcoded credentials)
- JWT authentication for API endpoints
- CORS configuration for frontend-backend communication
- Database connection pooling and security

## Future Enhancements

- Kubernetes deployment for production
- ML model integration for advanced strategies
- Real-time performance monitoring dashboard
- Multi-broker support beyond IBKR
- Advanced risk management features