# 데이터베이스 외래키 관계 설명서

## 외래키 관계 다이어그램

```
contracts (주 테이블)
    ├── contract_details (1:1)
    ├── contract_details_stock (1:1)
    ├── contract_details_future (1:1)
    ├── contract_details_option (1:1)
    └── contract_details_index (1:1)

orders (독립 테이블)
    └── order_status_history (1:N)
    └── trade_events (1:N)

exchanges (독립 테이블)
exc_x_con (매핑 테이블 - 외래키 없음)
con_x_data (매핑 테이블 - 외래키 없음)
```

## 상세 외래키 관계

### 1. contracts 테이블 관련

#### contract_details → contracts
- **외래키**: `contract_details.con_id` → `contracts.con_id`
- **관계**: 1:1 (각 계약은 하나의 상세정보를 가짐)
- **CASCADE**: DELETE CASCADE (계약 삭제 시 상세정보도 삭제)

#### contract_details_stock → contracts
- **외래키**: `contract_details_stock.con_id` → `contracts.con_id`
- **관계**: 1:1 (주식 계약만 해당)
- **조건**: `contracts.sec_type = 'STK'`인 경우만

#### contract_details_future → contracts
- **외래키**: `contract_details_future.con_id` → `contracts.con_id`
- **관계**: 1:1 (선물 계약만 해당)
- **조건**: `contracts.sec_type = 'FUT'`인 경우만

#### contract_details_option → contracts
- **외래키**: `contract_details_option.con_id` → `contracts.con_id`
- **관계**: 1:1 (옵션 계약만 해당)
- **조건**: `contracts.sec_type = 'OPT'`인 경우만

#### contract_details_index → contracts
- **외래키**: `contract_details_index.con_id` → `contracts.con_id`
- **관계**: 1:1 (지수 계약만 해당)
- **조건**: `contracts.sec_type = 'IND'`인 경우만

### 2. orders 테이블 관련

#### order_status_history → orders
- **외래키**: `order_status_history.order_id` → `orders.order_id`
- **관계**: 1:N (하나의 주문은 여러 상태 변경 이력을 가짐)
- **CASCADE**: DELETE CASCADE

#### trade_events → orders
- **외래키**: `trade_events.order_id` → `orders.order_id`
- **관계**: 1:N (하나의 주문은 여러 체결 이벤트를 가질 수 있음)
- **CASCADE**: SET NULL (주문이 삭제되어도 거래 기록은 유지)

### 3. 매핑 테이블 (외래키 없음)

#### exc_x_con
- **설명**: 거래소와 계약(심볼) 간의 다대다 매핑
- **필드**: `exchange`, `symbol`
- **외래키 없는 이유**: 유연한 데이터 관리를 위해

#### con_x_data
- **설명**: 계약과 데이터 소스 간의 매핑
- **필드**: `contract`, `data_source`
- **외래키 없는 이유**: 데이터 소스는 동적으로 추가/삭제 가능

### 4. 독립 테이블

#### exchanges
- **설명**: 거래소 마스터 데이터
- **외래키**: 없음 (마스터 테이블)

#### price_time, price_range, price_volume
- **참조**: `con_id`를 포함하지만 외래키 제약은 없음
- **이유**: 대량 데이터 입력 성능을 위해

## 외래키 제약 조건 SQL

```sql
-- contract_details 관련
ALTER TABLE contract_details 
    ADD CONSTRAINT fk_contract_details_con_id 
    FOREIGN KEY (con_id) REFERENCES contracts(con_id) ON DELETE CASCADE;

ALTER TABLE contract_details_stock 
    ADD CONSTRAINT fk_contract_details_stock_con_id 
    FOREIGN KEY (con_id) REFERENCES contracts(con_id) ON DELETE CASCADE;

ALTER TABLE contract_details_future 
    ADD CONSTRAINT fk_contract_details_future_con_id 
    FOREIGN KEY (con_id) REFERENCES contracts(con_id) ON DELETE CASCADE;

ALTER TABLE contract_details_option 
    ADD CONSTRAINT fk_contract_details_option_con_id 
    FOREIGN KEY (con_id) REFERENCES contracts(con_id) ON DELETE CASCADE;

ALTER TABLE contract_details_index 
    ADD CONSTRAINT fk_contract_details_index_con_id 
    FOREIGN KEY (con_id) REFERENCES contracts(con_id) ON DELETE CASCADE;

-- orders 관련
ALTER TABLE order_status_history 
    ADD CONSTRAINT fk_order_status_history_order_id 
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE;

ALTER TABLE trade_events 
    ADD CONSTRAINT fk_trade_events_order_id 
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE SET NULL;
```

## 주의사항

1. **성능 고려사항**
   - 대량 데이터 테이블(price_*, trade_events)은 외래키 제약을 최소화
   - 필요시 인덱스만 생성하여 조회 성능 확보

2. **데이터 무결성**
   - 매핑 테이블은 애플리케이션 레벨에서 무결성 관리
   - 중요 마스터 데이터는 외래키로 강제

3. **마이그레이션 시**
   - 외래키 제약은 데이터 마이그레이션 후 추가
   - 기존 데이터 정합성 검증 필수