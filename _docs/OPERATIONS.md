# 운영 가이드

> 이 문서는 Trade System의 일상 운영, 모니터링, 문제 해결 및 워크플로우를 포함합니다.

## 1. 시스템 시작/종료

### 1.1 전체 시스템 시작
```bash
# 기본 서비스 시작 (개발)
cd trade_infra/docker/compose
docker-compose up -d

# 전체 스택 시작 (모니터링 포함)
docker-compose -f docker-compose.full.yml up -d

# 핵심 서비스만 (DB, Redis)
docker-compose -f docker-compose-core.yml up -d
```

### 1.2 시스템 종료
```bash
# 정상 종료
docker-compose down

# 볼륨 포함 삭제 (주의!)
docker-compose down -v
```

### 1.3 개별 서비스 관리
```bash
# 특정 서비스 재시작
docker-compose restart backend

# 서비스 로그 확인
docker-compose logs -f backend

# 서비스 상태 확인
docker-compose ps
```

## 2. 모니터링

### 2.1 Grafana 대시보드
1. 접속: http://localhost:3001
2. 로그인: freeksj / [REDACTED]
3. 기본 대시보드:
   - System Overview: 시스템 리소스
   - Trade Metrics: 거래 지표
   - Application Logs: 애플리케이션 로그

### 2.2 주요 메트릭
| 메트릭 | 임계치 | 설명 |
|--------|---------|------|
| CPU 사용률 | > 80% | 성능 저하 가능 |
| 메모리 사용률 | > 85% | OOM 위험 |
| 디스크 사용률 | > 90% | 디스크 공간 부족 |
| API 응답시간 | > 1s | 사용자 경험 저하 |
| 에러율 | > 1% | 서비스 안정성 문제 |

### 2.3 로그 확인
```bash
# Docker 컨테이너 로그
docker logs -f trade_backend --tail 100

# 시스템 로그 (Loki로 수집됨)
journalctl -u docker -f

# 애플리케이션 로그 파일
tail -f /var/log/trade/*.log
```

## 3. 일상 운영 작업

### 3.1 데이터베이스 관리
```bash
# DB 접속
docker exec -it trade_db psql -U freeksj -d trade_db

# 테이블 크기 확인
SELECT
    schemaname AS schema,
    tablename AS table,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# 연결 상태 확인
SELECT count(*) FROM pg_stat_activity;
```

### 3.2 캐시 관리
```bash
# Redis 접속
docker exec -it trade_redis redis-cli

# 메모리 사용량 확인
INFO memory

# 키 패턴 확인
KEYS *

# 캐시 초기화 (주의!)
FLUSHALL
```

### 3.3 IB Gateway 연결 확인
```bash
# Backend 로그에서 IB 연결 확인
docker logs trade_backend | grep "IB Gateway"

# Health check 확인
curl http://localhost:8000/health/ibkr
```

## 4. 백업 및 복구

### 4.1 자동 백업 (스크립트)
```bash
# 전체 백업 실행
./scripts/backup.sh

# 특정 서비스만 백업
./scripts/backup.sh --service postgresql
```

### 4.2 수동 백업
```bash
# PostgreSQL 백업
docker exec trade_db pg_dump -U freeksj -d trade_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Redis 백업
docker exec trade_redis redis-cli BGSAVE
docker cp trade_redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### 4.3 복구 절차
```bash
# PostgreSQL 복구
docker exec -i trade_db psql -U freeksj -d trade_db < backup.sql

# Redis 복구
docker cp redis_backup.rdb trade_redis:/data/dump.rdb
docker restart trade_redis
```

## 5. 문제 해결

### 5.1 서비스가 시작되지 않을 때
```bash
# 1. 컨테이너 상태 확인
docker-compose ps

# 2. 로그 확인
docker-compose logs [service_name]

# 3. 포트 충돌 확인
sudo lsof -i :8000  # 해당 포트 사용 프로세스 확인

# 4. 환경변수 확인
cat .env.development
```

### 5.2 데이터베이스 연결 오류
```bash
# 1. DB 컨테이너 상태 확인
docker ps | grep trade_db

# 2. DB 로그 확인
docker logs trade_db

# 3. 연결 테스트
docker exec -it trade_db psql -U freeksj -d trade_db -c "SELECT 1;"

# 4. 네트워크 확인
docker network ls
docker network inspect trade_network
```

### 5.3 메모리 부족
```bash
# 1. 컨테이너 메모리 사용량 확인
docker stats --no-stream

# 2. 시스템 메모리 확인
free -h

# 3. 컨테이너 리소스 제한 조정
# docker-compose.yml에서 deploy.resources 수정
```

## 6. 성능 최적화

### 6.1 Docker 이미지 정리
```bash
# 사용하지 않는 이미지 삭제
docker image prune -a

# 사용하지 않는 볼륨 삭제
docker volume prune

# 전체 정리
docker system prune -a --volumes
```

### 6.2 데이터베이스 최적화
```bash
# VACUUM 실행
docker exec -it trade_db psql -U freeksj -d trade_db -c "VACUUM ANALYZE;"

# 인덱스 재구축
docker exec -it trade_db psql -U freeksj -d trade_db -c "REINDEX DATABASE trade_db;"
```

## 7. 배포 워크플로우

### 7.1 개발 환경 배포
```bash
# 1. 코드 푸시
git push origin develop

# 2. PR 생성 및 머지
# GitHub에서 Pull Request 생성

# 3. 자동 CI/CD 트리거
# GitHub Actions가 자동으로 실행
```

### 7.2 운영 환경 배포
```bash
# 1. 태그 생성
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 2. 운영 서버에서 풀
git pull origin main

# 3. Docker 이미지 업데이트
docker-compose pull

# 4. 서비스 재시작
docker-compose up -d
```

## 8. 긴급 대응

### 8.1 서비스 장애 대응
1. **즉시 확인**
   - 모니터링 대시보드 확인
   - 로그 확인
   - 헬스체크 상태 확인

2. **긴급 조치**
   ```bash
   # 서비스 재시작
   docker-compose restart [service_name]
   
   # 필요시 롤백
   git checkout [previous_commit]
   docker-compose build
   docker-compose up -d
   ```

3. **문제 해결 후**
   - 원인 분석
   - 재발 방지 대책 수립
   - 문서 업데이트

### 8.2 데이터 손실 대응
1. **즉시 서비스 중단**
   ```bash
   docker-compose stop
   ```

2. **백업에서 복구**
   ```bash
   ./scripts/restore.sh [backup_file]
   ```

3. **데이터 검증**
   - 복구된 데이터 확인
   - 무결성 검사
   - 서비스 재개

## 9. 성능 모니터링 체크리스트

### 9.1 일일 체크
- [ ] Grafana 대시보드 확인
- [ ] 시스템 리소스 사용량
- [ ] API 응답 시간
- [ ] 에러 로그 확인
- [ ] IB Gateway 연결 상태

### 9.2 주간 체크
- [ ] 디스크 사용량 점검
- [ ] 데이터베이스 최적화
- [ ] 로그 파일 정리
- [ ] Docker 이미지 정리
- [ ] 백업 파일 확인

### 9.3 월간 체크
- [ ] 보안 업데이트 적용
- [ ] 성능 트렌드 분석
- [ ] 자원 사용 계획 검토
- [ ] 비상 대응 훈련

## 10. 연락처 및 에스켈레이션

### 10.1 담당자
| 역할 | 담당자 | 연락처 | 비고 |
|------|---------|---------|------|
| 시스템 관리자 | - | - | 24/7 대응 |
| 개발자 | - | - | 업무시간 |
| DBA | - | - | DB 문제 |

### 10.2 에스켈레이션 정책
1. **Level 1**: 일반 장애 - 담당자 대응
2. **Level 2**: 서비스 중단 - 팀장 보고
3. **Level 3**: 데이터 손실 - 경영진 보고

## 11. 유용한 명령어 모음

```bash
# 실시간 로그 모니터링
docker-compose logs -f --tail=100

# 컨테이너 리소스 사용량
docker stats

# 네트워크 테스트
docker exec trade_backend ping -c 3 db

# 프로세스 확인
docker exec trade_backend ps aux

# 환경변수 확인
docker exec trade_backend env | grep TRADE
```