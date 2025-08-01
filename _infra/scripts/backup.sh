#!/bin/bash

# Backup script for Trade System
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$INFRA_DIR/volumes/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Load environment variables
PROJECT_ROOT="$(dirname "$(dirname "$INFRA_DIR")")"
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
elif [ -f "$PROJECT_ROOT/.env.production" ]; then
    export $(cat "$PROJECT_ROOT/.env.production" | grep -v '^#' | xargs)
fi

# Default values
DB_USER=${DB_USER:-trade_user}
DB_NAME=${DB_NAME:-trade_db}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

echo "Trade System Backup"
echo "==================="
echo "Timestamp: $TIMESTAMP"

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR/postgresql"
mkdir -p "$BACKUP_DIR/redis"

# Backup PostgreSQL
echo "Backing up PostgreSQL database..."
docker exec trade_db pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/postgresql/trade_db_$TIMESTAMP.sql"
if [ $? -eq 0 ]; then
    echo "PostgreSQL backup completed: trade_db_$TIMESTAMP.sql"
    # Compress the backup
    gzip "$BACKUP_DIR/postgresql/trade_db_$TIMESTAMP.sql"
    echo "Compressed to: trade_db_$TIMESTAMP.sql.gz"
else
    echo "Error: PostgreSQL backup failed!"
    exit 1
fi

# Backup Redis
echo "Backing up Redis data..."
docker exec trade_redis redis-cli BGSAVE
sleep 2  # Wait for background save to start
# Wait for background save to complete
while [ $(docker exec trade_redis redis-cli LASTSAVE) -eq $(docker exec trade_redis redis-cli LASTSAVE) ]; do
    sleep 1
done
docker cp trade_redis:/data/dump.rdb "$BACKUP_DIR/redis/redis_dump_$TIMESTAMP.rdb"
if [ $? -eq 0 ]; then
    echo "Redis backup completed: redis_dump_$TIMESTAMP.rdb"
else
    echo "Warning: Redis backup may have failed!"
fi

# Clean old backups
echo "Cleaning old backups (older than $BACKUP_RETENTION_DAYS days)..."
find "$BACKUP_DIR/postgresql" -name "*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS -delete
find "$BACKUP_DIR/redis" -name "*.rdb" -mtime +$BACKUP_RETENTION_DAYS -delete

echo ""
echo "Backup completed successfully!"
echo "Backup location: $BACKUP_DIR"

# List recent backups
echo ""
echo "Recent backups:"
echo "PostgreSQL:"
ls -lht "$BACKUP_DIR/postgresql" | head -5
echo ""
echo "Redis:"
ls -lht "$BACKUP_DIR/redis" | head -5