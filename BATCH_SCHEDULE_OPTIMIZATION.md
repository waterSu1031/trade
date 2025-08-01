# Trade System 배치 스케줄 최적화 가이드

## 개요
전세계 선물시장의 거래시간을 고려하여 Trade System의 배치 작업 스케줄을 최적화했습니다.

## 주요 변경사항

### 1. 기본 배치 스케줄 변경 (BatchScheduler.java)

#### 이전 스케줄 (문제점)
- 01:00 - setInitStructureJob
- 02:00 - addFutureMonthJob  
- 03:00 - collectTypeDataJob (미국 시장 활발)
- 04:00 - taskletJob

#### 새로운 스케줄 (최적화)
- **07:00** - setInitStructureJob
  - CME 일일 정산 완료 후
  - 아시아 시장 개장 전 초기 구조 설정
  
- **07:30** - addFutureMonthJob
  - 초기 구조 설정 후 선물 월물 추가
  - 주말/월초에 새로운 월물 반영
  
- **18:00** - collectTypeDataJob
  - 아시아 시장 마감 후 데이터 수집
  - 유럽 시장 본격 시작 전
  
- **06:30** - taskletJob
  - 미국 시장 마감 후
  - 다음날 아시아 개장 전 정리 작업

### 2. 시장별 데이터 수집 스케줄 (MarketSpecificScheduler.java)

새로운 시장별 데이터 수집 스케줄러를 추가하여 각 시장 마감 후 데이터를 수집합니다:

- **16:00 KST** - 아시아 시장 데이터 수집 (KRX, JPX, SGX, HKEX)
- **01:00 KST** - 유럽 시장 데이터 수집 (Eurex, LSE, Euronext)
- **06:00 KST** - 미국 시장 데이터 수집 (CME, ICE, CBOE)
- **09:00 KST** - 암호화폐 시장 일일 정산

### 3. IBKR 연결 모니터링 강화 (MarketAwareConnectionMonitor.java)

#### 시장 개장 전 체크
- **08:30 KST** - 아시아 시장 개장 30분 전
- **15:30 KST** - 유럽 시장 개장 30분 전
- **22:00 KST** - 미국 시장 개장 30분 전

#### 동적 모니터링 주기
- **활성 거래 시간**: 1분마다 체크
  - 아시아: 09:00-15:30 KST
  - 유럽: 16:00-00:30 KST
  - 미국: 22:30-05:00 KST
- **비활성 시간**: 5분마다 체크

#### 시장 전환 시간대 추가 체크
- **09:00 KST** - 아시아 개장
- **16:00 KST** - 유럽 개장
- **22:30 KST** - 미국 개장

### 4. 휴일 처리 로직 (MarketHolidayCalendar.java & HolidayAwareBatchScheduler.java)

#### 주요 기능
- 2025년 주요 거래소 휴일 캘린더 관리
- 시장별 휴일 체크 및 배치 작업 스킵
- 다음/이전 거래일 계산
- 연말연시 특별 처리

#### 지원 거래소
- KRX (한국거래소)
- JPX (일본거래소)
- CME (시카고상품거래소)
- Eurex (유럽거래소)

## 글로벌 시장 거래시간 참고 (KST 기준)

### 주요 거래소
1. **CME Group**
   - 전자거래: 월 07:00 - 토 06:00 (거의 24시간)
   - 일일 휴장: 06:00-07:00

2. **Eurex**
   - 아시아 세션: 09:00-16:00
   - 유럽 세션: 16:00-01:30
   - 미국 세션: 01:30-06:00

3. **아시아 거래소**
   - KRX: 09:00-15:30
   - JPX: 09:00-15:25 (점심 11:30-12:30)
   - SGX: 09:00-17:00
   - HKEX: 09:00-17:00

### 시장 오버랩 시간대
- 아시아-유럽: 16:00-18:00 KST
- 유럽-미국: 22:30-01:00 KST
- 미국-아시아: 06:00-09:00 KST

## 구현 파일 목록

1. `/trade_batch/src/main/java/com/trade/batch/endpoint/BatchScheduler.java`
   - 기본 배치 스케줄 업데이트

2. `/trade_batch/src/main/java/com/trade/batch/endpoint/MarketSpecificScheduler.java`
   - 시장별 데이터 수집 스케줄러 (신규)

3. `/trade_batch/src/main/java/com/trade/batch/service/MarketAwareConnectionMonitor.java`
   - 시장 시간대 고려 연결 모니터링 (신규)

4. `/trade_batch/src/main/java/com/trade/batch/config/MarketHolidayCalendar.java`
   - 글로벌 시장 휴일 캘린더 (신규)

5. `/trade_batch/src/main/java/com/trade/batch/endpoint/HolidayAwareBatchScheduler.java`
   - 휴일 고려 배치 스케줄러 (신규)

## 추가 고려사항

### 1. 동적 스케줄링
- 휴일이나 특수 상황에 대한 동적 스케줄 조정 필요
- Spring의 TaskScheduler를 활용한 런타임 스케줄 변경 검토

### 2. 시간대 처리
- 모든 스케줄은 KST(한국표준시) 기준
- DST(일광절약시간) 전환 시 주의 필요

### 3. 모니터링 및 알림
- 배치 작업 실패 시 알림 메커니즘 구현 필요
- 연결 상태 대시보드 구성 권장

### 4. 성능 최적화
- 시장별 데이터 수집 병렬 처리 검토
- 대용량 데이터 처리 시 청크 단위 처리

## 다음 단계

1. 개발 환경에서 새 스케줄 테스트
2. 로그 모니터링을 통한 스케줄 검증
3. 프로덕션 배포 전 스테이징 환경 검증
4. 휴일 캘린더 정기 업데이트 프로세스 수립