-- =====================================================
-- Trade System PostgreSQL Unified Schema
-- Version: 2.0
-- Description: 통일된 명명 규칙을 적용한 통합 스키마
-- =====================================================

-- 기존 테이블 삭제 (필요시 주석 해제)
-- DROP TABLE IF EXISTS trade_events CASCADE;
-- DROP TABLE IF EXISTS daily_statistics CASCADE;
-- DROP TABLE IF EXISTS performance_metrics CASCADE;
-- DROP VIEW IF EXISTS v_daily_performance CASCADE;
-- DROP VIEW IF EXISTS v_performance_by_type CASCADE;

-- =====================================================
-- 1. 종목/계약 관련 테이블
-- =====================================================

-- 종목 기본 정보
CREATE TABLE IF NOT EXISTS contracts (
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
    agg_group INTEGER,
    market_rule_ids VARCHAR(64)
);

-- 주식 상세 정보
CREATE TABLE IF NOT EXISTS contract_details_stock (
    con_id INTEGER PRIMARY KEY REFERENCES contracts(con_id),
    industry VARCHAR(64),
    category VARCHAR(64),
    subcategory VARCHAR(64),
    stock_type VARCHAR(16)
);

-- 선물 상세 정보
CREATE TABLE IF NOT EXISTS contract_details_future (
    con_id INTEGER PRIMARY KEY REFERENCES contracts(con_id),
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
CREATE TABLE IF NOT EXISTS contract_details_option (
    con_id INTEGER PRIMARY KEY REFERENCES contracts(con_id),
    contract_month VARCHAR(8),
    real_expiration_date VARCHAR(16),
    last_trade_time VARCHAR(32),
    ev_rule VARCHAR(32),
    ev_multiplier DOUBLE PRECISION,
    under_conid INTEGER,
    under_symbol VARCHAR(32),
    under_sec_type VARCHAR(16)
);

-- CSV 임포트용 심볼 정보
CREATE TABLE IF NOT EXISTS symbol_imports (
    symbol VARCHAR(16) NOT NULL,
    exchange VARCHAR(16) NOT NULL,
    currency VARCHAR(8) NOT NULL,
    sec_type VARCHAR(8) NOT NULL,
    PRIMARY KEY (symbol, exchange)
);

-- 거래소-종목 매핑
CREATE TABLE IF NOT EXISTS exchange_symbols (
    exchange VARCHAR(16) NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    PRIMARY KEY (exchange, symbol)
);

-- 거래소 정보
CREATE TABLE IF NOT EXISTS exchanges (
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

-- 종목 메타데이터
CREATE TABLE IF NOT EXISTS symbol_metadata (
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

-- =====================================================
-- 2. 시장 데이터 테이블 (지역별)
-- =====================================================

-- 미국 시계열 데이터
CREATE TABLE IF NOT EXISTS price_time_us (
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
CREATE TABLE IF NOT EXISTS price_time_cn (
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
CREATE TABLE IF NOT EXISTS price_time_eu (
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

-- =====================================================
-- 3. 거래/분석 테이블
-- =====================================================

-- 거래 이벤트 (스냅샷 포함)
CREATE TABLE IF NOT EXISTS trade_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE,
    
    -- 거래 정보
    symbol VARCHAR(20) NOT NULL,
    sec_type VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    commission DECIMAL(10,4),
    executed_at TIMESTAMP NOT NULL,
    
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
    
    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 일일 통계 (자산 유형별)
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
    
    -- 포지션 통계
    positions_count INTEGER,
    total_position_value DECIMAL(15,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, sec_type)
);

-- 성과 지표
CREATE TABLE IF NOT EXISTS performance_metrics (
    date DATE,
    sec_type VARCHAR(10),
    
    -- 수익률
    daily_return DECIMAL(10,4),
    cumulative_return DECIMAL(10,4),
    
    -- 리스크 지표
    volatility DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    
    -- 거래 효율성
    avg_win DECIMAL(15,2),
    avg_loss DECIMAL(15,2),
    avg_holding_period INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, sec_type)
);

-- =====================================================
-- 4. 뷰 (통합 조회용)
-- =====================================================

-- 일일 성과 통합 뷰
CREATE OR REPLACE VIEW v_daily_performance AS
SELECT 
    d.date,
    COALESCE(d.sec_type, 'ALL') as sec_type,
    SUM(d.total_trades) as total_trades,
    SUM(d.gross_pnl) as gross_pnl,
    SUM(d.net_pnl) as net_pnl,
    SUM(d.commission) as commission,
    CASE 
        WHEN SUM(d.win_trades + d.loss_trades) > 0 
        THEN SUM(d.win_trades)::FLOAT / SUM(d.win_trades + d.loss_trades) * 100
        ELSE 0 
    END as win_rate,
    SUM(d.win_trades) as total_wins,
    SUM(d.loss_trades) as total_losses
FROM daily_statistics d
GROUP BY ROLLUP(d.date, d.sec_type)
ORDER BY d.date DESC, d.sec_type;

-- 자산 유형별 성과 분석 뷰
CREATE OR REPLACE VIEW v_performance_by_type AS
SELECT 
    sec_type,
    COUNT(*) as total_trades,
    SUM(realized_pnl) as total_pnl,
    AVG(realized_pnl) as avg_pnl_per_trade,
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 as win_rate,
    SUM(commission) as total_commission,
    MAX(executed_at) as last_trade_time,
    MIN(executed_at) as first_trade_time
FROM trade_events
GROUP BY sec_type
ORDER BY total_pnl DESC;

-- =====================================================
-- 5. 인덱스
-- =====================================================

-- 거래 이벤트 인덱스
CREATE INDEX IF NOT EXISTS idx_trade_events_symbol_time ON trade_events(symbol, executed_at);
CREATE INDEX IF NOT EXISTS idx_trade_events_sec_type ON trade_events(sec_type);
CREATE INDEX IF NOT EXISTS idx_trade_events_date ON trade_events(DATE(executed_at));
CREATE INDEX IF NOT EXISTS idx_trade_events_symbol_date ON trade_events(symbol, DATE(executed_at));

-- 일일 통계 인덱스
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_statistics(date DESC);

-- 성과 지표 인덱스
CREATE INDEX IF NOT EXISTS idx_perf_metrics_date ON performance_metrics(date DESC);

-- =====================================================
-- 6. 권한 설정
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO freeksj;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO freeksj;