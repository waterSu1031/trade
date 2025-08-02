# SQL Schema Management

이 디렉토리는 Trade System의 데이터베이스 스키마를 관리합니다.

## SQL 파일 사용 방법

**이 SQL 파일들은 수동으로 실행해야 합니다.** 시스템이 자동으로 실행하지 않습니다.

### 실행 방법
```bash
# PostgreSQL에 접속
psql -U freeksj -h localhost -p 5432

# SQL 파일 실행
\i /path/to/sql/file.sql

# 또는 커맨드라인에서 직접 실행
psql -U freeksj -h localhost -p 5432 -f deployment/schema.sql
```

## 디렉토리 구조

### `/deployment` - 배포 시 사용
- **schema.sql**: 전체 데이터베이스 스키마 (신규 설치용)
- **unified_schema.sql**: 통합 스키마 정의
- **create_tables_ibkr.sql**: IBKR 관련 테이블 (contracts, trade_events 등)
- **create_dashboard_tables.sql**: Dashboard 서비스용 테이블
- **create_trades_table.sql**: trades 테이블 생성 (Dashboard용)
- **create_missing_tables.sql**: 누락된 테이블 추가

### `/maintenance` - 운영 중 유지보수
- **drop_all_tables.sql**: 모든 테이블 삭제 (주의! 개발환경에서만 사용)
- **cleanup_old_tables.sql**: 오래된 데이터 정리

### `/legacy` - 더 이상 사용하지 않음
- 이전 버전의 SQL 파일들 (참고용으로만 보관)

### `/development` - 개발용
- 개발 중 필요한 테스트 데이터나 임시 스크립트

## 각 서비스별 테이블 사용

### Spring Batch (trade_batch)
- Spring Batch 프레임워크가 자동으로 생성 (`initialize-schema: always`)
- BATCH_JOB_INSTANCE, BATCH_JOB_EXECUTION 등의 테이블 자동 생성

### Dashboard (trade_dashboard)
- 수동 실행 필요: `deployment/create_trades_table.sql`
- 사용 테이블: trades, positions, trading_sessions, accounts

### Trade Engine (trade_engine)
- PostgreSQL 연결만 필요 (기존 테이블 사용)
- 주로 trade_events, contracts 테이블 사용

## 배포 시나리오

### 1. 신규 설치
```bash
# 데이터베이스 생성
createdb -U postgres trade_db

# 전체 스키마 생성
psql -U freeksj -d trade_db -f deployment/schema.sql

# Dashboard용 trades 테이블 생성
psql -U freeksj -d trade_db -f deployment/create_trades_table.sql
```

### 2. 기존 시스템 업그레이드
```bash
# 누락된 테이블만 추가
psql -U freeksj -d trade_db -f deployment/create_missing_tables.sql

# trades 테이블이 없다면
psql -U freeksj -d trade_db -f deployment/create_trades_table.sql
```

### 3. 개발 환경 초기화
```bash
# 주의: 모든 데이터가 삭제됩니다!
psql -U freeksj -d trade_db -f maintenance/drop_all_tables.sql
psql -U freeksj -d trade_db -f deployment/schema.sql
```

## 주의사항

1. **production 환경에서는 drop_all_tables.sql 사용 금지**
2. 배포 전 반드시 백업 수행
3. trades 테이블 생성 시 기존 VIEW가 있다면 자동으로 삭제됨
4. Spring Batch 테이블은 수동으로 생성하지 말 것 (자동 생성됨)