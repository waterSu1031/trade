-- =====================================================
-- 테이블명 복원 (다시 복수형으로)
-- =====================================================

\c trade_db

-- 1. contract_detail 테이블명을 다시 contract_details로 변경
ALTER TABLE IF EXISTS contract_detail RENAME TO contract_details;

-- 2. exchange 테이블은 그대로 유지 (변경 없음)

-- 3. 증권 타입별 detail 테이블들도 복수형으로 변경
ALTER TABLE IF EXISTS contract_detail_stock RENAME TO contract_details_stock;
ALTER TABLE IF EXISTS contract_detail_future RENAME TO contract_details_future;
ALTER TABLE IF EXISTS contract_detail_option RENAME TO contract_details_option;
ALTER TABLE IF EXISTS contract_detail_index RENAME TO contract_details_index;

-- 4. 백업 테이블 삭제 (exchanges_backup이 있다면)
DROP TABLE IF EXISTS exchanges_backup;

\echo 'Table names reverted to plural form:'
\echo '- contract_detail → contract_details'
\echo '- contract_detail_stock → contract_details_stock'
\echo '- contract_detail_future → contract_details_future'
\echo '- contract_detail_option → contract_details_option'
\echo '- contract_detail_index → contract_details_index'
\echo '- exchange table remains unchanged'