# Docker Compose 사용 안내

## Docker Compose 위치
프로젝트의 모든 Docker 관련 설정은 trade_infra에서 중앙 관리됩니다:
- 위치: `/home/freeksj/Workspace_Rule/trade/trade_infra/docker/compose/docker-compose.yml`

## 실행 방법
```bash
# trade_infra/docker/compose 디렉토리로 이동
cd /home/freeksj/Workspace_Rule/trade/trade_infra/docker/compose

# 모든 서비스 시작
docker-compose up -d

# 특정 서비스만 시작 (예: DB와 Redis만)
docker-compose up -d db redis

# 백엔드만 시작
docker-compose up -d backend

# 로그 확인
docker-compose logs -f backend
```

## 주요 서비스
- **db**: PostgreSQL with TimescaleDB (포트: 5432)
- **redis**: Redis Cache (포트: 6379)
- **backend**: Trade Dashboard API (포트: 8000)
- **frontend**: Trade Frontend (포트: 3000)
- **nginx**: Reverse Proxy (포트: 80, 443)
- **portainer**: Docker 관리 UI (포트: 9000)

## 환경 변수
trade_infra의 docker-compose.yml은 환경 변수를 사용합니다:
- `DB_USER`: freeksj (기본값)
- `DB_PASSWORD`: Lsld1501! (기본값)
- `IB_HOST`: host.docker.internal (Docker 내부에서 호스트 접근)
- `IB_PORT`: 4002 (개발) / 4001 (운영)
- `IB_CLIENT_ID_DASHBOARD`: 10

## 개발 시 주의사항
1. Docker 컨테이너 내부에서 호스트의 IB Gateway에 접근할 때는 `host.docker.internal` 사용
2. 로컬 개발 시에는 `localhost` 또는 `127.0.0.1` 사용