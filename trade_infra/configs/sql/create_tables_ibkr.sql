-- =====================================================
-- Trade System PostgreSQL Schema (IBKR Field Names)
-- Version: 4.0
-- Description: Event-based schema with IBKR-compatible field names
-- =====================================================

-- trade_db 연결
\c trade_db

-- TimescaleDB Extension 확인
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- =====================================================
-- 1. 마스터 데이터 (Master Data)
-- =====================================================

-- Contracts 테이블 (IBKR Contract 객체 매핑)
CREATE TABLE IF NOT EXISTS contracts (
    conId INTEGER PRIMARY KEY,
    symbol VARCHAR(16) NOT NULL,
    secType VARCHAR(8) NOT NULL,        -- STK, FUT, OPT, CASH, etc.
    lastTradeDateOrContractMonth VARCHAR(16),
    strike DOUBLE PRECISION,
    "right" VARCHAR(2),                 -- C, P (Call, Put)
    multiplier VARCHAR(8),
    exchange VARCHAR(16) NOT NULL,
    primaryExchange VARCHAR(16),
    currency VARCHAR(8) NOT NULL,
    localSymbol VARCHAR(32),
    tradingClass VARCHAR(16),
    description VARCHAR(256),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contract Details 테이블
CREATE TABLE IF NOT EXISTS contract_details (
    conId INTEGER PRIMARY KEY REFERENCES contracts(conId),
    marketName VARCHAR(32),
    minTick DOUBLE PRECISION,
    priceMagnifier INTEGER,
    orderTypes VARCHAR(256),            -- 허용된 주문 타입들
    validExchanges VARCHAR(256),
    longName VARCHAR(128),
    timeZoneId VARCHAR(64),
    tradingHours VARCHAR(256),
    liquidHours VARCHAR(256),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exchanges 테이블
CREATE TABLE IF NOT EXISTS exchanges (
    exchange VARCHAR(16) PRIMARY KEY,
    region VARCHAR(32),
    timezone VARCHAR(64),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exchange-Symbol 매핑 테이블
CREATE TABLE IF NOT EXISTS exc_x_sym (
    exchange VARCHAR(16) NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (exchange, symbol)
);

-- Symbol-DataSource 매핑 테이블
CREATE TABLE IF NOT EXISTS sym_x_data (
    symbol VARCHAR(16) NOT NULL,
    data_source VARCHAR(32) NOT NULL,   -- 'time', 'range', 'volume'
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, data_source)
);

-- =====================================================
-- 2. 주문 관리 (Order Management)
-- =====================================================

-- Orders 테이블 (IBKR Order 객체 매핑)
CREATE TABLE IF NOT EXISTS orders (
    -- IBKR 기본 필드
    orderId VARCHAR(50) PRIMARY KEY,
    clientId INTEGER,
    permId BIGINT,
    parentId VARCHAR(50),
    
    -- 주문 정보
    symbol VARCHAR(16) NOT NULL,
    secType VARCHAR(10),                -- STK, FUT, OPT
    exchange VARCHAR(16),
    action VARCHAR(10) NOT NULL,        -- BUY, SELL
    orderType VARCHAR(20) NOT NULL,     -- MKT, LMT, STP, STP_LMT
    totalQuantity DECIMAL(15,8) NOT NULL,
    lmtPrice DECIMAL(15,8),
    auxPrice DECIMAL(15,8),             -- Stop price
    
    -- IBKR 추가 필드
    tif VARCHAR(10),                    -- DAY, GTC, IOC, GTD
    ocaGroup VARCHAR(50),               -- One-Cancels-All group
    ocaType INTEGER,                    -- 1=Cancel with block, 2=Reduce with block, 3=Reduce without block
    orderRef VARCHAR(50),               -- Order reference
    transmit BOOLEAN DEFAULT TRUE,
    account VARCHAR(20),
    
    -- 상태
    status VARCHAR(20) NOT NULL,        -- PendingSubmit, PreSubmitted, Submitted, Filled, Cancelled
    filled DECIMAL(15,8) DEFAULT 0,
    remaining DECIMAL(15,8),
    avgFillPrice DECIMAL(15,8),
    
    -- 시간
    placeTime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lastFillTime TIMESTAMPTZ,
    cancelledTime TIMESTAMPTZ,
    
    -- 메타데이터
    strategyName VARCHAR(50),
    notes TEXT
);

-- 인덱스
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_placeTime ON orders(placeTime DESC);
CREATE INDEX idx_orders_account ON orders(account);

-- Order Status History 테이블
CREATE TABLE IF NOT EXISTS order_status_history (
    id SERIAL PRIMARY KEY,
    orderId VARCHAR(50) REFERENCES orders(orderId),
    status VARCHAR(20) NOT NULL,
    filled DECIMAL(15,8),
    remaining DECIMAL(15,8),
    avgFillPrice DECIMAL(15,8),
    lastFillPrice DECIMAL(15,8),
    whyHeld VARCHAR(256),               -- IBKR가 주문을 보류한 이유
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message TEXT
);

-- 인덱스
CREATE INDEX idx_order_status_history_orderId ON order_status_history(orderId);
CREATE INDEX idx_order_status_history_timestamp ON order_status_history(timestamp DESC);

-- =====================================================
-- 3. 거래 이벤트 (Trade Events) - TimescaleDB
-- =====================================================

-- Trade Events 테이블 (IBKR Execution 객체 매핑)
CREATE TABLE IF NOT EXISTS trade_events (
    -- 체결 정보
    execId VARCHAR(50),
    orderId VARCHAR(50),
    clientId INTEGER,
    permId BIGINT,
    
    -- 거래 정보
    time TIMESTAMPTZ NOT NULL,
    acctNumber VARCHAR(20),             -- IBKR account number
    symbol VARCHAR(16) NOT NULL,
    secType VARCHAR(10),
    exchange VARCHAR(16),
    side VARCHAR(10) NOT NULL,          -- BOT, SLD (IBKR 스타일)
    shares DECIMAL(15,8) NOT NULL,      -- 체결 수량
    price DECIMAL(15,8) NOT NULL,       -- 체결 가격
    
    -- 포지션 변화 (해당 심볼만)
    position DECIMAL(15,8),             -- 체결 후 포지션
    avgCost DECIMAL(15,8),              -- 체결 후 평균단가
    
    -- 손익
    realizedPNL DECIMAL(15,2),
    commission DECIMAL(10,4),
    
    -- IBKR 추가 정보
    cumQty DECIMAL(15,8),               -- 누적 체결량
    liquidation BOOLEAN DEFAULT FALSE,
    orderRef VARCHAR(50),
    evRule VARCHAR(50),                 -- Execution rule
    evMultiplier DOUBLE PRECISION,      -- Execution multiplier
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (execId, time)
);

-- TimescaleDB 하이퍼테이블로 변환
SELECT create_hypertable('trade_events', 'time', 
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- 인덱스
CREATE INDEX idx_trade_events_symbol ON trade_events(symbol, time DESC);
CREATE INDEX idx_trade_events_orderId ON trade_events(orderId);
CREATE INDEX idx_trade_events_acctNumber ON trade_events(acctNumber, time DESC);

-- 압축 설정
ALTER TABLE trade_events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);

-- 압축 정책 (30일 후)
SELECT add_compression_policy('trade_events', 
    compress_after => INTERVAL '30 days',
    if_not_exists => TRUE
);

-- =====================================================
-- 4. 시장 데이터 (Market Data)
-- =====================================================

-- Time Bar 데이터 (TimescaleDB)
CREATE TABLE IF NOT EXISTS price_time (
    time TIMESTAMPTZ NOT NULL,
    conId INTEGER NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    count INTEGER,                      -- tick count
    vwap DECIMAL(12,4),                -- Volume Weighted Average Price
    hasGaps BOOLEAN DEFAULT FALSE       -- IBKR hasGaps flag
);

-- 하이퍼테이블로 변환
SELECT create_hypertable('price_time', 'time', 
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

-- 인덱스
CREATE INDEX idx_price_time_symbol ON price_time(symbol, time DESC);
CREATE INDEX idx_price_time_conId ON price_time(conId, time DESC);

-- Range Bar 데이터 (파티션)
CREATE TABLE IF NOT EXISTS price_range (
    symbol VARCHAR(16) NOT NULL,
    barNumber INTEGER NOT NULL,
    conId INTEGER NOT NULL,
    rangeSize DECIMAL(12,4) NOT NULL,
    startTime TIMESTAMPTZ NOT NULL,
    endTime TIMESTAMPTZ NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    tickCount INTEGER,
    PRIMARY KEY (symbol, barNumber)
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

-- DEFAULT 파티션
CREATE TABLE IF NOT EXISTS price_range_default 
PARTITION OF price_range DEFAULT;

-- Volume Bar 데이터 (파티션)
CREATE TABLE IF NOT EXISTS price_volume (
    symbol VARCHAR(16) NOT NULL,
    barNumber INTEGER NOT NULL,
    conId INTEGER NOT NULL,
    volumeThreshold BIGINT NOT NULL,
    startTime TIMESTAMPTZ NOT NULL,
    endTime TIMESTAMPTZ NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    tickCount INTEGER,
    PRIMARY KEY (symbol, barNumber)
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

-- DEFAULT 파티션
CREATE TABLE IF NOT EXISTS price_volume_default 
PARTITION OF price_volume DEFAULT;

-- =====================================================
-- 5. 통계 테이블 (Statistics)
-- =====================================================

-- Daily Statistics
CREATE TABLE IF NOT EXISTS daily_statistics (
    date DATE,
    secType VARCHAR(10),
    
    -- 거래 통계
    totalTrades INTEGER,
    totalVolume DECIMAL(15,2),
    
    -- 손익 통계
    grossPnl DECIMAL(15,2),
    netPnl DECIMAL(15,2),
    commission DECIMAL(10,2),
    
    -- 승률 통계
    winTrades INTEGER,
    lossTrades INTEGER,
    winRate DECIMAL(5,2),
    profitFactor DECIMAL(10,2),
    
    -- 추가 메트릭
    sharpeRatio DECIMAL(10,4),
    maxDrawdown DECIMAL(10,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, secType)
);

-- =====================================================
-- 6. 권한 설정
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO freeksj;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO freeksj;

-- =====================================================
-- 7. 데이터 정합성 체크 함수
-- =====================================================

-- 포지션 계산 함수 (예시)
CREATE OR REPLACE FUNCTION calculate_position(p_symbol VARCHAR, p_account VARCHAR)
RETURNS TABLE(
    symbol VARCHAR,
    position_qty DECIMAL,
    avgCost DECIMAL,
    realizedPNL DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.symbol,
        SUM(CASE WHEN t.side = 'BOT' THEN t.shares ELSE -t.shares END) as position_qty,
        CASE 
            WHEN SUM(CASE WHEN t.side = 'BOT' THEN t.shares ELSE -t.shares END) > 0
            THEN SUM(CASE WHEN t.side = 'BOT' THEN t.shares * t.price ELSE 0 END) / 
                 NULLIF(SUM(CASE WHEN t.side = 'BOT' THEN t.shares ELSE 0 END), 0)
            ELSE 0
        END as avgCost,
        SUM(t.realizedPNL) as realizedPNL
    FROM trade_events t
    WHERE t.symbol = p_symbol 
    AND t.acctNumber = p_account
    GROUP BY t.symbol;
END;
$$ LANGUAGE plpgsql;