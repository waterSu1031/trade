# Trade Dashboard Service

FastAPI 기반의 실시간 트레이딩 대시보드 백엔드 서비스입니다. WebSocket을 통한 실시간 데이터 스트리밍과 RESTful API를 제공합니다.

## 🚀 주요 기능

- **실시간 시장 데이터**: WebSocket을 통한 실시간 가격 정보 제공
- **포지션 모니터링**: 현재 보유 포지션 실시간 추적
- **거래 내역 관리**: 거래 이력 조회 및 분석
- **통계 대시보드**: 수익률, 손익 등 주요 지표 제공
- **IBKR 연동**: Interactive Brokers API 통합

## 📋 기술 스택

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- WebSocket
- Pydantic
- ib_insync

## 🛠️ 설정 및 실행

### 사전 요구사항

- Python 3.11 이상
- PostgreSQL 15 이상
- IBKR TWS/Gateway 실행 중

### 환경 설정

1. 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정 (.env 파일 생성):
```bash
IB_HOST=localhost
IB_PORT=4002
IB_CLIENT_ID_DASHBOARD=10
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trade_db
DB_USER=freeksj
DB_PASSWORD=your_password
```

### 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t trade-dashboard .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env trade-dashboard
```

## 📁 프로젝트 구조

```
app/
├── api/             # API 라우터
│   ├── dashboard.py # 대시보드 엔드포인트
│   ├── positions.py # 포지션 관리
│   ├── trades.py    # 거래 내역
│   ├── statistics.py # 통계 데이터
│   └── websocket.py # WebSocket 핸들러
├── database/        # 데이터베이스 설정
├── models/          # 데이터 모델
├── services/        # 비즈니스 로직
├── config.py        # 설정 관리
└── main.py          # 애플리케이션 진입점
```

## 🌐 API 엔드포인트

### 거래 (Trades)
- `GET /api/trades/` - 거래 내역 조회
- `GET /api/trades/{trade_id}` - 특정 거래 조회
- `POST /api/trades/` - 새 거래 생성
- `PUT /api/trades/{trade_id}` - 거래 정보 업데이트
- `GET /api/trades/live/recent` - IBKR에서 최근 거래 조회
- `GET /api/trades/summary/daily` - 일별 거래 요약

### 포지션 (Positions)
- `GET /api/positions/` - 포지션 목록 조회
- `GET /api/positions/{position_id}` - 특정 포지션 조회
- `POST /api/positions/` - 새 포지션 생성
- `PUT /api/positions/{position_id}` - 포지션 정보 업데이트
- `GET /api/positions/live/current` - IBKR에서 현재 포지션 조회
- `GET /api/positions/portfolio/summary` - 포트폴리오 요약
- `POST /api/positions/sync` - IBKR에서 포지션 동기화

### 통계 (Statistics)
- `GET /api/statistics/daily` - 일별 통계
- `GET /api/statistics/overall` - 전체 통계
- `GET /api/statistics/account` - 계좌 요약
- `GET /api/statistics/performance` - 성과 지표
- `GET /api/statistics/symbols/{symbol}` - 종목별 통계

### WebSocket
- `WS /api/ws/ws` - 실시간 데이터 스트림
- `GET /api/ws/status` - WebSocket 연결 상태

## 🔌 WebSocket 사용법

### 연결
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/ws');
```

### 구독
```javascript
// 계좌 업데이트 구독
ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'account_updates'
}));

// 포지션 업데이트 구독
ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'position_updates'
}));

// 거래 업데이트 구독
ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'trade_updates'
}));
```

### 메시지 수신
```javascript
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('받은 데이터:', data);
};
```

## 💾 데이터베이스 스키마

### Trades 테이블
- 거래 ID, 주문 ID, 종목, 액션, 수량, 가격
- 수수료, 실현손익, 상태, 거래소, 통화
- 실행 시간, 생성/수정 시간

### Positions 테이블
- 포지션 ID, 종목, 수량, 평균 비용
- 시장 가격, 시장 가치, 미실현/실현 손익
- 통화, 거래소, 활성 상태

### Trading Sessions 테이블
- 세션 날짜, 총 거래 수, 총 거래량
- 총/순 손익, 수수료, 승률
- 최대 이익/손실, 평균 이익/손실

### Accounts 테이블
- 계좌 ID, 순 청산 가치, 현금 가치
- 매수력, 증거금 정보, 통화

## 🧪 테스트

```bash
# 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app

# 특정 테스트 실행
pytest tests/test_api.py
```

## 📊 모니터링

- `/docs` - Swagger UI API 문서
- `/redoc` - ReDoc API 문서
- `/health` - 헬스체크 엔드포인트

## ⚠️ 주의사항

- IBKR 연결 시 고유한 Client ID 사용 (기본값: 10)
- WebSocket 연결 시 인증 토큰 필요
- 대량 데이터 조회 시 페이지네이션 사용 권장

## 🤝 관련 서비스

- [Trade Batch](../trade_batch/README.md) - 배치 처리 서비스
- [Trade Engine](../trade_engine/README.md) - 트레이딩 엔진
- [Trade Frontend](../trade_frontend/README.md) - 웹 인터페이스