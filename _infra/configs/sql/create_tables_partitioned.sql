-- =====================================================
-- Trade System PostgreSQL Schema with Partitioning
-- Version: 3.0
-- Description: 1단계 파티션 적용 스키마
-- =====================================================

-- =====================================================
-- trade_db: 대시보드/실시간 데이터
-- =====================================================
\c trade_db

-- 대시보드용 테이블들은 trade_db에 유지
-- (trades, positions, sessions, accounts 등)

-- =====================================================
-- data_db: 시장 데이터 (TimescaleDB 포함)
-- =====================================================
\c data_db

-- TimescaleDB Extension 확인
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- =====================================================
-- 1. 마스터 데이터 (일반 테이블)
-- =====================================================

-- 종목 기본 정보 (이미 존재하면 스킵)
CREATE TABLE IF NOT EXISTS contracts (
    con_id INTEGER PRIMARY KEY,
    symbol VARCHAR(16) NOT NULL,
    sec_type VARCHAR(8) NOT NULL,
    last_trade_date_or_contract_month VARCHAR(16),
    strike DOUBLE PRECISION,
    right_ VARCHAR(2),
    multiplier VARCHAR(8),
    exchange VARCHAR(16) NOT NULL,
    primary_exch VARCHAR(16),
    currency VARCHAR(8) NOT NULL,
    local_symbol VARCHAR(32),
    trading_class VARCHAR(16),
    description VARCHAR(128),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 종목 상세 정보
CREATE TABLE IF NOT EXISTS contract_details (
    con_id INTEGER PRIMARY KEY REFERENCES contracts(con_id),
    market_name VARCHAR(32),
    min_tick DOUBLE PRECISION,
    price_magnifier INTEGER,
    order_types VARCHAR(128),
    valid_exchanges VARCHAR(128),
    long_name VARCHAR(128),
    time_zone_id VARCHAR(64),
    trading_hours VARCHAR(128),
    liquid_hours VARCHAR(128),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 거래소 정보
CREATE TABLE IF NOT EXISTS exchanges (
    exchange TEXT PRIMARY KEY,
    region TEXT,
    sec_type TEXT,
    timezone TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 거래소-종목 매핑
CREATE TABLE IF NOT EXISTS exchange_symbols (
    exchange VARCHAR(16) NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (exchange, symbol)
);

-- =====================================================
-- 2. Time Bar 데이터 (TimescaleDB 하이퍼테이블)
-- =====================================================

-- Time Bar 통합 테이블
CREATE TABLE IF NOT EXISTS price_time (
    time TIMESTAMPTZ NOT NULL,
    con_id INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    count INTEGER,
    vwap DECIMAL(12,4)
);

-- 하이퍼테이블로 변환 (주별 청크)
SELECT create_hypertable('price_time', 'time', 
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_price_time_symbol_time ON price_time (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_price_time_exchange_time ON price_time (exchange, time DESC);

-- 압축 설정
ALTER TABLE price_time SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);

-- 압축 정책 설정 (30일 후)
SELECT add_compression_policy('price_time', 
    compress_after => INTERVAL '30 days',
    if_not_exists => TRUE
);

-- =====================================================
-- 3. Range Bar 데이터 (PostgreSQL 심볼 파티션)
-- =====================================================

-- Range Bar 테이블 (심볼별 파티션)
CREATE TABLE IF NOT EXISTS price_range (
    symbol VARCHAR(16) NOT NULL,
    bar_number INTEGER NOT NULL,
    con_id INTEGER NOT NULL,
    range_size DECIMAL(12,4) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    tick_count INTEGER,
    PRIMARY KEY (symbol, bar_number)
) PARTITION BY LIST (symbol);

-- 주요 종목별 파티션 생성
DO $$
DECLARE
    symbols TEXT[] := ARRAY['ES', 'NQ', 'YM', 'RTY', 'CL', 'GC', 'SI'];
    sym TEXT;
BEGIN
    FOREACH sym IN ARRAY symbols
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS price_range_%s 
            PARTITION OF price_range 
            FOR VALUES IN (%L)',
            lower(sym), sym
        );
    END LOOP;
END $$;

-- DEFAULT 파티션 (기타 종목)
CREATE TABLE IF NOT EXISTS price_range_default 
PARTITION OF price_range DEFAULT;

-- =====================================================
-- 4. Volume Bar 데이터 (PostgreSQL 심볼 파티션)
-- =====================================================

-- Volume Bar 테이블 (심볼별 파티션)
CREATE TABLE IF NOT EXISTS price_volume (
    symbol VARCHAR(16) NOT NULL,
    bar_number INTEGER NOT NULL,
    con_id INTEGER NOT NULL,
    volume_threshold BIGINT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    tick_count INTEGER,
    PRIMARY KEY (symbol, bar_number)
) PARTITION BY LIST (symbol);

-- 주요 종목별 파티션 생성
DO $$
DECLARE
    symbols TEXT[] := ARRAY['ES', 'NQ', 'YM', 'RTY', 'CL', 'GC', 'SI'];
    sym TEXT;
BEGIN
    FOREACH sym IN ARRAY symbols
    LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS price_volume_%s 
            PARTITION OF price_volume 
            FOR VALUES IN (%L)',
            lower(sym), sym
        );
    END LOOP;
END $$;

-- DEFAULT 파티션 (기타 종목)
CREATE TABLE IF NOT EXISTS price_volume_default 
PARTITION OF price_volume DEFAULT;

-- =====================================================
-- 5. 거래 이벤트 (TimescaleDB 하이퍼테이블)
-- =====================================================

-- 거래 이벤트 테이블
CREATE TABLE IF NOT EXISTS trade_events (
    event_id VARCHAR(50),
    executed_at TIMESTAMPTZ NOT NULL,
    
    -- 거래 정보
    symbol VARCHAR(20) NOT NULL,
    sec_type VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    commission DECIMAL(10,4),
    
    -- 포지션 스냅샷
    position_before DECIMAL(15,8),
    position_after DECIMAL(15,8),
    avg_cost_before DECIMAL(15,8),
    avg_cost_after DECIMAL(15,8),
    
    -- 계좌 스냅샷
    account_value DECIMAL(15,2),
    cash_balance DECIMAL(15,2),
    buying_power DECIMAL(15,2),
    daily_pnl DECIMAL(15,2),
    
    -- 손익
    realized_pnl DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, executed_at)
);

-- 하이퍼테이블로 변환
SELECT create_hypertable('trade_events', 'executed_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_trade_events_symbol ON trade_events(symbol, executed_at DESC);

-- =====================================================
-- 6. 통계 테이블
-- =====================================================

-- 일일 통계
CREATE TABLE IF NOT EXISTS daily_statistics (
    date DATE,
    sec_type VARCHAR(10),
    
    -- 거래 통계
    total_trades INTEGER,
    total_volume DECIMAL(15,2),
    
    -- 손익 통계
    gross_pnl DECIMAL(15,2),
    net_pnl DECIMAL(15,2),
    commission DECIMAL(10,2),
    
    -- 승률 통계
    win_trades INTEGER,
    loss_trades INTEGER,
    win_rate DECIMAL(5,2),
    profit_factor DECIMAL(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, sec_type)
);

-- =====================================================
-- 7. 권한 설정
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO freeksj;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO freeksj;