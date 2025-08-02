# Trade Batch (Python)

Python 기반 배치 처리 서비스입니다. 기존 Java 버전을 Python으로 재구현했습니다.

## 주요 기능

- **계약 초기화**: IBKR에서 계약 상세 정보 수집
- **선물 월물 관리**: 선물 계약의 월물 정보 자동 업데이트
- **시계열 데이터 수집**: 시장 데이터 수집 및 저장
- **거래시간 관리**: 거래소별 거래시간 자동 업데이트
- **데이터 정리**: 오래된 데이터 자동 삭제

## 기술 스택

- **Python 3.11**
- **FastAPI**: REST API 서버
- **APScheduler**: 배치 작업 스케줄링
- **asyncpg**: PostgreSQL 비동기 드라이버
- **ib_insync**: IBKR API 클라이언트
- **Redis**: 캐싱

## 프로젝트 구조

```
trade_batch/
├── src/
│   ├── main.py              # FastAPI 애플리케이션
│   ├── config.py            # 설정 관리
│   ├── scheduler.py         # 스케줄러 설정
│   ├── jobs/                # 배치 작업들
│   │   ├── contract_init.py
│   │   ├── future_month.py
│   │   ├── market_data.py
│   │   ├── trading_hours.py
│   │   └── cleanup.py
│   ├── utils/               # 유틸리티 (추후 trade_common으로 이동)
│   │   ├── db.py
│   │   ├── ibkr.py
│   │   ├── redis.py
│   │   └── converters.py
│   └── api/                 # REST API
│       └── batch_controller.py
└── tests/
```

## 설치 및 실행

### 개발 환경

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 실행
uvicorn src.main:app --reload --port 8082
```

### Docker

```bash
# 빌드
docker build -t trade_batch .

# 실행
docker run -p 8082:8082 --env-file .env trade_batch
```

## API 엔드포인트

- `GET /api/batch/scheduled-jobs` - 스케줄된 작업 목록
- `POST /api/batch/jobs/{job_name}/run` - 수동 작업 실행
- `GET /api/batch/jobs/{job_name}/status` - 작업 상태 조회
- `GET /api/batch/health` - 헬스 체크

## 스케줄된 작업

| 작업명 | 설명 | 스케줄 |
|--------|------|--------|
| init_contract_data | 계약 구조 초기화 | 매일 07:00 |
| add_future_months | 선물 월물 추가 | 매일 07:30 |
| collect_time_data | 시계열 데이터 수집 | 매일 18:00 |
| cleanup_old_data | 오래된 데이터 정리 | 매일 06:30 |
| update_trading_hours | 거래시간 업데이트 | 매주 일요일 05:00 |

## 환경 변수

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/trade

# Redis  
REDIS_URL=redis://localhost:6379

# IBKR
IBKR_HOST=localhost
IBKR_PORT=4002
IBKR_CLIENT_ID=2

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

## 테스트

```bash
# 단위 테스트
pytest

# 커버리지
pytest --cov=src
```

## 마이그레이션 가이드

Java에서 Python으로 마이그레이션하면서 다음 사항들이 변경되었습니다:

1. **데이터 처리**: 모든 데이터는 Dict 형태로 처리 (VO/DTO 미사용)
2. **비동기 처리**: 모든 I/O 작업은 async/await 사용
3. **스케줄링**: Spring Batch → APScheduler
4. **API**: Spring Boot → FastAPI

## 향후 계획

- `utils` 디렉토리의 공통 기능을 `trade_common` 라이브러리로 이동
- 더 많은 배치 작업 추가
- 모니터링 및 알림 기능 추가