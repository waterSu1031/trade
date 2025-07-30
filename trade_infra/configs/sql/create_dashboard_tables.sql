-- =====================================================
-- Dashboard Compatibility Tables
-- =====================================================

\c trade_db

-- Trading Sessions 테이블 (대시보드용)
CREATE TABLE IF NOT EXISTS trading_sessions (
    id SERIAL PRIMARY KEY,
    session_date TIMESTAMP NOT NULL,
    total_trades INTEGER DEFAULT 0,
    total_volume FLOAT DEFAULT 0.0,
    gross_pnl FLOAT DEFAULT 0.0,
    net_pnl FLOAT DEFAULT 0.0,
    commission FLOAT DEFAULT 0.0,
    win_trades INTEGER DEFAULT 0,
    loss_trades INTEGER DEFAULT 0,
    win_rate FLOAT DEFAULT 0.0,
    largest_win FLOAT DEFAULT 0.0,
    largest_loss FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_trading_sessions_date ON trading_sessions(session_date DESC);

-- =====================================================
-- 호환성을 위한 VIEW (선택사항)
-- =====================================================

-- 최신 거래 VIEW (trades 테이블 대체)
CREATE OR REPLACE VIEW trades AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY time DESC) as id,
    orderId as order_id,
    symbol,
    side as action,  -- BOT -> BUY, SLD -> SELL
    shares as quantity,
    price,
    commission,
    realizedPNL as realized_pnl,
    'FILLED' as status,  -- trade_events는 체결된 것만 저장
    exchange,
    'USD' as currency,
    time as execution_time,
    created_at,
    created_at as updated_at
FROM trade_events;

-- 현재 포지션 VIEW (positions 테이블 대체)
CREATE OR REPLACE VIEW positions AS
WITH latest_positions AS (
    SELECT 
        symbol,
        SUM(CASE WHEN side = 'BOT' THEN shares ELSE -shares END) as quantity,
        AVG(CASE WHEN side = 'BOT' THEN price END) as avg_cost,
        SUM(realizedPNL) as realized_pnl,
        MAX(time) as last_update
    FROM trade_events
    GROUP BY symbol
    HAVING SUM(CASE WHEN side = 'BOT' THEN shares ELSE -shares END) != 0
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY symbol) as id,
    symbol,
    quantity,
    avg_cost,
    0.0 as market_price,  -- 실시간으로 업데이트 필요
    0.0 as market_value,  -- 실시간으로 계산 필요
    0.0 as unrealized_pnl,  -- 실시간으로 계산 필요
    realized_pnl,
    'USD' as currency,
    NULL as exchange,
    TRUE as is_active,
    last_update as created_at,
    last_update as updated_at
FROM latest_positions;

-- 계좌 요약 VIEW (accounts 테이블 대체)
CREATE OR REPLACE VIEW accounts AS
WITH account_summary AS (
    SELECT 
        acctNumber as account_id,
        SUM(shares * price * CASE WHEN side = 'BOT' THEN 1 ELSE -1 END) as gross_position_value,
        SUM(realizedPNL) as total_realized_pnl,
        SUM(commission) as total_commission,
        MAX(time) as last_update
    FROM trade_events
    GROUP BY acctNumber
)
SELECT 
    1 as id,  -- 단일 계좌 가정
    COALESCE(account_id, 'DEFAULT') as account_id,
    100000.0 as net_liquidation,  -- 초기값, 실시간 업데이트 필요
    50000.0 as total_cash_value,  -- 초기값, 실시간 업데이트 필요
    50000.0 as settled_cash,
    0.0 as accrued_cash,
    200000.0 as buying_power,  -- 초기값, 실시간 업데이트 필요
    100000.0 as equity_with_loan_value,
    100000.0 as previous_day_equity_with_loan_value,
    COALESCE(gross_position_value, 0.0) as gross_position_value,
    100000.0 as reg_t_equity,
    50000.0 as reg_t_margin,
    100000.0 as sma,
    'USD' as currency,
    COALESCE(last_update, CURRENT_TIMESTAMP) as created_at,
    COALESCE(last_update, CURRENT_TIMESTAMP) as updated_at
FROM account_summary
LIMIT 1;

-- =====================================================
-- 또는 실제 테이블로 생성 (선택사항)
-- =====================================================

-- 만약 VIEW가 아닌 실제 테이블이 필요한 경우:
/*
-- Trades 테이블 (대시보드 호환)
CREATE TABLE IF NOT EXISTS trades_compat (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE,
    symbol VARCHAR(16) NOT NULL,
    action VARCHAR(10) NOT NULL,
    quantity FLOAT NOT NULL,
    price FLOAT NOT NULL,
    commission FLOAT DEFAULT 0.0,
    realized_pnl FLOAT DEFAULT 0.0,
    status VARCHAR(20) NOT NULL,
    exchange VARCHAR(16),
    currency VARCHAR(8) DEFAULT 'USD',
    execution_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Positions 테이블 (대시보드 호환)
CREATE TABLE IF NOT EXISTS positions_compat (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(16) UNIQUE NOT NULL,
    quantity FLOAT NOT NULL,
    avg_cost FLOAT NOT NULL,
    market_price FLOAT DEFAULT 0.0,
    market_value FLOAT DEFAULT 0.0,
    unrealized_pnl FLOAT DEFAULT 0.0,
    realized_pnl FLOAT DEFAULT 0.0,
    currency VARCHAR(8) DEFAULT 'USD',
    exchange VARCHAR(16),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts 테이블 (대시보드 호환)
CREATE TABLE IF NOT EXISTS accounts_compat (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(20) UNIQUE NOT NULL,
    net_liquidation FLOAT DEFAULT 0.0,
    total_cash_value FLOAT DEFAULT 0.0,
    settled_cash FLOAT DEFAULT 0.0,
    accrued_cash FLOAT DEFAULT 0.0,
    buying_power FLOAT DEFAULT 0.0,
    equity_with_loan_value FLOAT DEFAULT 0.0,
    previous_day_equity_with_loan_value FLOAT DEFAULT 0.0,
    gross_position_value FLOAT DEFAULT 0.0,
    reg_t_equity FLOAT DEFAULT 0.0,
    reg_t_margin FLOAT DEFAULT 0.0,
    sma FLOAT DEFAULT 0.0,
    currency VARCHAR(8) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
*/