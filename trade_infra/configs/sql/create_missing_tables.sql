-- Missing tables creation

-- Contracts 테이블 재생성
CREATE TABLE IF NOT EXISTS contracts (
    conId INTEGER PRIMARY KEY,
    symbol VARCHAR(16) NOT NULL,
    secType VARCHAR(8) NOT NULL,
    lastTradeDateOrContractMonth VARCHAR(16),
    strike DOUBLE PRECISION,
    "right" VARCHAR(2),
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

-- Contract Details 재생성
ALTER TABLE contract_details 
    ADD CONSTRAINT contract_details_conid_fkey 
    FOREIGN KEY (conId) REFERENCES contracts(conId);

-- Trade Events 재생성 (하이퍼테이블)
CREATE TABLE IF NOT EXISTS trade_events (
    -- 체결 정보
    execId VARCHAR(50) NOT NULL,
    orderId VARCHAR(50),
    clientId INTEGER,
    permId BIGINT,
    
    -- 거래 정보
    time TIMESTAMPTZ NOT NULL,
    acctNumber VARCHAR(20),
    symbol VARCHAR(16) NOT NULL,
    secType VARCHAR(10),
    exchange VARCHAR(16),
    side VARCHAR(10) NOT NULL,
    shares DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    
    -- 포지션 변화
    position DECIMAL(15,8),
    avgCost DECIMAL(15,8),
    
    -- 손익
    realizedPNL DECIMAL(15,2),
    commission DECIMAL(10,4),
    
    -- IBKR 추가 정보
    cumQty DECIMAL(15,8),
    liquidation BOOLEAN DEFAULT FALSE,
    orderRef VARCHAR(50),
    evRule VARCHAR(50),
    evMultiplier DOUBLE PRECISION,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (execId, time)
);

-- 하이퍼테이블로 변환
SELECT create_hypertable('trade_events', 'time', 
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_trade_events_symbol ON trade_events(symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_trade_events_orderId ON trade_events(orderId);
CREATE INDEX IF NOT EXISTS idx_trade_events_acctNumber ON trade_events(acctNumber, time DESC);

-- 압축 정책 (나중에 추가)
-- ALTER TABLE trade_events SET (
--     timescaledb.compress,
--     timescaledb.compress_segmentby = 'symbol',
--     timescaledb.compress_orderby = 'time DESC'
-- );

-- SELECT add_compression_policy('trade_events', 
--     compress_after => INTERVAL '30 days',
--     if_not_exists => TRUE
-- );