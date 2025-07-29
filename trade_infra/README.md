# Trade Infrastructure

This directory contains all infrastructure-related configurations for the Trade System.

## Directory Structure

```
trade_infra/
├── docker/              # Docker configurations
│   ├── compose/        # Docker Compose files
│   ├── proxy/          # Reverse proxy (Nginx)
│   ├── cache/          # Caching layer (Redis)
│   ├── database/       # Database (PostgreSQL)
│   ├── monitoring/     # Monitoring stack (Prometheus, Grafana)
│   └── logging/        # Logging stack (Elasticsearch)
├── scripts/            # Utility scripts
├── configs/            # Configuration files
└── README.md          # This file
```

## Quick Start

### Basic Setup (Required Services Only)

```bash
# Setup and build
./scripts/setup.sh

# Deploy
./scripts/deploy.sh
```

### Full Setup (With Monitoring and Logging)

```bash
# Setup with all services
./scripts/setup.sh full

# Deploy full stack
./scripts/deploy.sh --full
```

### Development Environment

```bash
# Deploy development environment with hot reload
./scripts/deploy.sh --dev
```

## Services

### Core Services
- **PostgreSQL**: Main database (port 5432)
- **Redis**: Caching and session storage (port 6379)
- **Nginx**: Reverse proxy and load balancer (port 80/443)
- **Backend**: FastAPI application (port 8000)
- **Frontend**: SvelteKit application (port 3000)

### Monitoring Stack (Optional)
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Metrics visualization (port 3001)
- **Exporters**: PostgreSQL, Redis, and Node exporters

### Logging Stack (Optional)
- **Elasticsearch**: Log storage and search (port 9200)

## Configuration

1. Copy the example environment file:
   ```bash
   cp configs/.env.example configs/.env
   ```

2. Edit `configs/.env` with your configuration

## Useful Commands

```bash
# View logs
cd docker/compose
docker-compose -f docker-compose.yml logs -f [service_name]

# Stop services
docker-compose -f docker-compose.yml down

# Remove all data
docker-compose -f docker-compose.yml down -v

# Access service shell
docker-compose -f docker-compose.yml exec [service_name] sh
```

## Access Points

- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Prometheus: http://localhost:9090 (full stack only)
- Grafana: http://localhost:3001 (full stack only, admin/admin)
- Elasticsearch: http://localhost:9200 (full stack only)

## Troubleshooting

### Port Conflicts
If you encounter port conflicts, you can modify the port mappings in the docker-compose files.

### IBKR Connection
Ensure IBKR Gateway or TWS is running on the host machine and configured to accept API connections.

### SSL Certificates
Place SSL certificates in `docker/proxy/nginx/ssl/` directory for HTTPS support.