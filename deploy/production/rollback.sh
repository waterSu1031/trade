#!/bin/bash

# 롤백 스크립트
# 사용법: ./rollback.sh /opt/trade/backups/20240101_120000

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ $# -eq 0 ]; then
    echo -e "${RED}Usage: $0 <backup_directory>${NC}"
    echo "Available backups:"
    ls -la /opt/trade/backups/
    exit 1
fi

BACKUP_DIR="$1"
DEPLOY_DIR="/opt/trade"

echo -e "${YELLOW}=== Rollback Script ===${NC}"
echo "Rolling back to: $BACKUP_DIR"
echo

# 1. 백업 확인
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup directory not found!${NC}"
    exit 1
fi

# 2. 설정 복원
echo -e "${YELLOW}Restoring configuration...${NC}"
cd "$DEPLOY_DIR"
cp "$BACKUP_DIR/docker-compose.yml" .
cp "$BACKUP_DIR/.env" .

# 3. 이전 버전으로 롤백
echo -e "${YELLOW}Rolling back services...${NC}"
docker-compose down
docker-compose up -d

# 4. 상태 확인
echo
echo -e "${YELLOW}Checking status...${NC}"
sleep 10
docker-compose ps

echo
echo -e "${GREEN}=== Rollback Complete ===${NC}"