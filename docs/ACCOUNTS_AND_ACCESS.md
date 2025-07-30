# 계정 및 접속 정보

> 이 문서는 Trade System의 모든 계정 및 인증 정보를 포함합니다.

## 1. 내부 서비스 계정

### 1.1 데이터베이스
| 서비스 | 호스트 | 포트 | 사용자 | 비밀번호 | 데이터베이스 | 접속 명령 |
|--------|--------|------|---------|----------|-------------|-----------|
| PostgreSQL | localhost | 5432 | freeksj | [REDACTED] | trade_db | `psql -h localhost -p 5432 -U freeksj -d trade_db` |
| Redis | localhost | 6379 | - | - | - | `redis-cli -h localhost -p 6379` |

**Docker 컨테이너 접속:**
```bash
# PostgreSQL
docker exec -it trade_db psql -U freeksj -d trade_db

# Redis
docker exec -it trade_redis redis-cli
```

### 1.2 모니터링 서비스
| 서비스 | URL | 사용자 | 비밀번호 | 용도 |
|--------|-----|---------|----------|------|
| Grafana | http://localhost:3001 | freeksj | [REDACTED] | 메트릭/로그 시각화 |
| Prometheus | http://localhost:9090 | - | - | 메트릭 수집 |
| Loki | http://localhost:3100 | - | - | 로그 저장 (Grafana로 접근) |
| Portainer | http://localhost:9000 | freeksj | [REDACTED] | Docker 관리 UI |

## 2. 외부 서비스 계정

### 2.1 Interactive Brokers (IB Gateway)
| 항목 | 값 | 설명 |
|------|-----|------|
| Username | freeksj1031 | IB 로그인 ID |
| Password | [REDACTED] | IB 로그인 비밀번호 |
| Paper Trading Host | localhost | 모의 거래 호스트 |
| Paper Trading Port | 4002 | 모의 거래 포트 |
| Live Trading Host | localhost | 실거래 호스트 |
| Live Trading Port | 4001 | 실거래 포트 |

**Client ID 할당:**
- trade_dashboard: 10
- trade_engine: 20
- trade_batch: 30

### 2.2 개발 도구 및 CI/CD
| 서비스 | URL | 사용자 | 토큰/비밀번호 위치 | 용도 |
|--------|-----|---------|-------------------|------|
| GitHub | github.com | freeksj | Personal Access Token | 소스 코드 저장소 |
| Docker Hub | hub.docker.com | [미설정] | GitHub Secrets: DOCKERHUB_TOKEN | 컨테이너 이미지 저장소 |

### 2.3 클라우드/VPS (예정)
| 서비스 | URL | 사용자 | 비고 |
|--------|-----|---------|------|
| Vultr | my.vultr.com | - | API Key 필요 |
| DigitalOcean | cloud.digitalocean.com | - | 토큰 필요 |
| AWS | aws.amazon.com | - | Access Key/Secret 필요 |

## 3. 환경변수 및 설정 파일

### 3.1 환경변수 파일 위치
- 개발: `.env.development`
- 운영: `.env.production`
- 템플릿: `.env.example`

### 3.2 주요 환경변수
```bash
# Database
DB_USER=freeksj
DB_PASSWORD=[REDACTED]
DB_NAME=trade_db

# Interactive Brokers
IB_HOST=localhost
IB_PORT=4002  # 4001 for live
IB_CLIENT_ID_DASHBOARD=10
IB_CLIENT_ID_ENGINE=20
IB_CLIENT_ID_BATCH=30
IB_USERNAME=freeksj1031
IB_PASSWORD=[REDACTED]

# Monitoring
GRAFANA_USER=freeksj
GRAFANA_PASSWORD=[REDACTED]
```

## 4. API 키 및 토큰 관리

### 4.1 GitHub Secrets (CI/CD)
| Secret 이름 | 용도 | 설정 방법 |
|------------|------|-----------|
| DOCKERHUB_USERNAME | Docker Hub 사용자명 | Repository Settings > Secrets |
| DOCKERHUB_TOKEN | Docker Hub Access Token | Docker Hub에서 생성 |
| VPS_HOST | 배포 서버 IP | VPS 생성 후 설정 |
| VPS_SSH_KEY | SSH 개인키 | ssh-keygen으로 생성 |

### 4.2 로컬 시크릿 관리
- `.env` 파일들은 `.gitignore`에 포함
- 실제 비밀번호는 절대 커밋하지 않음
- 팀원 간 공유는 안전한 채널로

## 5. 접속 체크리스트

### 5.1 초기 설정 시
- [ ] PostgreSQL 접속 확인
- [ ] Redis 접속 확인
- [ ] IB Gateway 연결 확인
- [ ] Grafana 로그인 확인

### 5.2 문제 발생 시
- [ ] 환경변수 파일 존재 확인
- [ ] Docker 컨테이너 실행 상태 확인
- [ ] 포트 충돌 확인
- [ ] 방화벽 설정 확인