# Docker Volume 관리 가이드

## 개요

Trade System은 Docker Named Volumes를 사용하여 데이터를 관리합니다. 이는 권한 문제를 해결하고 OS 독립적인 데이터 관리를 가능하게 합니다.

## Named Volumes 구조

```yaml
volumes:
  postgres-data:    # PostgreSQL 데이터베이스 파일
  redis-data:       # Redis 캐시 데이터
```

## 주요 명령어

### 1. 볼륨 확인

```bash
# 모든 볼륨 목록
docker volume ls

# 특정 볼륨 상세 정보
docker volume inspect postgres-data
docker volume inspect redis-data
```

### 2. 볼륨 생성/삭제

```bash
# 볼륨 생성 (docker-compose up 시 자동 생성됨)
docker volume create postgres-data
docker volume create redis-data

# 볼륨 삭제 (주의: 모든 데이터가 삭제됨!)
docker volume rm postgres-data
docker volume rm redis-data
```

### 3. 데이터 백업

```bash
# 백업 스크립트 실행
cd _platform/infra
./scripts/backup.sh

# 수동 PostgreSQL 백업
docker exec trade_db pg_dump -U freeksj trade_db > backup.sql

# 수동 Redis 백업
docker exec trade_redis redis-cli BGSAVE
docker cp trade_redis:/data/dump.rdb ./redis_backup.rdb
```

### 4. 데이터 복원

```bash
# 복원 스크립트 실행
cd _platform/infra
./scripts/restore.sh backup_20240101.sql.gz

# 수동 PostgreSQL 복원
docker exec -i trade_db psql -U freeksj trade_db < backup.sql

# 수동 Redis 복원
docker cp redis_backup.rdb trade_redis:/data/dump.rdb
docker restart trade_redis
```

## 개발 환경 설정

### 초기 설정

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-repo/trade.git
cd trade

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 3. 시스템 시작
docker-compose up -d

# 4. 데이터베이스 초기화 (필요시)
docker exec -i trade_db psql -U freeksj < _platform/infra/configs/sql/deployment/schema.sql
```

### 기존 데이터 마이그레이션

기존 bind mount 방식에서 named volumes로 전환하는 경우:

```bash
# 1. 기존 시스템 중지
docker-compose down

# 2. 기존 데이터 백업
./scripts/backup.sh

# 3. Named volumes로 전환된 시스템 시작
docker-compose up -d

# 4. 백업 데이터 복원
./scripts/restore.sh [백업파일명]
```

## 문제 해결

### 권한 문제

Named volumes를 사용하면 Docker가 자동으로 권한을 관리하므로 권한 문제가 발생하지 않습니다.

### 볼륨 위치 찾기

```bash
# Linux/Mac
docker volume inspect postgres-data | grep Mountpoint
# 일반적으로: /var/lib/docker/volumes/postgres-data/_data

# Windows
docker volume inspect postgres-data
# 일반적으로: \\wsl$\docker-desktop-data\...\volumes\postgres-data\_data
```

### 용량 확인

```bash
# 볼륨 사용량 확인
docker system df -v

# PostgreSQL 데이터베이스 크기 확인
docker exec trade_db psql -U freeksj -c "SELECT pg_database_size('trade_db');"
```

## 프로덕션 권장사항

1. **정기 백업**: 크론잡으로 일일 백업 설정
2. **백업 검증**: 정기적으로 복원 테스트 수행
3. **모니터링**: 볼륨 용량 모니터링 설정
4. **외부 백업**: 백업 파일을 외부 스토리지(S3 등)에 복사

## 주의사항

- `docker volume rm` 명령은 모든 데이터를 영구 삭제합니다
- 볼륨 이름 변경 시 데이터 마이그레이션 필요
- Docker 재설치 시 볼륨 데이터가 삭제될 수 있음