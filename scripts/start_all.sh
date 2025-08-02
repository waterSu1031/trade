#!/bin/bash
# 전체 시스템 시작 스크립트

echo "===================="
echo "Trade System Startup"
echo "===================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 서비스 상태 체크
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "Checking $service_name... "
    if eval $check_command > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 함수: 포트 체크
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Warning: Port $port ($service) is already in use${NC}"
        return 1
    fi
    return 0
}

echo ""
echo "1. Checking prerequisites..."
echo "----------------------------"

# PostgreSQL 체크
check_service "PostgreSQL" "pg_isready -h localhost -p 5432"
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    # PostgreSQL 시작 명령 (시스템에 따라 다름)
    sudo systemctl start postgresql || brew services start postgresql
fi

# Redis 체크
check_service "Redis" "redis-cli ping"
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes
fi

# IBKR Gateway 체크
check_service "IBKR Gateway (Port 4002)" "nc -z localhost 4002"
if [ $? -ne 0 ]; then
    echo -e "${RED}IBKR Gateway is not running on port 4002${NC}"
    echo "Please start IB Gateway in Paper Trading mode"
    read -p "Press enter when ready..."
fi

echo ""
echo "2. Checking port availability..."
echo "--------------------------------"

check_port 8082 "trade_batch"
check_port 8000 "trade_dashboard"
check_port 5173 "trade_frontend"

echo ""
echo "Installing trade_common library..."
echo "----------------------------------"

# trade_common 설치 (모든 Python 서비스에서 사용)
cd trade_common
pip install -e .
cd ..

echo ""
echo "3. Setting environment variables..."
echo "-----------------------------------"

export IBKR_HOST=localhost
export IBKR_PORT=4002
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=trade
export DB_USER=freeksj
export DB_PASSWORD=Lsld1501!
export REDIS_HOST=localhost
export REDIS_PORT=6379
export LOG_LEVEL=INFO

echo "Environment variables set"

echo ""
echo "4. Starting services..."
echo "----------------------"

# .pids 디렉토리 생성
mkdir -p .pids

# trade_batch 시작 (Python으로 변경됨)
echo -e "${GREEN}Starting trade_batch...${NC}"
cd trade_batch
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi
nohup python src/main.py > ../logs/trade_batch_startup.log 2>&1 &
BATCH_PID=$!
echo "trade_batch PID: $BATCH_PID"
deactivate
cd ..

sleep 5

# trade_dashboard 시작
echo -e "${GREEN}Starting trade_dashboard...${NC}"
cd trade_dashboard
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/trade_dashboard_startup.log 2>&1 &
DASHBOARD_PID=$!
echo "trade_dashboard PID: $DASHBOARD_PID"
deactivate
cd ..

sleep 5

# trade_engine 시작
echo -e "${GREEN}Starting trade_engine...${NC}"
cd trade_engine
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi
nohup python main.py > ../logs/trade_engine_startup.log 2>&1 &
ENGINE_PID=$!
echo "trade_engine PID: $ENGINE_PID"
deactivate
cd ..

sleep 5

# trade_frontend 시작
echo -e "${GREEN}Starting trade_frontend...${NC}"
cd trade_frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
nohup npm run dev > ../logs/trade_frontend_startup.log 2>&1 &
FRONTEND_PID=$!
echo "trade_frontend PID: $FRONTEND_PID"
cd ..

# PID 파일 저장
echo $BATCH_PID > .pids/trade_batch.pid
echo $DASHBOARD_PID > .pids/trade_dashboard.pid
echo $ENGINE_PID > .pids/trade_engine.pid
echo $FRONTEND_PID > .pids/trade_frontend.pid

echo ""
echo "5. Waiting for services to be ready..."
echo "-------------------------------------"

sleep 10

# 헬스체크
echo ""
echo "6. Health checks..."
echo "------------------"

check_service "trade_batch" "curl -s http://localhost:8082/health"
check_service "trade_dashboard" "curl -s http://localhost:8000/health"
check_service "trade_frontend" "curl -s http://localhost:5173"

echo ""
echo "===================="
echo "Startup Complete!"
echo "===================="
echo ""
echo "Services running:"
echo "- trade_batch: http://localhost:8082"
echo "- trade_dashboard: http://localhost:8000"
echo "- trade_frontend: http://localhost:5173"
echo ""
echo "Logs available at: ./logs/"
echo ""
echo "To stop all services, run: ./stop_all.sh"
echo ""