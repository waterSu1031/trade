-- =====================================================
-- 누락된 테이블 생성 (코드 호환성을 위한 기존 구조)
-- Version: 1.0
-- Description: 대시보드와 기존 코드에서 기대하는 테이블 구조
-- =====================================================

-- trade_db 연결
\c trade_db

-- =====================================================
-- 1. 거래 테이블 (Trades)
-- =====================================================
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(16) NOT NULL,
    side VARCHAR(10) NOT NULL,      -- BUY, SELL
    price DECIMAL(15,8) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    commission DECIMAL(10,4),
    realized_pnl DECIMAL(15,2),
    timestamp TIMESTAMPTZ NOT NULL,
    order_id VARCHAR(50),
    execution_id VARCHAR(50),
    account_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_account ON trades(account_id);

-- =====================================================
-- 2. 포지션 테이블 (Positions)
-- =====================================================
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(16) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    avg_price DECIMAL(15,8) NOT NULL,
    current_price DECIMAL(15,8),
    unrealized_pnl DECIMAL(15,2),
    realized_pnl DECIMAL(15,2),
    account_id VARCHAR(50),
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, account_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_id);

-- =====================================================
-- 3. 계좌 테이블 (Accounts)
-- =====================================================
CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    account_type VARCHAR(20),        -- PAPER, LIVE
    currency VARCHAR(8) DEFAULT 'USD',
    balance DECIMAL(15,2),
    equity DECIMAL(15,2),
    margin_used DECIMAL(15,2),
    margin_available DECIMAL(15,2),
    buying_power DECIMAL(15,2),
    daily_pnl DECIMAL(15,2),
    total_pnl DECIMAL(15,2),
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 4. 동기화 메타데이터 테이블
-- =====================================================
CREATE TABLE IF NOT EXISTS sync_metadata (
    table_name VARCHAR(50) PRIMARY KEY,
    last_sync TIMESTAMP,
    record_count INTEGER,
    sync_status VARCHAR(20),         -- SUCCESS, FAILED, IN_PROGRESS
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 초기 데이터 삽입
INSERT INTO sync_metadata (table_name, last_sync, record_count, sync_status) VALUES 
    ('contracts', '1970-01-01'::timestamp, 0, 'PENDING'),
    ('exchanges', '1970-01-01'::timestamp, 0, 'PENDING'),
    ('trade_events', '1970-01-01'::timestamp, 0, 'PENDING'),
    ('daily_statistics', '1970-01-01'::timestamp, 0, 'PENDING')
ON CONFLICT (table_name) DO NOTHING;

-- =====================================================
-- 5. 대시보드용 세션 테이블
-- =====================================================
CREATE TABLE IF NOT EXISTS trading_sessions (
    id SERIAL PRIMARY KEY,
    session_date DATE NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    status VARCHAR(20),              -- ACTIVE, COMPLETED, FAILED
    total_trades INTEGER DEFAULT 0,
    total_volume DECIMAL(15,2) DEFAULT 0,
    gross_pnl DECIMAL(15,2) DEFAULT 0,
    net_pnl DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_date)
);

-- =====================================================
-- 6. 트리거 함수: trade_events -> trades 동기화
-- =====================================================
CREATE OR REPLACE FUNCTION sync_trade_events_to_trades()
RETURNS TRIGGER AS $$
BEGIN
    -- trade_events에서 trades 테이블로 데이터 복사
    INSERT INTO trades (
        symbol, side, price, quantity, commission, 
        realized_pnl, timestamp, order_id, execution_id
    ) VALUES (
        NEW.symbol, 
        NEW.side, 
        NEW.price, 
        NEW.shares,
        NEW.commission,
        NEW.realizedPNL,
        NEW.time,
        NEW.orderId,
        NEW.execId
    );
    
    -- positions 테이블 업데이트
    INSERT INTO positions (symbol, quantity, avg_price, current_price, unrealized_pnl)
    VALUES (NEW.symbol, NEW.position, NEW.avgCost, NEW.lastPrice, NEW.unrealizedPNL)
    ON CONFLICT (symbol, account_id) 
    DO UPDATE SET
        quantity = NEW.position,
        avg_price = NEW.avgCost,
        current_price = NEW.lastPrice,
        unrealized_pnl = NEW.unrealizedPNL,
        last_updated = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성 (trade_events 테이블이 있는 경우에만)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'trade_events') THEN
        DROP TRIGGER IF EXISTS sync_trades_trigger ON trade_events;
        CREATE TRIGGER sync_trades_trigger
        AFTER INSERT ON trade_events
        FOR EACH ROW
        EXECUTE FUNCTION sync_trade_events_to_trades();
    END IF;
END $$;

-- =====================================================
-- 7. 통계 업데이트 함수
-- =====================================================
CREATE OR REPLACE FUNCTION update_trading_session_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE trading_sessions
    SET 
        total_trades = total_trades + 1,
        total_volume = total_volume + NEW.quantity,
        gross_pnl = gross_pnl + COALESCE(NEW.realized_pnl, 0)
    WHERE session_date = DATE(NEW.timestamp)
      AND status = 'ACTIVE';
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- trades 테이블에 트리거 생성
DROP TRIGGER IF EXISTS update_session_stats_trigger ON trades;
CREATE TRIGGER update_session_stats_trigger
AFTER INSERT ON trades
FOR EACH ROW
EXECUTE FUNCTION update_trading_session_stats();

-- =====================================================
-- 8. 계좌 정보 초기화 (테스트용)
-- =====================================================
INSERT INTO accounts (account_id, account_type, balance, equity, buying_power) VALUES
    ('DU1234567', 'PAPER', 100000.00, 100000.00, 400000.00),
    ('U1234567', 'LIVE', 50000.00, 50000.00, 200000.00)
ON CONFLICT (account_id) DO NOTHING;

-- 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO freeksj;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO freeksj;
EOF < /dev/null
