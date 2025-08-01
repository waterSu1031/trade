-- =====================================================
-- Exchange 테이블 구조 비교 테스트
-- =====================================================

-- 현재 exchanges 테이블 구조 확인
\c trade_db

-- 1. 현재 exchanges 테이블 정보
\echo '=== 현재 exchanges 테이블 구조 ==='
\d exchanges

-- 2. 요구되는 exchange 테이블과의 차이점 분석
\echo '\n=== 필드별 비교 분석 ==='

-- 현재 테이블의 컬럼 목록
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'exchanges'
ORDER BY ordinal_position;

-- 3. 누락된 필드 확인
\echo '\n=== 누락된 필드 ==='
WITH required_fields AS (
    SELECT unnest(ARRAY[
        'exchange', 'country', 'sec_type', 'aws_coverage', 
        'timezone', 'location_lat', 'location_lon', 
        'description', 'symbol_cnt'
    ]) AS field_name
),
existing_fields AS (
    SELECT column_name AS field_name
    FROM information_schema.columns
    WHERE table_name = 'exchanges'
)
SELECT r.field_name AS missing_field
FROM required_fields r
LEFT JOIN existing_fields e ON r.field_name = e.field_name
WHERE e.field_name IS NULL;

-- 4. 데이터 타입 차이
\echo '\n=== 데이터 타입 비교 ==='
WITH field_comparison AS (
    SELECT 
        column_name,
        data_type AS current_type,
        character_maximum_length AS current_length,
        CASE column_name
            WHEN 'exchange' THEN 'VARCHAR(32)'
            WHEN 'country' THEN 'VARCHAR(16)'
            WHEN 'sec_type' THEN 'VARCHAR(8)'
            WHEN 'aws_coverage' THEN 'VARCHAR(12)'
            WHEN 'timezone' THEN 'VARCHAR(24)'
            WHEN 'location_lat' THEN 'REAL'
            WHEN 'location_lon' THEN 'REAL'
            WHEN 'description' THEN 'VARCHAR(100)'
            WHEN 'symbol_cnt' THEN 'INTEGER'
            ELSE 'N/A'
        END AS required_type
    FROM information_schema.columns
    WHERE table_name = 'exchanges'
)
SELECT 
    column_name,
    current_type || COALESCE('(' || current_length::text || ')', '') AS current_definition,
    required_type,
    CASE 
        WHEN column_name = 'exchange' AND current_length != 32 THEN '길이 불일치'
        WHEN column_name = 'timezone' AND current_length != 24 THEN '길이 불일치'
        WHEN column_name = 'description' AND current_type = 'text' THEN '타입 차이 (TEXT vs VARCHAR)'
        ELSE 'OK'
    END AS status
FROM field_comparison
WHERE required_type != 'N/A';

-- 5. 테이블 변경 제안
\echo '\n=== 테이블 변경 SQL (필요한 경우) ==='
\echo 'ALTER TABLE exchanges ADD COLUMN IF NOT EXISTS country VARCHAR(16);'
\echo 'ALTER TABLE exchanges ADD COLUMN IF NOT EXISTS sec_type VARCHAR(8);'
\echo 'ALTER TABLE exchanges ADD COLUMN IF NOT EXISTS aws_coverage VARCHAR(12);'
\echo 'ALTER TABLE exchanges ADD COLUMN IF NOT EXISTS location_lat REAL;'
\echo 'ALTER TABLE exchanges ADD COLUMN IF NOT EXISTS location_lon REAL;'
\echo 'ALTER TABLE exchanges ADD COLUMN IF NOT EXISTS symbol_cnt INTEGER;'
\echo ''
\echo '-- 데이터 타입 변경 (필요시)'
\echo 'ALTER TABLE exchanges ALTER COLUMN exchange TYPE VARCHAR(32);'
\echo 'ALTER TABLE exchanges ALTER COLUMN timezone TYPE VARCHAR(24);'
\echo 'ALTER TABLE exchanges ALTER COLUMN description TYPE VARCHAR(100);'