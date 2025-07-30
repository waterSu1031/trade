-- =====================================================
-- Create Partition Tables
-- Description: 파티션 테이블 생성
-- =====================================================

-- 미국 시계열 파티션
CREATE TABLE IF NOT EXISTS price_time_us_es PARTITION OF price_time_us FOR VALUES IN ('ES');
CREATE TABLE IF NOT EXISTS price_time_us_nq PARTITION OF price_time_us FOR VALUES IN ('NQ');
CREATE TABLE IF NOT EXISTS price_time_us_ym PARTITION OF price_time_us FOR VALUES IN ('YM');
CREATE TABLE IF NOT EXISTS price_time_us_rty PARTITION OF price_time_us FOR VALUES IN ('RTY');
CREATE TABLE IF NOT EXISTS price_time_us_cl PARTITION OF price_time_us FOR VALUES IN ('CL');
CREATE TABLE IF NOT EXISTS price_time_us_gc PARTITION OF price_time_us FOR VALUES IN ('GC');
CREATE TABLE IF NOT EXISTS price_time_us_si PARTITION OF price_time_us FOR VALUES IN ('SI');

-- 중국 시계열 파티션
CREATE TABLE IF NOT EXISTS price_time_cn_a50 PARTITION OF price_time_cn FOR VALUES IN ('A50');
CREATE TABLE IF NOT EXISTS price_time_cn_hsi PARTITION OF price_time_cn FOR VALUES IN ('HSI');

-- 유럽 시계열 파티션 (필요시 추가)
-- CREATE TABLE IF NOT EXISTS price_time_eu_dax PARTITION OF price_time_eu FOR VALUES IN ('DAX');