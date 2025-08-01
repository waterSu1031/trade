-- =====================================================
-- 테이블명 변경 스크립트
-- =====================================================

\c trade_db

-- 1. exc_x_sym 테이블을 exc_x_con으로 변경
ALTER TABLE IF EXISTS exc_x_sym RENAME TO exc_x_con;

-- 2. sym_x_data 테이블을 con_x_data로 변경  
ALTER TABLE IF EXISTS sym_x_data RENAME TO con_x_data;

-- 3. con_x_data 테이블의 symbol 컬럼을 contract로 변경
ALTER TABLE IF EXISTS con_x_data RENAME COLUMN symbol TO contract;
    exchange VARCHAR(32) PRIMARY KEY,
    country VARCHAR(16),
    sec_type VARCHAR(8),
    aws_coverage VARCHAR(12),
    timezone VARCHAR(24),
    location_lat REAL,
    location_lon REAL,
    description VARCHAR(100),
    symbol_cnt INTEGER
);

-- 7. 기존 데이터 마이그레이션 (있는 필드만)
INSERT INTO exchange (exchange, timezone, description)
SELECT exchange, 
       CASE 
           WHEN LENGTH(timezone) > 24 THEN LEFT(timezone, 24)
           ELSE timezone
       END,
       CASE 
           WHEN LENGTH(description) > 100 THEN LEFT(description, 100)
           ELSE description
       END
FROM exchanges_backup;

-- 5. 외래키 제약조건이 있는 경우 업데이트
-- exc_x_sym 테이블의 외래키는 exchange 컬럼명이 같으므로 문제없음

-- 6. 증권 타입별 contract_detail 테이블 생성
CREATE TABLE IF NOT EXISTS contract_detail_stock (
    con_id INTEGER PRIMARY KEY REFERENCES contracts(conId),
    isin VARCHAR(12),
    cusip VARCHAR(9),
    ratings VARCHAR(50),
    desc_append VARCHAR(256),
    bond_type VARCHAR(50),
    coupon_type VARCHAR(50),
    callable BOOLEAN,
    putable BOOLEAN,
    coupon DECIMAL(10,4),
    convertible BOOLEAN,
    maturity DATE,
    issue_date DATE,
    next_option_date DATE,
    next_option_type VARCHAR(10),
    next_option_partial BOOLEAN,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contract_detail_future (
    con_id INTEGER PRIMARY KEY REFERENCES contracts(conId),
    contract_month VARCHAR(8),
    last_trade_date DATE,
    multiplier INTEGER,
    ev_rule VARCHAR(50),
    ev_multiplier DECIMAL(10,4),
    underlying_con_id INTEGER,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contract_detail_option (
    con_id INTEGER PRIMARY KEY REFERENCES contracts(conId),
    option_type VARCHAR(4),  -- CALL, PUT
    strike DECIMAL(15,4),
    expiry_date DATE,
    multiplier INTEGER,
    underlying_con_id INTEGER,
    underlying_symbol VARCHAR(16),
    exercise_style VARCHAR(10),  -- AMERICAN, EUROPEAN
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contract_detail_index (
    con_id INTEGER PRIMARY KEY REFERENCES contracts(conId),
    index_family VARCHAR(50),
    index_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO freeksj;

-- 8. 백업 테이블 삭제 (확인 후)
-- DROP TABLE IF EXISTS exchanges_backup;

\echo 'Table renaming completed:'
\echo '- contract_details → contract_detail'
\echo '- exchanges → exchange (with new structure)'
\echo '- Added: contract_detail_stock, contract_detail_future, contract_detail_option, contract_detail_index'