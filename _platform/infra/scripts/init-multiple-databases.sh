#!/bin/bash
set -e
set -u

function create_user_and_database() {
    local database=$1
    echo "Creating database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_user_and_database $db
    done
    
    # Create TimescaleDB extension in data_db
    echo "Creating TimescaleDB extension in data_db"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d data_db <<-EOSQL
        CREATE EXTENSION IF NOT EXISTS timescaledb;
EOSQL
fi

