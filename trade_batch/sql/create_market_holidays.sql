-- 시장 휴일 테이블
CREATE TABLE IF NOT EXISTS market_holidays (
    id SERIAL PRIMARY KEY,
    market VARCHAR(10) NOT NULL,  -- US, KR, JP, HK, EU, UK
    holiday_date DATE NOT NULL,
    holiday_name VARCHAR(100),
    is_fixed BOOLEAN DEFAULT false,  -- 고정 휴일 여부
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 복합 유니크 키 (시장별 날짜는 유일)
    UNIQUE(market, holiday_date)
);

-- 인덱스 생성
CREATE INDEX idx_market_holidays_market ON market_holidays(market);
CREATE INDEX idx_market_holidays_date ON market_holidays(holiday_date);
CREATE INDEX idx_market_holidays_year ON market_holidays(EXTRACT(YEAR FROM holiday_date));

-- 업데이트 시간 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_market_holidays_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_market_holidays_timestamp
BEFORE UPDATE ON market_holidays
FOR EACH ROW
EXECUTE FUNCTION update_market_holidays_timestamp();

-- 2024년 주요 휴일 샘플 데이터
INSERT INTO market_holidays (market, holiday_date, holiday_name, is_fixed) VALUES
-- US
('US', '2024-01-01', 'New Year''s Day', true),
('US', '2024-01-15', 'Martin Luther King Jr. Day', false),
('US', '2024-02-19', 'Presidents Day', false),
('US', '2024-03-29', 'Good Friday', false),
('US', '2024-05-27', 'Memorial Day', false),
('US', '2024-07-04', 'Independence Day', true),
('US', '2024-09-02', 'Labor Day', false),
('US', '2024-11-28', 'Thanksgiving Day', false),
('US', '2024-12-25', 'Christmas Day', true),

-- KR
('KR', '2024-01-01', '신정', true),
('KR', '2024-02-09', '설날 연휴', false),
('KR', '2024-02-10', '설날', false),
('KR', '2024-02-11', '설날 연휴', false),
('KR', '2024-02-12', '대체공휴일', false),
('KR', '2024-03-01', '삼일절', true),
('KR', '2024-04-10', '국회의원 선거일', false),
('KR', '2024-05-05', '어린이날', true),
('KR', '2024-05-06', '대체공휴일', false),
('KR', '2024-05-15', '부처님오신날', false),
('KR', '2024-06-06', '현충일', true),
('KR', '2024-08-15', '광복절', true),
('KR', '2024-09-16', '추석 연휴', false),
('KR', '2024-09-17', '추석', false),
('KR', '2024-09-18', '추석 연휴', false),
('KR', '2024-10-03', '개천절', true),
('KR', '2024-10-09', '한글날', true),
('KR', '2024-12-25', '크리스마스', true)
ON CONFLICT (market, holiday_date) DO NOTHING;