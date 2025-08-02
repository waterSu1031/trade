-- 데이터 정합성 검증 로그 테이블
CREATE TABLE IF NOT EXISTS data_integrity_log (
    id SERIAL PRIMARY KEY,
    check_type VARCHAR(50) NOT NULL,  -- POSITION, PNL, DUPLICATE, INTEGRITY
    symbol VARCHAR(20),
    exec_id VARCHAR(50),
    issue_type VARCHAR(100) NOT NULL,  -- position_mismatch, pnl_mismatch, duplicate_found, etc.
    old_value TEXT,
    new_value TEXT,
    details JSONB,
    checked_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_integrity_log_check_type ON data_integrity_log(check_type);
CREATE INDEX idx_integrity_log_symbol ON data_integrity_log(symbol);
CREATE INDEX idx_integrity_log_checked_at ON data_integrity_log(checked_at);

-- 포지션 테이블 (없는 경우 생성)
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    position DECIMAL(15,4) NOT NULL DEFAULT 0,
    avg_price DECIMAL(15,4) NOT NULL DEFAULT 0,
    realized_pnl DECIMAL(15,4) NOT NULL DEFAULT 0,
    unrealized_pnl DECIMAL(15,4) NOT NULL DEFAULT 0,
    market_value DECIMAL(15,4) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 포지션 업데이트 트리거
CREATE OR REPLACE FUNCTION update_position_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_positions_timestamp
BEFORE UPDATE ON positions
FOR EACH ROW
EXECUTE FUNCTION update_position_timestamp();