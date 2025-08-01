#!/bin/bash

# Restore script for Trade System
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$INFRA_DIR/volumes/backups"

# Load environment variables
if [ -f "$INFRA_DIR/configs/.env" ]; then
    export $(cat "$INFRA_DIR/configs/.env" | grep -v '^#' | xargs)
fi

# Default values
DB_USER=${DB_USER:-trade_user}
DB_NAME=${DB_NAME:-trade_db}

echo "Trade System Restore"
echo "===================="

# Function to list available backups
list_backups() {
    echo "Available PostgreSQL backups:"
    ls -1 "$BACKUP_DIR/postgresql"/*.sql.gz 2>/dev/null | nl -v 0 || echo "No PostgreSQL backups found"
    echo ""
    echo "Available Redis backups:"
    ls -1 "$BACKUP_DIR/redis"/*.rdb 2>/dev/null | nl -v 0 || echo "No Redis backups found"
}

# Function to restore PostgreSQL
restore_postgresql() {
    local backup_file=$1
    echo "Restoring PostgreSQL from: $backup_file"
    
    # Decompress if needed
    if [[ $backup_file == *.gz ]]; then
        echo "Decompressing backup..."
        gunzip -c "$backup_file" | docker exec -i trade_db psql -U $DB_USER -d $DB_NAME
    else
        docker exec -i trade_db psql -U $DB_USER -d $DB_NAME < "$backup_file"
    fi
    
    if [ $? -eq 0 ]; then
        echo "PostgreSQL restore completed successfully!"
    else
        echo "Error: PostgreSQL restore failed!"
        exit 1
    fi
}

# Function to restore Redis
restore_redis() {
    local backup_file=$1
    echo "Restoring Redis from: $backup_file"
    
    # Stop Redis to restore
    echo "Stopping Redis..."
    docker exec trade_redis redis-cli SHUTDOWN NOSAVE
    sleep 2
    
    # Copy backup file
    docker cp "$backup_file" trade_redis:/data/dump.rdb
    
    # Restart Redis container
    echo "Restarting Redis..."
    docker restart trade_redis
    sleep 5
    
    if [ $? -eq 0 ]; then
        echo "Redis restore completed successfully!"
    else
        echo "Error: Redis restore failed!"
        exit 1
    fi
}

# Main menu
if [ $# -eq 0 ]; then
    echo "Usage: $0 [postgresql|redis|all] [backup_file]"
    echo ""
    list_backups
    exit 0
fi

case $1 in
    postgresql|pg|db)
        if [ -z "$2" ]; then
            echo "Please specify a PostgreSQL backup file"
            echo ""
            echo "Available PostgreSQL backups:"
            ls -1 "$BACKUP_DIR/postgresql"/*.sql.gz 2>/dev/null || echo "No backups found"
            exit 1
        fi
        restore_postgresql "$2"
        ;;
    redis)
        if [ -z "$2" ]; then
            echo "Please specify a Redis backup file"
            echo ""
            echo "Available Redis backups:"
            ls -1 "$BACKUP_DIR/redis"/*.rdb 2>/dev/null || echo "No backups found"
            exit 1
        fi
        restore_redis "$2"
        ;;
    all)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Please specify both PostgreSQL and Redis backup files"
            echo "Usage: $0 all <postgresql_backup> <redis_backup>"
            echo ""
            list_backups
            exit 1
        fi
        restore_postgresql "$2"
        restore_redis "$3"
        ;;
    *)
        echo "Unknown option: $1"
        echo "Usage: $0 [postgresql|redis|all] [backup_file]"
        exit 1
        ;;
esac

echo ""
echo "Restore completed!"