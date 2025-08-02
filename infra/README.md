# Trade System Platform

이 디렉토리는 Trade System의 인프라 및 문서 관련 리소스를 포함합니다.

## 디렉토리 구조

```
_platform/
├── infra/          # 인프라스트럭처 및 운영
│   ├── docker/     # Docker 관련 설정
│   ├── configs/    # 시스템 설정 파일
│   ├── scripts/    # 운영 스크립트
│   └── docker-compose.base.yml
│
└── docs/           # 프로젝트 문서
    ├── API_DOCUMENTATION.md
    ├── INFRASTRUCTURE.md
    ├── OPERATIONS.md
    └── ...
```

## 주요 구성 요소

### 1. Infrastructure (infra/)
- **Docker 설정**: PostgreSQL, Redis, Nginx 컨테이너 구성
- **설정 파일**: 데이터베이스, 캐시, ML 모델 서빙 설정
- **운영 스크립트**: 백업/복원, 배포, 초기화 스크립트
- **SQL 스키마**: 데이터베이스 테이블 정의 및 마이그레이션

### 2. Documentation (docs/)
- **INFRASTRUCTURE.md**: 시스템 아키텍처 및 인프라 구성
- **API_DOCUMENTATION.md**: API 엔드포인트 및 사용법
- **OPERATIONS.md**: 운영 및 모니터링 가이드
- **DATABASE_FOREIGN_KEYS.md**: 데이터베이스 관계 정의
- **PORT_CONFIGURATION.md**: 서비스별 포트 설정

## 사용 방법

### 인프라 관리
```bash
# PostgreSQL과 Redis 시작
docker-compose -f docker-compose.yml up -d db redis

# 데이터베이스 초기화
docker exec -i trade_db psql -U freeksj -d trade_db < _platform/infra/configs/sql/deployment/schema.sql

# trades 테이블 생성 (Dashboard용)
docker exec -i trade_db psql -U freeksj -d trade_db < _platform/infra/configs/sql/deployment/create_trades_table.sql

# 백업 실행
cd _platform/infra
./scripts/backup.sh

# 복원 실행
./scripts/restore.sh backup_20240101.sql.gz
```

### SQL 파일 구조
- **deployment/**: 배포 시 필요한 스키마 파일
- **maintenance/**: 운영 중 유지보수 스크립트
- **development/**: 개발용 샘플 데이터

### Docker 구성
- **docker-compose.base.yml**: 인프라 서비스 정의
- **docker/proxy/**: Nginx 리버스 프록시 설정
- **docker/monitoring/**: 모니터링 도구 설정 (Grafana, Prometheus)

## 관리 지침

1. **인프라 변경**: docker-compose.base.yml 수정 시 모든 서비스 재시작 필요
2. **설정 변경**: configs/ 하위 파일 변경 시 해당 서비스만 재시작
3. **SQL 실행**: 모든 SQL 파일은 수동 실행 필요 (자동 실행 안됨)
4. **문서 업데이트**: 시스템 변경 시 관련 문서 즉시 업데이트

## 주의사항

- Named volumes 사용으로 데이터는 Docker가 관리
- 백업은 정기적으로 수행하고 외부 저장소에 보관
- SQL 파일 실행 전 반드시 백업 수행
- production 환경에서는 drop_all_tables.sql 사용 금지