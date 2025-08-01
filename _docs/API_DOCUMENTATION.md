# Trade System API Documentation

전체 Trade System의 API 문서입니다. 각 마이크로서비스별 API 엔드포인트를 정리합니다.

## 서비스별 기본 URL

- Trade Dashboard (FastAPI): `http://localhost:8000`
- Trade Batch (Spring Boot): `http://localhost:8080`
- Trade Frontend (SvelteKit): `http://localhost:3000`

---

# Trade Dashboard API

Base URL: `http://localhost:8000`

## 기본 엔드포인트

- `GET /` - API 루트
- `GET /health` - 헬스 체크
- `GET /docs` - Swagger UI API 문서 (자동 생성)
- `GET /redoc` - ReDoc API 문서 (자동 생성)

## 1. 대시보드 (`/api/dashboard`)

- `GET /api/dashboard/summary` - 대시보드 요약 정보
- `GET /api/dashboard/performance` - 성과 메트릭
- `GET /api/dashboard/top-performers` - 상위 수익 종목
- `GET /api/dashboard/market-overview` - 시장 개요
- `GET /api/dashboard/alerts` - 알림 목록
- `PUT /api/dashboard/alerts/{alert_id}/read` - 알림 읽음 처리
- `GET /api/dashboard/activity-feed` - 활동 피드
- `GET /api/dashboard/risk-metrics` - 리스크 메트릭

## 2. 포지션 (`/api/positions`)

- `GET /api/positions/` - 포지션 목록 조회
- `GET /api/positions/{position_id}` - 특정 포지션 조회
- `POST /api/positions/` - 포지션 생성
- `PUT /api/positions/{position_id}` - 포지션 수정
- `GET /api/positions/live/current` - 실시간 현재 포지션
- `GET /api/positions/portfolio/summary` - 포트폴리오 요약
- `POST /api/positions/sync` - IB Gateway와 포지션 동기화

## 3. 거래 (`/api/trades`)

- `GET /api/trades/` - 거래 목록 조회
- `GET /api/trades/{trade_id}` - 특정 거래 조회
- `POST /api/trades/` - 거래 생성
- `PUT /api/trades/{trade_id}` - 거래 수정
- `GET /api/trades/live/recent` - 최근 실시간 거래
- `GET /api/trades/summary/daily` - 일별 거래 요약

## 4. 통계 (`/api/statistics`)

- `GET /api/statistics/daily` - 일별 통계
- `GET /api/statistics/overall` - 전체 통계
- `GET /api/statistics/account` - 계정 요약
- `GET /api/statistics/performance` - 성과 메트릭
- `GET /api/statistics/symbols/{symbol}` - 종목별 통계

## 5. 실시간 데이터 (`/api/realtime`)

- `GET /api/realtime/prices` - 전체 실시간 가격
- `GET /api/realtime/prices/{symbol}` - 특정 종목 실시간 가격
- `GET /api/realtime/positions` - 실시간 포지션
- `POST /api/realtime/positions` - 실시간 포지션 추가
- `PUT /api/realtime/positions/{symbol}` - 실시간 포지션 수정
- `DELETE /api/realtime/positions/{symbol}` - 실시간 포지션 제거
- `GET /api/realtime/alerts` - 실시간 알림
- `POST /api/realtime/alerts` - 알림 생성
- `GET /api/realtime/status` - 실시간 서비스 상태

## 6. 전략 (`/api/strategy`)

- `GET /api/strategy/` - 전략 목록
- `GET /api/strategy/{strategy_name}` - 특정 전략 정보
- `GET /api/strategy/{strategy_name}/performance` - 전략 성과
- `POST /api/strategy/{strategy_name}/activate` - 전략 활성화
- `POST /api/strategy/{strategy_name}/deactivate` - 전략 비활성화
- `PUT /api/strategy/{strategy_name}/parameters` - 전략 파라미터 수정
- `GET /api/strategy/{strategy_name}/signals` - 전략 시그널

## 7. 트레이딩 (`/api/trading`)

- `GET /api/trading/status` - 트레이딩 시스템 상태
- `POST /api/trading/start` - 트레이딩 시작
- `POST /api/trading/stop` - 트레이딩 중지
- `POST /api/trading/pause` - 트레이딩 일시정지
- `POST /api/trading/resume` - 트레이딩 재개
- `GET /api/trading/account` - 계정 정보
- `POST /api/trading/orders` - 주문 생성
- `GET /api/trading/orders` - 주문 목록
- `DELETE /api/trading/orders/{order_id}` - 주문 취소
- `POST /api/trading/orders/cancel-all` - 모든 주문 취소
- `POST /api/trading/positions/close-all` - 모든 포지션 청산
- `GET /api/trading/pnl/daily` - 일별 손익

## 8. 웹소켓 (`/api/ws`)

- `WebSocket /api/ws/ws` - 실시간 데이터 스트리밍
- `GET /api/ws/status` - 웹소켓 상태

---

# Trade Batch API

Base URL: `http://localhost:8080`

## 기본 엔드포인트

- `GET /actuator/health` - 서비스 상태 확인
- `GET /actuator/info` - 서비스 정보

## 배치 작업 제어

- `POST /batch/run/{jobName}` - 배치 작업 수동 실행
  - 지원 작업: CollectDataJob, DailyStatisticsJob, DataIntegrityJob, DataSyncJob, PartitionManagementJob
- `GET /batch/status/{jobName}` - 작업 상태 조회
- `GET /batch/history/{jobName}` - 작업 실행 이력

## 데이터 수집

- `POST /batch/collect/historical` - 과거 데이터 수집
- `POST /batch/collect/realtime/start` - 실시간 데이터 수집 시작
- `POST /batch/collect/realtime/stop` - 실시간 데이터 수집 중지

---

# 인증 및 보안

## CORS 설정

허용된 오리진:
- http://localhost:5173 (Svelte 개발)
- http://localhost:4173 (Svelte 프리뷰)
- http://localhost:3000 (프로덕션)
- http://127.0.0.1:5173
- http://127.0.0.1:4173
- http://127.0.0.1:3000

## IBKR 연결 정보

각 서비스별 IBKR Client ID:
- Trade Dashboard: 10
- Trade Engine: 20
- Trade Batch: 30

Paper Trading 포트: 4002
Live Trading 포트: 4001

---

# WebSocket 메시지 포맷

## 구독 메시지

```json
{
  "type": "subscribe",
  "topic": "account_updates" | "position_updates" | "trade_updates" | "price_updates",
  "symbols": ["AAPL", "GOOGL"] // price_updates의 경우
}
```

## 구독 취소

```json
{
  "type": "unsubscribe",
  "topic": "account_updates" | "position_updates" | "trade_updates" | "price_updates",
  "symbols": ["AAPL"] // price_updates의 경우
}
```

## 서버 응답 메시지

### 계정 업데이트
```json
{
  "type": "account_update",
  "data": {
    "net_liquidation": 100000.00,
    "cash_balance": 50000.00,
    "buying_power": 200000.00,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### 포지션 업데이트
```json
{
  "type": "position_update",
  "data": {
    "symbol": "AAPL",
    "quantity": 100,
    "avg_cost": 150.00,
    "market_price": 155.00,
    "unrealized_pnl": 500.00,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### 거래 업데이트
```json
{
  "type": "trade_update",
  "data": {
    "trade_id": "12345",
    "symbol": "AAPL",
    "action": "BUY",
    "quantity": 100,
    "price": 150.00,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### 가격 업데이트
```json
{
  "type": "price_update",
  "data": {
    "symbol": "AAPL",
    "bid": 154.98,
    "ask": 155.02,
    "last": 155.00,
    "volume": 1000000,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```