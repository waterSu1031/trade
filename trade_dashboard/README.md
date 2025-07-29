# Trade Dashboard Backend

트레이딩 대시보드를 위한 FastAPI 백엔드 서버입니다. IBKR (Interactive Brokers) API와 연동하여 실시간 거래 데이터를 제공합니다.

## 기능

- **IBKR API 연동**: TWS/IB Gateway를 통한 실시간 거래 데이터 수집
- **거래 관리**: 거래 내역 조회, 생성, 업데이트
- **포지션 관리**: 현재 포지션 및 포트폴리오 정보
- **통계 분석**: 일별/전체 거래 통계, 성과 지표 계산
- **실시간 데이터**: WebSocket을 통한 실시간 데이터 스트리밍
- **데이터베이스**: SQLite/PostgreSQL 지원

## 설치 및 실행

### 환경 설정

1. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```

2. **환경 변수 설정**:
   ```bash
   cp .env.example .env
   # .env 파일을 편집하여 IBKR 연결 정보 입력
   ```

3. **IBKR TWS/Gateway 설정**:
   - TWS 또는 IB Gateway 실행
   - API 설정에서 소켓 포트 활성화 (기본: 7497)
   - 신뢰할 수 있는 IP 주소에 127.0.0.1 추가

### 개발 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker 실행

```bash
docker-compose up --build
```

## API 엔드포인트

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

## WebSocket 사용법

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

## 데이터베이스 스키마

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

## 환경 변수

```env
# IBKR 설정
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1

# 데이터베이스 설정
DATABASE_URL=sqlite:///./trading.db

# API 설정
API_HOST=0.0.0.0
API_PORT=8000

# 환경
ENVIRONMENT=development
DEBUG=true
```

## 개발 노트

- Svelte 프론트엔드와 연동하여 완전한 트레이딩 대시보드 구성
- IBKR Paper Trading 계정으로 테스트 권장
- 실시간 데이터는 5초마다 업데이트
- 모든 API는 OpenAPI/Swagger 문서 자동 생성 (http://localhost:8000/docs)

## 주의사항

- IBKR API 사용 시 적절한 권한과 설정 필요
- Paper Trading 계정으로 먼저 테스트
- 실제 거래 시 위험 관리 필수