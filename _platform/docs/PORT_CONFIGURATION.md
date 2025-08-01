# Trade System 포트 설정 가이드

전체 Trade System에서 사용하는 포트 정보를 중앙에서 관리합니다.

## 서비스별 기본 포트

### 애플리케이션 서비스
| 서비스 | 포트 | 설명 |
|--------|------|------|
| Trade Dashboard (FastAPI) | 8000 | API 백엔드 서버 |
| Trade Batch (Spring Boot) | 8080 | 배치 처리 서비스 |
| Trade Frontend (SvelteKit) | 5173 (dev) / 3000 (prod) | 웹 UI |
| Trade Engine | - | 백그라운드 서비스 (포트 없음) |

### 데이터베이스 및 캐시
| 서비스 | 포트 | 설명 |
|--------|------|------|
| PostgreSQL | 5432 (prod) / 5433 (dev) | 메인 데이터베이스 |
| Redis | 6379 (prod) / 6380 (dev) | 캐시 및 세션 저장소 |

### IBKR 연결
| 용도 | 포트 | 설명 |
|------|------|------|
| Paper Trading | 4002 | 모의 거래용 |
| Live Trading | 4001 | 실거래용 |

### 모니터링 및 관리
| 서비스 | 포트 | 설명 |
|--------|------|------|
| Prometheus | 9090 | 메트릭 수집 |
| Grafana | 3001 | 메트릭 시각화 |
| Portainer | 9000 | Docker 관리 UI |
| Nginx | 80 / 443 | 리버스 프록시 |

## 환경변수 설정

### 공통 환경변수 (.env)
```bash
# 애플리케이션 포트
BACKEND_PORT=8000
BATCH_PORT=8080
FRONTEND_PORT=3000
FRONTEND_DEV_PORT=5173

# 데이터베이스 포트
DB_PORT=5432
DB_PORT_DEV=5433
REDIS_PORT=6379
REDIS_PORT_DEV=6380

# IBKR 포트
IB_PORT_PAPER=4002
IB_PORT_LIVE=4001

# 모니터링 포트
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
PORTAINER_PORT=9000
```

## Docker Compose 설정

### 프로덕션 환경 (docker-compose.yml)
```yaml
services:
  db:
    ports:
      - "${DB_PORT:-5432}:5432"
  
  redis:
    ports:
      - "${REDIS_PORT:-6379}:6379"
  
  backend:
    ports:
      - "${BACKEND_PORT:-8000}:8000"
  
  frontend:
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
```

### 개발 환경 (docker-compose.dev.yml)
```yaml
services:
  db:
    ports:
      - "${DB_PORT_DEV:-5433}:5432"
  
  redis:
    ports:
      - "${REDIS_PORT_DEV:-6380}:6379"
  
  backend:
    ports:
      - "${BACKEND_PORT:-8000}:8000"
  
  frontend:
    ports:
      - "${FRONTEND_DEV_PORT:-5173}:5173"
```

## 포트 충돌 해결

### 포트 사용 확인
```bash
# Linux/Mac
lsof -i :포트번호

# Windows
netstat -ano | findstr :포트번호
```

### 포트 변경 시 체크리스트
1. `.env` 파일에서 해당 포트 변경
2. Docker Compose 파일 확인
3. 애플리케이션 설정 파일 확인
4. Nginx 설정 업데이트 (필요시)
5. 방화벽 규칙 업데이트

## 보안 고려사항

### 외부 노출 포트
- 80 (HTTP) - Nginx
- 443 (HTTPS) - Nginx
- 기타 포트는 localhost만 접근 가능하도록 설정

### 내부 통신용 포트
- Docker 네트워크 내부에서만 접근 가능
- 호스트 머신에 바인딩하지 않음

## 클라이언트 ID 관리

각 서비스별 IBKR Client ID:
- Trade Dashboard: 10
- Trade Engine: 20  
- Trade Batch: 30

## 문제 해결

### 포트가 이미 사용 중일 때
1. 사용 중인 프로세스 확인
2. 프로세스 종료 또는 다른 포트 사용
3. `.env` 파일에서 포트 변경

### Docker 컨테이너 포트 매핑 확인
```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
```