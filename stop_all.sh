#!/bin/bash
# 전체 시스템 종료 스크립트

echo "===================="
echo "Trade System Shutdown"
echo "===================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# PID 디렉토리 확인
if [ ! -d ".pids" ]; then
    echo -e "${YELLOW}No .pids directory found. Trying to find processes...${NC}"
    mkdir -p .pids
fi

# 프로세스 종료 함수
stop_process() {
    local service_name=$1
    local pid_file=".pids/${service_name}.pid"
    
    echo -n "Stopping $service_name... "
    
    if [ -f "$pid_file" ]; then
        PID=$(cat $pid_file)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            echo -e "${GREEN}✓${NC} (PID: $PID)"
            rm $pid_file
        else
            echo -e "${YELLOW}Process not found${NC}"
            rm $pid_file
        fi
    else
        # PID 파일이 없으면 프로세스 이름으로 찾기
        case $service_name in
            "trade_batch")
                pkill -f "spring-boot:run" && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}Not running${NC}"
                ;;
            "trade_dashboard")
                pkill -f "uvicorn app.main:app" && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}Not running${NC}"
                ;;
            "trade_engine")
                pkill -f "python main.py" && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}Not running${NC}"
                ;;
            "trade_frontend")
                pkill -f "npm run dev" && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}Not running${NC}"
                ;;
        esac
    fi
}

echo ""
echo "Stopping services..."
echo "-------------------"

# 역순으로 종료 (시작 순서의 반대)
stop_process "trade_frontend"
stop_process "trade_engine"
stop_process "trade_dashboard"
stop_process "trade_batch"

echo ""
echo "Cleaning up..."
echo "--------------"

# 남은 프로세스 확인
echo -n "Checking for remaining processes... "
REMAINING=$(ps aux | grep -E "(spring-boot:run|uvicorn|npm run dev|python main.py)" | grep -v grep | wc -l)
if [ $REMAINING -eq 0 ]; then
    echo -e "${GREEN}Clean${NC}"
else
    echo -e "${YELLOW}Found $REMAINING remaining processes${NC}"
    ps aux | grep -E "(spring-boot:run|uvicorn|npm run dev|python main.py)" | grep -v grep
fi

# 포트 확인
echo ""
echo "Checking ports..."
echo "----------------"

for port in 8080 8000 5173; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Port $port is still in use${NC}"
    else
        echo -e "${GREEN}Port $port is free${NC}"
    fi
done

echo ""
echo "===================="
echo "Shutdown Complete!"
echo "===================="
echo ""
echo "Note: Infrastructure services (PostgreSQL, Redis) are still running."
echo "To stop them:"
echo "  - PostgreSQL: sudo systemctl stop postgresql"
echo "  - Redis: redis-cli shutdown"
echo ""