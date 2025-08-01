-- =====================================================
-- 테이블명 변경 스크립트
-- =====================================================

\c trade_db

-- 1. exc_x_sym 테이블을 exc_x_con으로 변경
ALTER TABLE IF EXISTS exc_x_sym RENAME TO exc_x_con;

-- 2. sym_x_data 테이블을 con_x_data로 변경  
ALTER TABLE IF EXISTS sym_x_data RENAME TO con_x_data;

-- 3. con_x_data 테이블의 symbol 컬럼을 contract로 변경
ALTER TABLE IF EXISTS con_x_data RENAME COLUMN symbol TO contract;

-- 4. 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO freeksj;

\echo 'Table renaming completed:'
\echo '- exc_x_sym → exc_x_con'
\echo '- sym_x_data → con_x_data'
\echo '- con_x_data.symbol → con_x_data.contract'