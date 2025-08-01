# Trade Frontend Service

SvelteKit 기반의 실시간 트레이딩 대시보드 웹 인터페이스입니다.

## 🚀 주요 기능

- **실시간 대시보드**: 포지션, 손익, 시장 데이터 실시간 모니터링
- **거래 분석**: 거래 내역 조회 및 성과 분석 차트
- **전략 관리**: 트레이딩 전략 설정 및 백테스팅
- **배치 작업 제어**: 데이터 수집 작업 스케줄링 및 모니터링
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원

## 📋 기술 스택

- SvelteKit
- TypeScript
- Tailwind CSS
- Socket.io-client (WebSocket)
- Chart.js (차트 시각화)
- Vite (빌드 도구)

## 🛠️ 설정 및 실행

### 사전 요구사항

- Node.js 18 이상
- npm 또는 yarn

### 환경 설정

1. 의존성 설치:
```bash
npm install
```

2. 환경 변수 설정 (.env 파일 생성):
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 실행

```bash
# 개발 모드 (핫 리로드)
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t trade-frontend .

# 컨테이너 실행
docker run -p 3000:3000 trade-frontend
```

## 📁 프로젝트 구조

```
src/
├── lib/
│   ├── api/         # API 클라이언트
│   │   ├── client.ts      # HTTP 클라이언트
│   │   ├── positions.ts   # 포지션 API
│   │   ├── trades.ts      # 거래 API
│   │   └── statistics.ts  # 통계 API
│   ├── components/  # 재사용 컴포넌트
│   │   ├── IBKRCard.svelte      # 카드 컴포넌트
│   │   ├── IBKRTable.svelte     # 테이블 컴포넌트
│   │   └── PositionMonitor.svelte # 포지션 모니터
│   ├── stores/      # Svelte 스토어
│   │   └── realtime.ts    # 실시간 데이터 스토어
│   └── types/       # TypeScript 타입 정의
├── routes/          # 페이지 라우트
│   ├── +page.svelte       # 홈/대시보드
│   ├── trading/           # 거래 페이지
│   ├── statistics/        # 통계 페이지
│   ├── strategy/          # 전략 페이지
│   └── batch/            # 배치 작업 페이지
└── app.html         # HTML 템플릿
```

## 🎨 주요 컴포넌트

### IBKRCard
- 정보 표시용 카드 컴포넌트
- 타이틀, 값, 변화율 표시

### IBKRTable
- 데이터 테이블 컴포넌트
- 정렬, 필터링 기능 포함

### PositionMonitor
- 실시간 포지션 모니터링
- WebSocket 연결 자동 관리

### PriceTicker
- 실시간 가격 정보 표시
- 가격 변동 애니메이션

## 🌐 페이지 구성

- `/` - 메인 대시보드
- `/trading` - 거래 관리
- `/statistics` - 통계 분석
- `/strategy` - 전략 설정
- `/batch` - 배치 작업 관리

## 🧪 테스트

```bash
# 단위 테스트 실행
npm run test

# E2E 테스트 실행
npm run test:e2e

# 타입 체크
npm run check
```

## 🎯 빌드 및 배포

```bash
# 프로덕션 빌드
npm run build

# 정적 파일은 build/ 디렉토리에 생성됨
# Node.js 서버로 실행
node build
```

## ⚠️ 주의사항

- API 서버(trade_dashboard)가 실행 중이어야 함
- WebSocket 연결을 위해 CORS 설정 확인 필요
- 프로덕션 환경에서는 HTTPS 사용 권장

## 🤝 관련 서비스

- [Trade Batch](../trade_batch/README.md) - 배치 처리 서비스
- [Trade Dashboard](../trade_dashboard/README.md) - API 백엔드
- [Trade Engine](../trade_engine/README.md) - 트레이딩 엔진
