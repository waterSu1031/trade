# Trade Common

공통 유틸리티 라이브러리로 모든 Python 기반 마이크로서비스에서 사용됩니다.

## 주요 기능

- **Database**: PostgreSQL 비동기 연결 및 Dict 기반 쿼리
- **IBKR**: Interactive Brokers 게이트웨이 연결 관리
- **Cache**: Redis 연결 및 캐싱 유틸리티
- **Config**: 환경 설정 관리

## 설치

### 개발 환경

```bash
# 로컬 개발 시 편집 가능 모드로 설치
pip install -e ../trade-common

# 또는 개발 의존성과 함께 설치
pip install -e "../trade-common[dev]"
```

### 프로덕션

```bash
# Git에서 직접 설치
pip install git+https://github.com/waterSu1031/trade.git#subdirectory=trade-common

# 또는 특정 버전 설치
pip install git+https://github.com/waterSu1031/trade.git@v0.1.0#subdirectory=trade-common
```

## 사용 예시

### Database 연결

```python
from trade_common.db import DatabaseManager

# 초기화
db = DatabaseManager("postgresql://user:pass@localhost/trade")

# 연결
await db.connect()

# Dict 기반 쿼리
rows = await db.fetch_all("SELECT * FROM contracts WHERE symbol = $1", "AAPL")
for row in rows:
    print(row)  # Dict 형태로 반환

# 연결 해제
await db.disconnect()
```

### IBKR 연결

```python
from trade_common.ibkr import IBKRManager

# 초기화
ibkr = IBKRManager()

# 연결
await ibkr.connect("localhost", 4002, client_id=1)

# 계약 정보 조회 (Dict 반환)
details = await ibkr.get_contract_details("AAPL", "SMART", "STK")

# 연결 해제
await ibkr.disconnect()
```

### Redis 캐싱

```python
from trade_common.cache import RedisManager

# 초기화
redis = RedisManager("redis://localhost:6379")

# 연결
await redis.connect()

# 캐싱
await redis.set("key", {"data": "value"})
data = await redis.get("key")

# 연결 해제
await redis.disconnect()
```

## 개발

### 테스트 실행

```bash
pytest
pytest --cov=trade_common
```

### 코드 포맷팅

```bash
black trade_common tests
flake8 trade_common tests
mypy trade_common
```

## 버전 관리

Semantic Versioning을 따릅니다:
- MAJOR: 호환되지 않는 API 변경
- MINOR: 하위 호환 기능 추가
- PATCH: 하위 호환 버그 수정

## 라이선스

MIT License