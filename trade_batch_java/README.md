# Trade Batch Service

Spring Boot 기반의 배치 처리 서비스로, Interactive Brokers(IBKR)와 연동하여 시장 데이터를 수집하고 처리합니다.

## 🚀 주요 기능

- **실시간 데이터 수집**: IBKR API를 통한 실시간 시장 데이터 수집
- **배치 작업 스케줄링**: 일별 통계, 데이터 동기화, 파티션 관리 등
- **데이터 무결성 검증**: 수집된 데이터의 정합성 검증
- **다중 데이터소스 지원**: 지역별 데이터베이스 라우팅 (US, CN, EU)

## 📋 기술 스택

- Java 17
- Spring Boot 3.x
- Spring Batch
- PostgreSQL (TimescaleDB)
- IBKR TWS API
- Maven

## 🛠️ 설정 및 실행

### 사전 요구사항

- JDK 17 이상
- Maven 3.6 이상
- PostgreSQL 15 이상
- IBKR TWS/Gateway 실행 중

### 환경 설정

1. 환경 변수 설정 (.env 파일 생성):
```bash
IB_HOST=localhost
IB_PORT=4001
IB_CLIENT_ID_BATCH=30
IB_USERNAME=your_username
IB_PASSWORD=your_password
```

2. 데이터베이스 설정:
- `application.yaml`에서 데이터베이스 연결 정보 확인
- 필요시 환경에 맞게 수정

### 빌드 및 실행

```bash
# 빌드
./mvnw clean package

# 실행
./mvnw spring-boot:run

# 또는 JAR 파일 직접 실행
java -jar target/trade-batch-*.jar
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t trade-batch .

# 컨테이너 실행
docker run -p 8080:8080 --env-file .env trade-batch
```

## 📁 프로젝트 구조

```
src/main/java/com/trade/batch/
├── config/          # 설정 클래스
├── endpoint/        # REST API 및 스케줄러
├── health/          # 헬스체크
├── ibkr/           # IBKR 연동
├── job/            # 배치 작업 정의
├── repository/     # 데이터 접근 계층
└── service/        # 비즈니스 로직
```

## 🔌 주요 배치 작업

### 1. CollectDataJob
- 실시간 시장 데이터 수집
- IBKR API를 통한 가격 정보 저장

### 2. DailyStatisticsJob
- 일별 거래 통계 계산
- 성과 지표 생성

### 3. DataIntegrityJob
- 데이터 정합성 검증
- 누락 데이터 감지 및 보정

### 4. DataSyncJob
- 데이터베이스 간 동기화
- 백업 및 복구

### 5. PartitionManagementJob
- TimescaleDB 파티션 관리
- 오래된 파티션 자동 삭제

## 🌐 API 엔드포인트

- `GET /actuator/health` - 서비스 상태 확인
- `POST /batch/run/{jobName}` - 배치 작업 수동 실행
- `GET /batch/status/{jobName}` - 작업 상태 조회

## 🧪 테스트

```bash
# 단위 테스트 실행
./mvnw test

# 특정 테스트 클래스 실행
./mvnw test -Dtest=BatchApplicationTests
```

## 📊 모니터링

- Spring Actuator를 통한 헬스체크
- IBKR 연결 상태 모니터링
- 배치 작업 실행 로그

## ⚠️ 주의사항

- IBKR TWS/Gateway가 실행 중이어야 함
- Paper Trading: 포트 4002 사용
- Live Trading: 포트 4001 사용
- 각 서비스별로 고유한 Client ID 사용 필요

## 🤝 관련 서비스

- [Trade Dashboard](../trade_dashboard/README.md) - 대시보드 백엔드
- [Trade Engine](../trade_engine/README.md) - 트레이딩 엔진
- [Trade Frontend](../trade_frontend/README.md) - 웹 인터페이스