-- =====================================================
-- Trade System PostgreSQL Schema
-- Version: 1.0
-- Description: 자동매매 시스템을 위한 데이터베이스 스키마
-- =====================================================

-- =====================================================
-- 1. 거래소 및 종목 관련 테이블
-- =====================================================

-- 거래소 정보
CREATE TABLE IF NOT EXISTS exchange (
    exchange TEXT PRIMARY KEY,
    region TEXT,
    sec_type TEXT,
    total_cnt INTEGER,
    aws_coverage TEXT,
    timezone TEXT,
    location_lat REAL,
    location_lon REAL,
    description TEXT
);

-- 종목 기본 정보 (IBKR Contract)
CREATE TABLE IF NOT EXISTS contract (
    con_id INTEGER PRIMARY KEY,
    symbol VARCHAR(16) NOT NULL,
    sec_type VARCHAR(8) NOT NULL,
    last_trade_date_or_contract_month VARCHAR(16),
    crt_month_con_id INTEGER,
    last_trade_date VARCHAR(16),
    strike DOUBLE PRECISION,
    right_ VARCHAR(2),
    multiplier VARCHAR(8),
    exchange VARCHAR(16) NOT NULL,
    primary_exch VARCHAR(16),
    currency VARCHAR(8) NOT NULL,
    local_symbol VARCHAR(32),
    trading_class VARCHAR(16),
    sec_id_type VARCHAR(16),
    sec_id VARCHAR(32),
    description VARCHAR(128),
    issuer_id VARCHAR(32),
    delta_neutral_conid INTEGER,
    include_expired BOOLEAN DEFAULT FALSE
);

-- 종목 상세 정보 (ContractDetails)
CREATE TABLE IF NOT EXISTS contract_detail (
    con_id INTEGER PRIMARY KEY REFERENCES contract(con_id),
    market_name VARCHAR(32),
    min_tick DOUBLE PRECISION,
    price_magnifier INTEGER,
    order_types VARCHAR(128),
    valid_exchanges VARCHAR(128),
    long_name VARCHAR(128),
    time_zone_id VARCHAR(64),
    trading_hours VARCHAR(128),
    liquid_hours VARCHAR(128),
    agg_group INTEGER,
    market_rule_ids VARCHAR(64)
);

-- 주식 상세 정보
CREATE TABLE IF NOT EXISTS contract_detail_stock (
    con_id INTEGER PRIMARY KEY REFERENCES contract(con_id),
    industry VARCHAR(64),
    category VARCHAR(64),
    subcategory VARCHAR(64),
    stock_type VARCHAR(16)
);

-- 선물 상세 정보
CREATE TABLE IF NOT EXISTS contract_detail_future (
    con_id INTEGER PRIMARY KEY REFERENCES contract(con_id),
    contract_month VARCHAR(8),
    real_expiration_date VARCHAR(16),
    last_trade_time VARCHAR(32),
    ev_rule VARCHAR(32),
    ev_multiplier DOUBLE PRECISION,
    under_conid INTEGER,
    under_symbol VARCHAR(32),
    under_sec_type VARCHAR(16)
);

-- 옵션 상세 정보
CREATE TABLE IF NOT EXISTS contract_detail_option (
    con_id INTEGER PRIMARY KEY REFERENCES contract(con_id),
    contract_month VARCHAR(8),
    real_expiration_date VARCHAR(16),
    last_trade_time VARCHAR(32),
    ev_rule VARCHAR(32),
    ev_multiplier DOUBLE PRECISION,
    under_conid INTEGER,
    under_symbol VARCHAR(32),
    under_sec_type VARCHAR(16)
);

-- 종목별 데이터 관리 메타 정보
CREATE TABLE IF NOT EXISTS sym_x_data (
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    data_type VARCHAR(8) NOT NULL,
    size DECIMAL(16,4),
    stt_date_loc TIMESTAMP NOT NULL,
    end_date_loc TIMESTAMP NOT NULL,
    row_count BIGINT,
    data_status VARCHAR(16),
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, exchange, data_type, size)
);

-- CSV에서 가져온 심볼 정보
CREATE TABLE IF NOT EXISTS symbol_from_csv (
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    currency VARCHAR(8) NOT NULL,
    sec_type VARCHAR(8) NOT NULL,
    PRIMARY KEY (symbol, exchange)
);

-- 거래소별 종목 연결 테이블
CREATE TABLE IF NOT EXISTS exc_x_sym (
    exchange VARCHAR(16) NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    PRIMARY KEY (exchange, symbol)
);

-- =====================================================
-- 2. 시장 데이터 테이블 (리전별)
-- =====================================================

-- 미국 시계열 데이터
CREATE TABLE IF NOT EXISTS price_US_time (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    count INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc)
) PARTITION BY LIST (symbol);

-- 중국 시계열 데이터
CREATE TABLE IF NOT EXISTS price_CN_time (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    count INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc)
) PARTITION BY LIST (symbol);

-- 유럽 시계열 데이터
CREATE TABLE IF NOT EXISTS price_EU_time (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    count INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc)
) PARTITION BY LIST (symbol);

-- 미국 레인지바 데이터
CREATE TABLE IF NOT EXISTS price_US_range (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    range_size DECIMAL(8,4) NOT NULL,
    idx INTEGER NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    cnt INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc, range_size, idx)
) PARTITION BY LIST (symbol);

-- 중국 레인지바 데이터
CREATE TABLE IF NOT EXISTS price_CN_range (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    range_size DECIMAL(8,4) NOT NULL,
    idx INTEGER NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    cnt INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc, range_size, idx)
) PARTITION BY LIST (symbol);

-- 유럽 레인지바 데이터
CREATE TABLE IF NOT EXISTS price_EU_range (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    range_size DECIMAL(8,4) NOT NULL,
    idx INTEGER NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    cnt INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc, range_size, idx)
) PARTITION BY LIST (symbol);

-- 미국 볼륨바 데이터
CREATE TABLE IF NOT EXISTS price_US_volume (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    vol_size BIGINT NOT NULL,
    idx INTEGER NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    cnt INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc, vol_size, idx)
) PARTITION BY LIST (symbol);

-- 중국 볼륨바 데이터
CREATE TABLE IF NOT EXISTS price_CN_volume (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    vol_size BIGINT NOT NULL,
    idx INTEGER NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    cnt INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc, vol_size, idx)
) PARTITION BY LIST (symbol);

-- 유럽 볼륨바 데이터
CREATE TABLE IF NOT EXISTS price_EU_volume (
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    utc TIMESTAMP NOT NULL,
    loc TIMESTAMP NOT NULL,
    vol_size BIGINT NOT NULL,
    idx INTEGER NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    cnt INTEGER,
    vwap DECIMAL(12,4),
    PRIMARY KEY (con_id, symbol, utc, vol_size, idx)
) PARTITION BY LIST (symbol);

-- =====================================================
-- 3. 통합 뷰
-- =====================================================

-- 시계열 데이터 통합 뷰
CREATE OR REPLACE VIEW price_time AS
SELECT * FROM price_US_time
UNION ALL
SELECT * FROM price_CN_time
UNION ALL
SELECT * FROM price_EU_time;

-- 레인지바 데이터 통합 뷰
CREATE OR REPLACE VIEW price_range AS
SELECT * FROM price_US_range
UNION ALL
SELECT * FROM price_CN_range
UNION ALL
SELECT * FROM price_EU_range;

-- 볼륨바 데이터 통합 뷰
CREATE OR REPLACE VIEW price_volume AS
SELECT * FROM price_US_volume
UNION ALL
SELECT * FROM price_CN_volume
UNION ALL
SELECT * FROM price_EU_volume;

-- =====================================================
-- 4. 인덱스 생성
-- =====================================================

-- 시계열 데이터 인덱스
CREATE INDEX IF NOT EXISTS idx_price_us_time_symbol ON price_US_time(symbol, exchange, utc);
CREATE INDEX IF NOT EXISTS idx_price_cn_time_symbol ON price_CN_time(symbol, exchange, utc);
CREATE INDEX IF NOT EXISTS idx_price_eu_time_symbol ON price_EU_time(symbol, exchange, utc);

-- 레인지바 데이터 인덱스
CREATE INDEX IF NOT EXISTS idx_price_us_range_symbol ON price_US_range(symbol, exchange, utc);
CREATE INDEX IF NOT EXISTS idx_price_cn_range_symbol ON price_CN_range(symbol, exchange, utc);
CREATE INDEX IF NOT EXISTS idx_price_eu_range_symbol ON price_EU_range(symbol, exchange, utc);

-- 볼륨바 데이터 인덱스
CREATE INDEX IF NOT EXISTS idx_price_us_volume_symbol ON price_US_volume(symbol, exchange, utc);
CREATE INDEX IF NOT EXISTS idx_price_cn_volume_symbol ON price_CN_volume(symbol, exchange, utc);
CREATE INDEX IF NOT EXISTS idx_price_eu_volume_symbol ON price_EU_volume(symbol, exchange, utc);

-- =====================================================
-- 5. 파티션 생성 예시 (주요 심볼)
-- =====================================================

-- 미국 시계열 파티션
CREATE TABLE IF NOT EXISTS price_US_time_ES PARTITION OF price_US_time FOR VALUES IN ('ES');
CREATE TABLE IF NOT EXISTS price_US_time_NQ PARTITION OF price_US_time FOR VALUES IN ('NQ');
CREATE TABLE IF NOT EXISTS price_US_time_YM PARTITION OF price_US_time FOR VALUES IN ('YM');
CREATE TABLE IF NOT EXISTS price_US_time_RTY PARTITION OF price_US_time FOR VALUES IN ('RTY');
CREATE TABLE IF NOT EXISTS price_US_time_CL PARTITION OF price_US_time FOR VALUES IN ('CL');
CREATE TABLE IF NOT EXISTS price_US_time_GC PARTITION OF price_US_time FOR VALUES IN ('GC');
CREATE TABLE IF NOT EXISTS price_US_time_SI PARTITION OF price_US_time FOR VALUES IN ('SI');

-- 중국 시계열 파티션
CREATE TABLE IF NOT EXISTS price_CN_time_A50 PARTITION OF price_CN_time FOR VALUES IN ('A50');
CREATE TABLE IF NOT EXISTS price_CN_time_HSI PARTITION OF price_CN_time FOR VALUES IN ('HSI');

-- 유럽 시계열 파티션 (필요시 추가)

-- 레인지바, 볼륨바도 동일하게 파티션 생성 가능

-- =====================================================
-- 6. 권한 설정
-- =====================================================

-- 사용자에게 권한 부여 (username을 실제 사용자로 변경)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO freeksj;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO freeksj;