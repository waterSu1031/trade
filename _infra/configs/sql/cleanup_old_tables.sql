-- =====================================================
-- Cleanup Old Tables
-- Description: 기존 테이블 정리 스크립트
-- =====================================================

-- 뷰 삭제
DROP VIEW IF EXISTS price_time CASCADE;
DROP VIEW IF EXISTS price_range CASCADE;
DROP VIEW IF EXISTS price_volume CASCADE;

-- 기존 명명 규칙 테이블 삭제
DROP TABLE IF EXISTS contract CASCADE;
DROP TABLE IF EXISTS contract_detail CASCADE;
DROP TABLE IF EXISTS contract_detail_stock CASCADE;
DROP TABLE IF EXISTS contract_detail_future CASCADE;
DROP TABLE IF EXISTS contract_detail_option CASCADE;
DROP TABLE IF EXISTS exchange CASCADE;
DROP TABLE IF EXISTS sym_x_data CASCADE;
DROP TABLE IF EXISTS symbol_from_csv CASCADE;
DROP TABLE IF EXISTS exc_x_sym CASCADE;

-- 가격 테이블 삭제 (파티션 포함)
DROP TABLE IF EXISTS price_us_time CASCADE;
DROP TABLE IF EXISTS price_cn_time CASCADE;
DROP TABLE IF EXISTS price_eu_time CASCADE;
DROP TABLE IF EXISTS price_us_range CASCADE;
DROP TABLE IF EXISTS price_cn_range CASCADE;
DROP TABLE IF EXISTS price_eu_range CASCADE;
DROP TABLE IF EXISTS price_us_volume CASCADE;
DROP TABLE IF EXISTS price_cn_volume CASCADE;
DROP TABLE IF EXISTS price_eu_volume CASCADE;