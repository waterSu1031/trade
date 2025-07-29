# Trade Dashboard API Endpoints

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

## 인증 및 보안

현재 설정:
- CORS 허용 오리진: 
  - http://localhost:5173 (Svelte 개발)
  - http://localhost:4173 (Svelte 프리뷰)
  - http://127.0.0.1:5173
  - http://127.0.0.1:4173

## IB Gateway 연결 정보

- Host: 127.0.0.1
- Port: 4002 (Paper Trading)
- Client ID: 10 (trade_dashboard 전용)