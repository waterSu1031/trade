# 전체 시스템 실행 전 체크리스트

## 1. 환경 변수 설정 확인

### 필수 환경 변수
```bash
# IBKR 연결
IBKR_HOST=localhost
IBKR_PORT=4002  # 개발: 4002, 운영: 4001

# 데이터베이스
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trade_db
DB_USER=freeksj
DB_PASSWORD=freeksj

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 로깅
LOG_LEVEL=INFO
```

### 서비스별 Client ID
- trade_batch: 1
- trade_dashboard: 2  
- trade_engine: 3

## 2. 사전 준비사항

### IBKR Gateway/TWS
- [ ] IB Gateway 실행 중
- [ ] Paper Trading 모드 (포트 4002)
- [ ] API 연결 허용 설정
- [ ] 로컬호스트 연결 허용

### 데이터베이스
- [ ] PostgreSQL 실행 중
- [ ] trade_db 데이터베이스 생성
- [ ] 테이블 스키마 적용 완료
- [ ] 권한 설정 확인

### Redis
- [ ] Redis 서버 실행 중
- [ ] 연결 테스트 완료

## 3. 실행 순서

### 방법 1: Docker Compose 통합 실행
```bash
# 루트 디렉토리에서
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 방법 2: 개별 서비스 실행

#### 1단계: 인프라 서비스
```bash
# PostgreSQL
docker run -d \
  --name trade-postgres \
  -e POSTGRES_DB=trade_db \
  -e POSTGRES_USER=freeksj \
  -e POSTGRES_PASSWORD=freeksj \
  -p 5432:5432 \
  postgres:15

# Redis
docker run -d \
  --name trade-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### 2단계: 백엔드 서비스
```bash
# trade_batch (Java)
cd trade_batch
./mvnw spring-boot:run

# trade_dashboard (Python)
cd trade_dashboard
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# trade_engine (Python)
cd trade_engine
source venv/bin/activate
python main.py
```

#### 3단계: 프론트엔드
```bash
cd trade_frontend
npm run dev
```

## 4. 상태 확인

### 서비스 헬스체크
```bash
# trade_batch
curl http://localhost:8080/actuator/health

# trade_dashboard
curl http://localhost:8000/health

# trade_frontend
curl http://localhost:5173
```

### 로그 위치
- trade_batch: `logs/trade_batch.log`
- trade_dashboard: `logs/trade_dashboard.log`
- trade_engine: `logs/trade_engine.log`

## 5. 문제 해결

### IBKR 연결 실패
1. IB Gateway 실행 확인
2. API 설정에서 "Enable ActiveX and Socket Clients" 체크
3. "Trusted IP Addresses"에 127.0.0.1 추가
4. 포트 번호 확인 (Paper: 4002, Live: 4001)

### 데이터베이스 연결 실패
1. PostgreSQL 서비스 상태 확인
2. 방화벽 설정 확인
3. pg_hba.conf에서 로컬 연결 허용 확인

### 포트 충돌
- 8080: trade_batch
- 8000: trade_dashboard  
- 5173: trade_frontend
- 5432: PostgreSQL
- 6379: Redis

## 6. 모니터링

### 시스템 리소스
```bash
# Docker 컨테이너 상태
docker ps

# 리소스 사용량
docker stats
```

### 로그 모니터링
```bash
# 모든 로그 실시간 확인
tail -f logs/*.log
```

## 7. 종료 순서

### Docker Compose
```bash
docker-compose down
```

### 개별 서비스
1. trade_frontend (Ctrl+C)
2. trade_engine (Ctrl+C)
3. trade_dashboard (Ctrl+C)
4. trade_batch (Ctrl+C)
5. Redis 중지
6. PostgreSQL 중지
7. IB Gateway 종료