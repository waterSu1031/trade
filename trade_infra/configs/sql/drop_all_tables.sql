-- =====================================================
-- 모든 기존 테이블 삭제
-- =====================================================

-- trade_db 연결
\c trade_db

-- 기존 테이블 삭제
DROP TABLE IF EXISTS trade_events CASCADE;
DROP TABLE IF EXISTS positions_history CASCADE;
DROP TABLE IF EXISTS accounts_history CASCADE;
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS positions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS order_status_history CASCADE;
DROP TABLE IF EXISTS daily_statistics CASCADE;
DROP TABLE IF EXISTS contracts CASCADE;
DROP TABLE IF EXISTS contract_details CASCADE;
DROP TABLE IF EXISTS exchanges CASCADE;
DROP TABLE IF EXISTS exchange_symbols CASCADE;
DROP TABLE IF EXISTS exc_x_sym CASCADE;
DROP TABLE IF EXISTS sym_x_data CASCADE;
DROP TABLE IF EXISTS price_time CASCADE;
DROP TABLE IF EXISTS price_range CASCADE;
DROP TABLE IF EXISTS price_volume CASCADE;

-- 파티션 테이블들 삭제
DROP TABLE IF EXISTS price_range_es CASCADE;
DROP TABLE IF EXISTS price_range_nq CASCADE;
DROP TABLE IF EXISTS price_range_ym CASCADE;
DROP TABLE IF EXISTS price_range_rty CASCADE;
DROP TABLE IF EXISTS price_range_cl CASCADE;
DROP TABLE IF EXISTS price_range_gc CASCADE;
DROP TABLE IF EXISTS price_range_si CASCADE;
DROP TABLE IF EXISTS price_range_default CASCADE;

DROP TABLE IF EXISTS price_volume_es CASCADE;
DROP TABLE IF EXISTS price_volume_nq CASCADE;
DROP TABLE IF EXISTS price_volume_ym CASCADE;
DROP TABLE IF EXISTS price_volume_rty CASCADE;
DROP TABLE IF EXISTS price_volume_cl CASCADE;
DROP TABLE IF EXISTS price_volume_gc CASCADE;
DROP TABLE IF EXISTS price_volume_si CASCADE;
DROP TABLE IF EXISTS price_volume_default CASCADE;

-- VIEW 삭제
DROP VIEW IF EXISTS trades_latest CASCADE;
DROP VIEW IF EXISTS positions_current CASCADE;
DROP VIEW IF EXISTS accounts_current CASCADE;
DROP VIEW IF EXISTS positions_latest CASCADE;
DROP VIEW IF EXISTS accounts_latest CASCADE;
DROP VIEW IF EXISTS current_positions CASCADE;

-- data_db가 있다면 삭제 (현재는 trade_db로 통합)
\c postgres
DROP DATABASE IF EXISTS data_db;

-- trade_db로 다시 연결
\c trade_db

-- TimescaleDB extension 확인 (이미 있으면 스킵)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;