#!/bin/bash

# Trade System 배포 스크립트
# 수동으로 서버에서 실행

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Trade System Deployment Script ===${NC}"
echo

# 설정
DEPLOY_DIR="/opt/trade"
REGISTRY_URL="${REGISTRY_URL:-localhost:5000}"
BACKUP_DIR="/opt/trade/backups/$(date +%Y%m%d_%H%M%S)"

# 1. 환경 확인
echo -e "${YELLOW}Checking environment...${NC}"
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file with required variables"
    exit 1
fi

# 환경변수 로드
source "$DEPLOY_DIR/.env"

# 2. Registry 로그인
echo -e "${YELLOW}Logging into Docker Registry...${NC}"
echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY_URL" -u "$REGISTRY_USER" --password-stdin

# 3. 현재 상태 백업
echo -e "${YELLOW}Creating backup...${NC}"
mkdir -p "$BACKUP_DIR"
cd "$DEPLOY_DIR"

# 현재 이미지 태그 저장
docker-compose ps --format json > "$BACKUP_DIR/running_services.json"
cp docker-compose.yml "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"

# 4. 새 이미지 Pull
echo -e "${YELLOW}Pulling latest images...${NC}"
docker-compose pull

# 5. 헬스체크 함수
health_check() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "Checking health of $service..."
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null; then
            echo -e "${GREEN}✓ $service is healthy${NC}"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}✗ $service health check failed${NC}"
    return 1
}

# 6. 순차적 배포
echo -e "${YELLOW}Starting deployment...${NC}"

# Database는 건드리지 않음
services=("trade_batch" "trade_dashboard" "trade_engine" "trade_frontend")

for service in "${services[@]}"; do
    echo
    echo -e "${YELLOW}Deploying $service...${NC}"
    
    # Blue-Green 배포
    docker-compose up -d --no-deps --scale "$service=2" "$service"
    sleep 10
    
    # 헬스체크
    case $service in
        trade_batch)
            if health_check "$service" "http://localhost:8080/actuator/health"; then
                docker-compose up -d --no-deps --remove-orphans "$service"
            else
                echo -e "${RED}Deployment failed for $service${NC}"
                break
            fi
            ;;
        trade_dashboard)
            if health_check "$service" "http://localhost:8000/health"; then
                docker-compose up -d --no-deps --remove-orphans "$service"
            else
                echo -e "${RED}Deployment failed for $service${NC}"
                break
            fi
            ;;
        trade_engine)
            # Engine은 헬스체크 엔드포인트가 없으므로 로그 확인
            if docker-compose logs --tail=50 "$service" | grep -q "Error"; then
                echo -e "${RED}Deployment failed for $service${NC}"
                break
            else
                echo -e "${GREEN}✓ $service started successfully${NC}"
            fi
            ;;
        trade_frontend)
            if health_check "$service" "http://localhost:3000"; then
                docker-compose up -d --no-deps --remove-orphans "$service"
            else
                echo -e "${RED}Deployment failed for $service${NC}"
                break
            fi
            ;;
    esac
done

# 7. 최종 상태 확인
echo
echo -e "${YELLOW}Final status check...${NC}"
docker-compose ps

# 8. 정리
echo
echo -e "${YELLOW}Cleaning up...${NC}"
docker image prune -f

echo
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo
echo "Next steps:"
echo "1. Check logs: docker-compose logs -f"
echo "2. Monitor services: docker-compose ps"
echo "3. If issues occur, rollback: ./rollback.sh $BACKUP_DIR"