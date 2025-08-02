-- 기존 테이블 삭제
DROP TABLE IF EXISTS trading_hour_daily CASCADE;
DROP TABLE IF EXISTS trading_hour CASCADE;

-- 통합된 거래시간 테이블
CREATE TABLE IF NOT EXISTS trading_hours (
    exchange VARCHAR(16) NOT NULL,
    type VARCHAR(10) NOT NULL DEFAULT '',    -- 'FIX' 또는 '' (빈값)
    session VARCHAR(20) NOT NULL DEFAULT 'REGULAR',
    trade_date DATE NOT NULL,
    day_of_week VARCHAR(3),                 -- MON, TUE, WED, THU, FRI, SAT, SUN
    start_time_utc TIMESTAMP,
    end_time_utc TIMESTAMP,
    start_time_loc TIMESTAMP,
    end_time_loc TIMESTAMP,
    timezone VARCHAR(50) NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (exchange, type, session, trade_date)
);

-- 인덱스
CREATE INDEX idx_trading_hours_date ON trading_hours(trade_date);
CREATE INDEX idx_trading_hours_exchange_date ON trading_hours(exchange, trade_date);
CREATE INDEX idx_trading_hours_holiday ON trading_hours(is_holiday);

-- 거래소별 FIX 거래시간 초기 데이터
-- FIX 데이터는 참조용 날짜로 2025-01-01 사용, 실제로는 요일별 반복
-- UTC 시간은 자동 계산될 예정

-- CME: 연속 거래 (일요일 17:00 ~ 금요일 16:00)
INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week, timezone, start_time_loc, end_time_loc, start_time_utc, end_time_utc) VALUES
-- 일요일 17:00 ~ 월요일 16:00 (Chicago -> UTC: +6시간)
('CME', 'FIX', 'REGULAR', '2025-01-01', 'SUN', 'America/Chicago', '2025-01-05 17:00:00', '2025-01-06 16:00:00', '2025-01-05 23:00:00', '2025-01-06 22:00:00'),
-- 월요일 17:00 ~ 화요일 16:00
('CME', 'FIX', 'REGULAR', '2025-01-01', 'MON', 'America/Chicago', '2025-01-06 17:00:00', '2025-01-07 16:00:00', '2025-01-06 23:00:00', '2025-01-07 22:00:00'),
-- 화요일 17:00 ~ 수요일 16:00
('CME', 'FIX', 'REGULAR', '2025-01-01', 'TUE', 'America/Chicago', '2025-01-07 17:00:00', '2025-01-08 16:00:00', '2025-01-07 23:00:00', '2025-01-08 22:00:00'),
-- 수요일 17:00 ~ 목요일 16:00
('CME', 'FIX', 'REGULAR', '2025-01-01', 'WED', 'America/Chicago', '2025-01-08 17:00:00', '2025-01-09 16:00:00', '2025-01-08 23:00:00', '2025-01-09 22:00:00'),
-- 목요일 17:00 ~ 금요일 16:00
('CME', 'FIX', 'REGULAR', '2025-01-01', 'THU', 'America/Chicago', '2025-01-09 17:00:00', '2025-01-10 16:00:00', '2025-01-09 23:00:00', '2025-01-10 22:00:00');

-- HKFE: 오전/오후 세션 구분 (Hong Kong -> UTC: -8시간)
INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week, timezone, start_time_loc, end_time_loc, start_time_utc, end_time_utc) VALUES
('HKFE', 'FIX', 'MORNING', '2025-01-01', 'MON', 'Asia/Hong_Kong', '2025-01-06 09:15:00', '2025-01-06 12:00:00', '2025-01-06 01:15:00', '2025-01-06 04:00:00'),
('HKFE', 'FIX', 'AFTERNOON', '2025-01-01', 'MON', 'Asia/Hong_Kong', '2025-01-06 13:00:00', '2025-01-06 16:00:00', '2025-01-06 05:00:00', '2025-01-06 08:00:00'),
('HKFE', 'FIX', 'MORNING', '2025-01-01', 'TUE', 'Asia/Hong_Kong', '2025-01-07 09:15:00', '2025-01-07 12:00:00', '2025-01-07 01:15:00', '2025-01-07 04:00:00'),
('HKFE', 'FIX', 'AFTERNOON', '2025-01-01', 'TUE', 'Asia/Hong_Kong', '2025-01-07 13:00:00', '2025-01-07 16:00:00', '2025-01-07 05:00:00', '2025-01-07 08:00:00'),
('HKFE', 'FIX', 'MORNING', '2025-01-01', 'WED', 'Asia/Hong_Kong', '2025-01-08 09:15:00', '2025-01-08 12:00:00', '2025-01-08 01:15:00', '2025-01-08 04:00:00'),
('HKFE', 'FIX', 'AFTERNOON', '2025-01-01', 'WED', 'Asia/Hong_Kong', '2025-01-08 13:00:00', '2025-01-08 16:00:00', '2025-01-08 05:00:00', '2025-01-08 08:00:00'),
('HKFE', 'FIX', 'MORNING', '2025-01-01', 'THU', 'Asia/Hong_Kong', '2025-01-09 09:15:00', '2025-01-09 12:00:00', '2025-01-09 01:15:00', '2025-01-09 04:00:00'),
('HKFE', 'FIX', 'AFTERNOON', '2025-01-01', 'THU', 'Asia/Hong_Kong', '2025-01-09 13:00:00', '2025-01-09 16:00:00', '2025-01-09 05:00:00', '2025-01-09 08:00:00'),
('HKFE', 'FIX', 'MORNING', '2025-01-01', 'FRI', 'Asia/Hong_Kong', '2025-01-10 09:15:00', '2025-01-10 12:00:00', '2025-01-10 01:15:00', '2025-01-10 04:00:00'),
('HKFE', 'FIX', 'AFTERNOON', '2025-01-01', 'FRI', 'Asia/Hong_Kong', '2025-01-10 13:00:00', '2025-01-10 16:00:00', '2025-01-10 05:00:00', '2025-01-10 08:00:00');

-- JPX: 오전/오후 세션 구분 (Tokyo -> UTC: -9시간)
INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week, timezone, start_time_loc, end_time_loc, start_time_utc, end_time_utc) VALUES
('JPX', 'FIX', 'MORNING', '2025-01-01', 'MON', 'Asia/Tokyo', '2025-01-06 09:00:00', '2025-01-06 11:30:00', '2025-01-06 00:00:00', '2025-01-06 02:30:00'),
('JPX', 'FIX', 'AFTERNOON', '2025-01-01', 'MON', 'Asia/Tokyo', '2025-01-06 12:30:00', '2025-01-06 15:00:00', '2025-01-06 03:30:00', '2025-01-06 06:00:00'),
('JPX', 'FIX', 'MORNING', '2025-01-01', 'TUE', 'Asia/Tokyo', '2025-01-07 09:00:00', '2025-01-07 11:30:00', '2025-01-07 00:00:00', '2025-01-07 02:30:00'),
('JPX', 'FIX', 'AFTERNOON', '2025-01-01', 'TUE', 'Asia/Tokyo', '2025-01-07 12:30:00', '2025-01-07 15:00:00', '2025-01-07 03:30:00', '2025-01-07 06:00:00'),
('JPX', 'FIX', 'MORNING', '2025-01-01', 'WED', 'Asia/Tokyo', '2025-01-08 09:00:00', '2025-01-08 11:30:00', '2025-01-08 00:00:00', '2025-01-08 02:30:00'),
('JPX', 'FIX', 'AFTERNOON', '2025-01-01', 'WED', 'Asia/Tokyo', '2025-01-08 12:30:00', '2025-01-08 15:00:00', '2025-01-08 03:30:00', '2025-01-08 06:00:00'),
('JPX', 'FIX', 'MORNING', '2025-01-01', 'THU', 'Asia/Tokyo', '2025-01-09 09:00:00', '2025-01-09 11:30:00', '2025-01-09 00:00:00', '2025-01-09 02:30:00'),
('JPX', 'FIX', 'AFTERNOON', '2025-01-01', 'THU', 'Asia/Tokyo', '2025-01-09 12:30:00', '2025-01-09 15:00:00', '2025-01-09 03:30:00', '2025-01-09 06:00:00'),
('JPX', 'FIX', 'MORNING', '2025-01-01', 'FRI', 'Asia/Tokyo', '2025-01-10 09:00:00', '2025-01-10 11:30:00', '2025-01-10 00:00:00', '2025-01-10 02:30:00'),
('JPX', 'FIX', 'AFTERNOON', '2025-01-01', 'FRI', 'Asia/Tokyo', '2025-01-10 12:30:00', '2025-01-10 15:00:00', '2025-01-10 03:30:00', '2025-01-10 06:00:00');

-- EUREX: 연속 거래 (Berlin -> UTC: -1시간)
INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week, timezone, start_time_loc, end_time_loc, start_time_utc, end_time_utc) VALUES
('EUREX', 'FIX', 'REGULAR', '2025-01-01', 'MON', 'Europe/Berlin', '2025-01-06 08:00:00', '2025-01-06 22:00:00', '2025-01-06 07:00:00', '2025-01-06 21:00:00'),
('EUREX', 'FIX', 'REGULAR', '2025-01-01', 'TUE', 'Europe/Berlin', '2025-01-07 08:00:00', '2025-01-07 22:00:00', '2025-01-07 07:00:00', '2025-01-07 21:00:00'),
('EUREX', 'FIX', 'REGULAR', '2025-01-01', 'WED', 'Europe/Berlin', '2025-01-08 08:00:00', '2025-01-08 22:00:00', '2025-01-08 07:00:00', '2025-01-08 21:00:00'),
('EUREX', 'FIX', 'REGULAR', '2025-01-01', 'THU', 'Europe/Berlin', '2025-01-09 08:00:00', '2025-01-09 22:00:00', '2025-01-09 07:00:00', '2025-01-09 21:00:00'),
('EUREX', 'FIX', 'REGULAR', '2025-01-01', 'FRI', 'Europe/Berlin', '2025-01-10 08:00:00', '2025-01-10 22:00:00', '2025-01-10 07:00:00', '2025-01-10 21:00:00');

-- KSE: 연속 거래 (Seoul -> UTC: -9시간)
INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week, timezone, start_time_loc, end_time_loc, start_time_utc, end_time_utc) VALUES
('KSE', 'FIX', 'REGULAR', '2025-01-01', 'MON', 'Asia/Seoul', '2025-01-06 09:00:00', '2025-01-06 15:30:00', '2025-01-06 00:00:00', '2025-01-06 06:30:00'),
('KSE', 'FIX', 'REGULAR', '2025-01-01', 'TUE', 'Asia/Seoul', '2025-01-07 09:00:00', '2025-01-07 15:30:00', '2025-01-07 00:00:00', '2025-01-07 06:30:00'),
('KSE', 'FIX', 'REGULAR', '2025-01-01', 'WED', 'Asia/Seoul', '2025-01-08 09:00:00', '2025-01-08 15:30:00', '2025-01-08 00:00:00', '2025-01-08 06:30:00'),
('KSE', 'FIX', 'REGULAR', '2025-01-01', 'THU', 'Asia/Seoul', '2025-01-09 09:00:00', '2025-01-09 15:30:00', '2025-01-09 00:00:00', '2025-01-09 06:30:00'),
('KSE', 'FIX', 'REGULAR', '2025-01-01', 'FRI', 'Asia/Seoul', '2025-01-10 09:00:00', '2025-01-10 15:30:00', '2025-01-10 00:00:00', '2025-01-10 06:30:00');

-- SGX: 오전/오후 세션 구분 (Singapore -> UTC: -8시간)
INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week, timezone, start_time_loc, end_time_loc, start_time_utc, end_time_utc) VALUES
('SGX', 'FIX', 'MORNING', '2025-01-01', 'MON', 'Asia/Singapore', '2025-01-06 08:30:00', '2025-01-06 12:00:00', '2025-01-06 00:30:00', '2025-01-06 04:00:00'),
('SGX', 'FIX', 'AFTERNOON', '2025-01-01', 'MON', 'Asia/Singapore', '2025-01-06 13:00:00', '2025-01-06 17:15:00', '2025-01-06 05:00:00', '2025-01-06 09:15:00'),
('SGX', 'FIX', 'MORNING', '2025-01-01', 'TUE', 'Asia/Singapore', '2025-01-07 08:30:00', '2025-01-07 12:00:00', '2025-01-07 00:30:00', '2025-01-07 04:00:00'),
('SGX', 'FIX', 'AFTERNOON', '2025-01-01', 'TUE', 'Asia/Singapore', '2025-01-07 13:00:00', '2025-01-07 17:15:00', '2025-01-07 05:00:00', '2025-01-07 09:15:00'),
('SGX', 'FIX', 'MORNING', '2025-01-01', 'WED', 'Asia/Singapore', '2025-01-08 08:30:00', '2025-01-08 12:00:00', '2025-01-08 00:30:00', '2025-01-08 04:00:00'),
('SGX', 'FIX', 'AFTERNOON', '2025-01-01', 'WED', 'Asia/Singapore', '2025-01-08 13:00:00', '2025-01-08 17:15:00', '2025-01-08 05:00:00', '2025-01-08 09:15:00'),
('SGX', 'FIX', 'MORNING', '2025-01-01', 'THU', 'Asia/Singapore', '2025-01-09 08:30:00', '2025-01-09 12:00:00', '2025-01-09 00:30:00', '2025-01-09 04:00:00'),
('SGX', 'FIX', 'AFTERNOON', '2025-01-01', 'THU', 'Asia/Singapore', '2025-01-09 13:00:00', '2025-01-09 17:15:00', '2025-01-09 05:00:00', '2025-01-09 09:15:00'),
('SGX', 'FIX', 'MORNING', '2025-01-01', 'FRI', 'Asia/Singapore', '2025-01-10 08:30:00', '2025-01-10 12:00:00', '2025-01-10 00:30:00', '2025-01-10 04:00:00'),
('SGX', 'FIX', 'AFTERNOON', '2025-01-01', 'FRI', 'Asia/Singapore', '2025-01-10 13:00:00', '2025-01-10 17:15:00', '2025-01-10 05:00:00', '2025-01-10 09:15:00');

-- 나머지 거래소들 (CBOT, NYMEX, COMEX, ICEEU, NSE, OSE)
INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week, timezone, start_time_loc, end_time_loc, start_time_utc, end_time_utc) VALUES
-- CBOT (Chicago -> UTC: +6시간)
('CBOT', 'FIX', 'REGULAR', '2025-01-01', 'SUN', 'America/Chicago', '2025-01-05 17:00:00', '2025-01-06 14:20:00', '2025-01-05 23:00:00', '2025-01-06 20:20:00'),
('CBOT', 'FIX', 'REGULAR', '2025-01-01', 'MON', 'America/Chicago', '2025-01-06 17:00:00', '2025-01-07 14:20:00', '2025-01-06 23:00:00', '2025-01-07 20:20:00'),
('CBOT', 'FIX', 'REGULAR', '2025-01-01', 'TUE', 'America/Chicago', '2025-01-07 17:00:00', '2025-01-08 14:20:00', '2025-01-07 23:00:00', '2025-01-08 20:20:00'),
('CBOT', 'FIX', 'REGULAR', '2025-01-01', 'WED', 'America/Chicago', '2025-01-08 17:00:00', '2025-01-09 14:20:00', '2025-01-08 23:00:00', '2025-01-09 20:20:00'),
('CBOT', 'FIX', 'REGULAR', '2025-01-01', 'THU', 'America/Chicago', '2025-01-09 17:00:00', '2025-01-10 14:20:00', '2025-01-09 23:00:00', '2025-01-10 20:20:00'),
-- NYMEX (New York -> UTC: +5시간)
('NYMEX', 'FIX', 'REGULAR', '2025-01-01', 'SUN', 'America/New_York', '2025-01-05 18:00:00', '2025-01-06 17:00:00', '2025-01-05 23:00:00', '2025-01-06 22:00:00'),
('NYMEX', 'FIX', 'REGULAR', '2025-01-01', 'MON', 'America/New_York', '2025-01-06 18:00:00', '2025-01-07 17:00:00', '2025-01-06 23:00:00', '2025-01-07 22:00:00'),
('NYMEX', 'FIX', 'REGULAR', '2025-01-01', 'TUE', 'America/New_York', '2025-01-07 18:00:00', '2025-01-08 17:00:00', '2025-01-07 23:00:00', '2025-01-08 22:00:00'),
('NYMEX', 'FIX', 'REGULAR', '2025-01-01', 'WED', 'America/New_York', '2025-01-08 18:00:00', '2025-01-09 17:00:00', '2025-01-08 23:00:00', '2025-01-09 22:00:00'),
('NYMEX', 'FIX', 'REGULAR', '2025-01-01', 'THU', 'America/New_York', '2025-01-09 18:00:00', '2025-01-10 17:00:00', '2025-01-09 23:00:00', '2025-01-10 22:00:00'),
-- COMEX (New York -> UTC: +5시간)
('COMEX', 'FIX', 'REGULAR', '2025-01-01', 'SUN', 'America/New_York', '2025-01-05 18:00:00', '2025-01-06 17:00:00', '2025-01-05 23:00:00', '2025-01-06 22:00:00'),
('COMEX', 'FIX', 'REGULAR', '2025-01-01', 'MON', 'America/New_York', '2025-01-06 18:00:00', '2025-01-07 17:00:00', '2025-01-06 23:00:00', '2025-01-07 22:00:00'),
('COMEX', 'FIX', 'REGULAR', '2025-01-01', 'TUE', 'America/New_York', '2025-01-07 18:00:00', '2025-01-08 17:00:00', '2025-01-07 23:00:00', '2025-01-08 22:00:00'),
('COMEX', 'FIX', 'REGULAR', '2025-01-01', 'WED', 'America/New_York', '2025-01-08 18:00:00', '2025-01-09 17:00:00', '2025-01-08 23:00:00', '2025-01-09 22:00:00'),
('COMEX', 'FIX', 'REGULAR', '2025-01-01', 'THU', 'America/New_York', '2025-01-09 18:00:00', '2025-01-10 17:00:00', '2025-01-09 23:00:00', '2025-01-10 22:00:00'),
-- ICEEU (London -> UTC: 0시간)
('ICEEU', 'FIX', 'REGULAR', '2025-01-01', 'MON', 'Europe/London', '2025-01-06 08:00:00', '2025-01-06 18:00:00', '2025-01-06 08:00:00', '2025-01-06 18:00:00'),
('ICEEU', 'FIX', 'REGULAR', '2025-01-01', 'TUE', 'Europe/London', '2025-01-07 08:00:00', '2025-01-07 18:00:00', '2025-01-07 08:00:00', '2025-01-07 18:00:00'),
('ICEEU', 'FIX', 'REGULAR', '2025-01-01', 'WED', 'Europe/London', '2025-01-08 08:00:00', '2025-01-08 18:00:00', '2025-01-08 08:00:00', '2025-01-08 18:00:00'),
('ICEEU', 'FIX', 'REGULAR', '2025-01-01', 'THU', 'Europe/London', '2025-01-09 08:00:00', '2025-01-09 18:00:00', '2025-01-09 08:00:00', '2025-01-09 18:00:00'),
('ICEEU', 'FIX', 'REGULAR', '2025-01-01', 'FRI', 'Europe/London', '2025-01-10 08:00:00', '2025-01-10 18:00:00', '2025-01-10 08:00:00', '2025-01-10 18:00:00'),
-- NSE (Kolkata -> UTC: -5:30시간)
('NSE', 'FIX', 'REGULAR', '2025-01-01', 'MON', 'Asia/Kolkata', '2025-01-06 09:15:00', '2025-01-06 15:30:00', '2025-01-06 03:45:00', '2025-01-06 10:00:00'),
('NSE', 'FIX', 'REGULAR', '2025-01-01', 'TUE', 'Asia/Kolkata', '2025-01-07 09:15:00', '2025-01-07 15:30:00', '2025-01-07 03:45:00', '2025-01-07 10:00:00'),
('NSE', 'FIX', 'REGULAR', '2025-01-01', 'WED', 'Asia/Kolkata', '2025-01-08 09:15:00', '2025-01-08 15:30:00', '2025-01-08 03:45:00', '2025-01-08 10:00:00'),
('NSE', 'FIX', 'REGULAR', '2025-01-01', 'THU', 'Asia/Kolkata', '2025-01-09 09:15:00', '2025-01-09 15:30:00', '2025-01-09 03:45:00', '2025-01-09 10:00:00'),
('NSE', 'FIX', 'REGULAR', '2025-01-01', 'FRI', 'Asia/Kolkata', '2025-01-10 09:15:00', '2025-01-10 15:30:00', '2025-01-10 03:45:00', '2025-01-10 10:00:00'),
-- OSE (Tokyo -> UTC: -9시간)
('OSE', 'FIX', 'MORNING', '2025-01-01', 'MON', 'Asia/Tokyo', '2025-01-06 09:00:00', '2025-01-06 11:30:00', '2025-01-06 00:00:00', '2025-01-06 02:30:00'),
('OSE', 'FIX', 'AFTERNOON', '2025-01-01', 'MON', 'Asia/Tokyo', '2025-01-06 12:30:00', '2025-01-06 15:15:00', '2025-01-06 03:30:00', '2025-01-06 06:15:00'),
('OSE', 'FIX', 'MORNING', '2025-01-01', 'TUE', 'Asia/Tokyo', '2025-01-07 09:00:00', '2025-01-07 11:30:00', '2025-01-07 00:00:00', '2025-01-07 02:30:00'),
('OSE', 'FIX', 'AFTERNOON', '2025-01-01', 'TUE', 'Asia/Tokyo', '2025-01-07 12:30:00', '2025-01-07 15:15:00', '2025-01-07 03:30:00', '2025-01-07 06:15:00'),
('OSE', 'FIX', 'MORNING', '2025-01-01', 'WED', 'Asia/Tokyo', '2025-01-08 09:00:00', '2025-01-08 11:30:00', '2025-01-08 00:00:00', '2025-01-08 02:30:00'),
('OSE', 'FIX', 'AFTERNOON', '2025-01-01', 'WED', 'Asia/Tokyo', '2025-01-08 12:30:00', '2025-01-08 15:15:00', '2025-01-08 03:30:00', '2025-01-08 06:15:00'),
('OSE', 'FIX', 'MORNING', '2025-01-01', 'THU', 'Asia/Tokyo', '2025-01-09 09:00:00', '2025-01-09 11:30:00', '2025-01-09 00:00:00', '2025-01-09 02:30:00'),
('OSE', 'FIX', 'AFTERNOON', '2025-01-01', 'THU', 'Asia/Tokyo', '2025-01-09 12:30:00', '2025-01-09 15:15:00', '2025-01-09 03:30:00', '2025-01-09 06:15:00'),
('OSE', 'FIX', 'MORNING', '2025-01-01', 'FRI', 'Asia/Tokyo', '2025-01-10 09:00:00', '2025-01-10 11:30:00', '2025-01-10 00:00:00', '2025-01-10 02:30:00'),
('OSE', 'FIX', 'AFTERNOON', '2025-01-01', 'FRI', 'Asia/Tokyo', '2025-01-10 12:30:00', '2025-01-10 15:15:00', '2025-01-10 03:30:00', '2025-01-10 06:15:00')
ON CONFLICT (exchange, type, session, trade_date) DO NOTHING;

-- 코멘트
COMMENT ON TABLE trading_hours IS '거래소별 거래시간 통합 테이블 (FIX: 표준시간, DAILY: 실제시간)';
COMMENT ON COLUMN trading_hours.exchange IS '거래소 코드';
COMMENT ON COLUMN trading_hours.type IS 'FIX: 표준 거래시간, 빈값: IBKR 실시간 데이터';
COMMENT ON COLUMN trading_hours.session IS 'REGULAR, MORNING, AFTERNOON, CLOSED';
COMMENT ON COLUMN trading_hours.trade_date IS '거래일자';
COMMENT ON COLUMN trading_hours.day_of_week IS '요일 (MON, TUE, WED, THU, FRI, SAT, SUN)';
COMMENT ON COLUMN trading_hours.start_time_utc IS '시작시간 (UTC)';
COMMENT ON COLUMN trading_hours.end_time_utc IS '종료시간 (UTC)';
COMMENT ON COLUMN trading_hours.start_time_loc IS '시작시간 (현지)';
COMMENT ON COLUMN trading_hours.end_time_loc IS '종료시간 (현지)';
COMMENT ON COLUMN trading_hours.timezone IS '거래소 시간대';
COMMENT ON COLUMN trading_hours.is_holiday IS '휴일 여부';
COMMENT ON COLUMN trading_hours.raw_data IS 'IBKR 원본 데이터';