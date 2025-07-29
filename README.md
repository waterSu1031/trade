# Trade System - Monorepo

An automated trading system built with microservices architecture, integrating with Interactive Brokers (IBKR) for real-time trading operations.

## 🏗️ Architecture Overview

```
trade/
├── trade_batch/        # Spring Boot batch processing service
├── trade_dashboard/    # FastAPI dashboard backend
├── trade_engine/       # Python trading engine with strategies
├── trade_frontend/     # Svelte-based web interface
├── trade_infra/        # Infrastructure and deployment configs
└── common/            # Shared libraries and resources
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Java 17 (for trade_batch)
- Python 3.11+ (for trade_dashboard, trade_engine)
- Node.js 18+ (for trade_frontend)
- Interactive Brokers TWS/Gateway

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/waterSu1031/trade.git
cd trade
```

2. Copy environment templates:
```bash
cp trade_infra/configs/.env.example .env
# Edit .env with your configurations
```

3. Start infrastructure services:
```bash
cd trade_infra/docker/compose
docker-compose up -d
```

### Running Services

#### Option 1: Using Docker Compose (Recommended)
```bash
cd trade_infra/docker/compose
docker-compose -f docker-compose.full.yml up
```

#### Option 2: Individual Services

**Trade Batch (Spring Boot):**
```bash
cd trade_batch
./mvnw spring-boot:run
```

**Trade Dashboard (FastAPI):**
```bash
cd trade_dashboard
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Trade Engine (Python):**
```bash
cd trade_engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Trade Frontend (Svelte):**
```bash
cd trade_frontend
npm install
npm run dev
```

## 📋 Services Description

### trade_batch
- **Purpose**: Batch data collection and processing
- **Tech Stack**: Java 17, Spring Boot, Spring Batch
- **Port**: 8080
- **Features**:
  - Historical data collection from IBKR
  - Scheduled batch jobs
  - Data persistence to PostgreSQL

### trade_dashboard
- **Purpose**: Real-time dashboard and API backend
- **Tech Stack**: Python, FastAPI, SQLAlchemy
- **Port**: 8000
- **Features**:
  - WebSocket for real-time updates
  - RESTful API endpoints
  - Position and trade monitoring

### trade_engine
- **Purpose**: Trading strategy execution engine
- **Tech Stack**: Python, ib_insync, vectorbtpro
- **Port**: N/A (Backend service)
- **Features**:
  - Strategy backtesting
  - Live trading execution
  - Risk management

### trade_frontend
- **Purpose**: Web-based user interface
- **Tech Stack**: Svelte, TypeScript, Tailwind CSS
- **Port**: 5173 (dev), 3000 (production)
- **Features**:
  - Real-time dashboard
  - Trade monitoring
  - Strategy configuration

## 🔧 Configuration

### Database
- PostgreSQL is used as the main database
- Connection settings in `.env` file
- Schema migrations in `trade_infra/configs/database-schema.sql`

### IBKR Connection
- Configure TWS/Gateway connection in each service's config
- Paper trading: Port 4002
- Live trading: Port 4001

### Environment Variables
Key environment variables (see `.env.example`):
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trade_db
DB_USER=trade_user
DB_PASSWORD=your_password

IBKR_HOST=localhost
IBKR_PORT=4002
IBKR_CLIENT_ID=1
```

## 🧪 Testing

Run all tests:
```bash
make test-all
```

Service-specific tests:
```bash
# Java/Spring Boot
cd trade_batch && ./mvnw test

# Python services
cd trade_dashboard && pytest
cd trade_engine && pytest

# Frontend
cd trade_frontend && npm test
```

## 📊 Monitoring

- **Prometheus**: Metrics collection (http://localhost:9090)
- **Grafana**: Visualization (http://localhost:3001)
- **Health checks**: Each service exposes `/health` endpoint

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For issues and questions:
- Create an issue in the GitHub repository
- Check existing documentation in `/docs`
- Review service-specific README files