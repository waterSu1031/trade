
symbol_from_csv_table_sql = """
CREATE TABLE IF NOT EXISTS symbol_from_csv (
    sec_type TEXT,
    ibkr_symbol TEXT,
    symbol TEXT,
    exchange TEXT,
    currency TEXT,
    description TEXT
);  
"""

exchanges_table_sql = """
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
"""

exc_x_con_table_sql = """
CREATE TABLE IF NOT EXISTS exc_x_con (
    exchange TEXT,
    symbol TEXT,
    PRIMARY KEY (exchange, symbol)
);
"""

contracts_table_sql = """
CREATE TABLE IF NOT EXISTS contracts (
    con_id INTEGER PRIMARY KEY,
    symbol TEXT,                -- 기본 심볼 (ex: AAPL, ES, EUR)
    exchange TEXT,              -- 기본 거래소
    sec_type TEXT,              -- IBKR 기준 자산 타입 (STK, FUT, CASH)
    currency TEXT,              -- 거래 통화 (USD, EUR 등)
    local_symbol TEXT,          -- 로컬 마켓에서 쓰는 심볼
    last_trade_date TEXT,       -- 선물 만기일 (YYYYMM 또는 YYYYMMDD, STK/CASH는 NULL)
    multiplier TEXT,            -- 계약 승수 (선물만 의미 있음)
    right_type TEXT,            -- 옵션 권리 구분 (C/P)

    desc TEXT,                  -- 종목 설명
    market_name TEXT,           -- 거래소 표시용 이름
    min_tick DOUBLE,            -- 최소 호가 단위
    trading_class TEXT,         -- 거래 클래스 (옵션 등 구분)
    time_zone_id TEXT,          -- 거래소 시간대
    valid_exchanges TEXT,       -- 유효한 거래소 리스트 (쉼표로 구분)
    trading_hours TEXT,         -- 정규 거래 시간대 (YYYYMMDD:HHMM-HHMM;)
    liquid_hours TEXT,          -- 유동성 시간 (주로 선물만 의미 있음)
    market_rule_ids TEXT,       -- 가격 호가 규칙 ID
    order_types TEXT,           -- 허용 주문 타입 (MKT, LMT 등)
    is_ibkr_routable BOOLEAN,   -- IBKR 직접 주문 가능 여부
    is_data_source BOOLEAN      -- 데이터만 제공하는 경우
);
"""

con_x_data_table_sql = """
CREATE TABLE IF NOT EXISTS con_x_data (
    con_id INTEGER PRIMARY KEY,
    contract TEXT NOT NULL,
    -- database TEXT,                 -- 예: 'CN, US, EU'
    interval TEXT,                 -- 예: '5s,1m,1R' (쉼표 구분)
    -- 만기일자
    is_active TEXT DEFAULT 'Y',    -- 'Y' or 'N'
    is_live TEXT DEFAULT 'N'       -- 실시간 대상 여부, 연결/해체 상태
);
"""

data_table_sql = """
CREATE TABLE IF NOT EXISTS symbol_interval (
    timestamp TIMESTAMP NOT NULL,     -- 각 캔들의 시작 시간
    index INTEGER,                    -- 레인지 바일 경우 순번 또는 범위 구분용
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    PRIMARY KEY (timestamp, index)    -- 데이터 중복 방지
);
"""

sample_insert_sql = """
CREATE TABLE IF NOT EXISTS sample_insert_sql (
    id INTEGER PRIMARY KEY ,
    table_name TEXT NOT NULL,          -- 대상 테이블 (예: AAPL_1234)
    description TEXT,                  -- 설명 (예: 5초 간격 테스트용)
    insert_sql TEXT NOT NULL,          -- 실제 INSERT SQL 전체
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# -------------------------------------------------------------------------------------------------------------------

insert_exchanges = """
    INSERT INTO exchanges(exchange, region, asset_type, aws_coverage, timezone, location_lat, location_lon, description) VALUES
        ('CME', 'North America', 'Various (Agriculture, Energy, Metals, Indices, Interest Rates)', 'us-east-2', 'America/Chicago', 41.883, -87.632, 'CME Group: CME, CBOT, NYMEX, COMEX 포함'),
        ('CFE', 'North America', 'Volatility, Index Futures', 'us-east-2', 'America/Chicago', 41.878, -87.631, 'CBOE Futures Exchange'),
        ('ICEUS', 'North America', 'Agriculture, Energy, Financials', 'us-east-1', 'America/New_York', 40.712, -74.006, 'ICE Futures U.S.'),
        ('MX', 'North America', 'Interest Rates, Equity Futures', 'ca-central-1', 'America/Montreal', 45.508, -73.554, 'Montreal Exchange'),
        ('MEXDER', 'North America', 'Agriculture, Financial Futures', 'us-east-2', 'America/Mexico_City', 19.432, -99.133, 'Mexican Derivatives Exchange'),
        ('EUX', 'Europe', 'Interest Rates, Equity Indices', 'eu-central-1', 'Europe/Berlin', 50.110, 8.682, 'Eurex, 독일 기반 유럽 최대 파생상품 거래소'),
        ('ICEEU', 'Europe', 'Energy, Financials', 'eu-west-2', 'Europe/London', 51.515, -0.092, 'ICE Futures Europe (런던)'),
        ('ENX', 'Europe', 'Indices, Commodities', 'eu-west-1', 'Europe/Paris', 48.856, 2.352, 'Euronext Derivatives'),
        ('LME', 'Europe', 'Metals', 'eu-west-2', 'Europe/London', 51.507, -0.127, 'London Metal Exchange'),
        ('MEFF', 'Europe', 'Equity, Interest Rate Futures', 'eu-south-1', 'Europe/Madrid', 40.416, -3.703, 'Spanish MEFF 파생상품 거래소'),
        ('KRX', 'Asia', 'Equity, Interest Rate, Commodities', 'ap-northeast-2', 'Asia/Seoul', 37.566, 126.978, 'Korea Exchange - 선물/옵션'),
        ('TOCOM', 'Asia', 'Energy, Metals', 'ap-northeast-1', 'Asia/Tokyo', 35.689, 139.692, 'Tokyo Commodity Exchange'),
        ('OSE', 'Asia', 'Equity, Index Futures', 'ap-northeast-1', 'Asia/Tokyo', 34.693, 135.502, 'Osaka Exchange'),
        ('TAIFEX', 'Asia', 'Equity, Interest Rate, Currency', 'ap-northeast-1', 'Asia/Taipei', 25.033, 121.565, 'Taiwan Futures Exchange'),
        ('SGX', 'Asia', 'Equity, Commodity, FX Futures', 'ap-southeast-1', 'Asia/Singapore', 1.352, 103.819, 'Singapore Exchange Derivatives'),
        ('SHFE', 'Asia', 'Metals, Energy Futures', 'ap-east-1', 'Asia/Shanghai', 31.230, 121.473, 'Shanghai Futures Exchange'),
        ('DCE', 'Asia', 'Agriculture, Metals Futures', 'ap-east-1', 'Asia/Dalian', 38.914, 121.614, 'Dalian Commodity Exchange'),
        ('ZCE', 'Asia', 'Agriculture, Energy Futures', 'ap-east-1', 'Asia/Zhengzhou', 34.746, 113.625, 'Zhengzhou Commodity Exchange'),
        ('B3', 'South America', 'Agriculture, Financial Futures', 'sa-east-1', 'America/Sao_Paulo', -23.550, -46.633, 'B3 (브라질거래소)'),
        ('ROFEX', 'South America', 'Agriculture Futures', 'sa-east-1', 'America/Argentina/Buenos_Aires', -34.603, -58.381, 'MATba-ROFEX (아르헨티나)'),
        ('SAFEX', 'Africa', 'Agriculture, Energy Futures', 'af-south-1', 'Africa/Johannesburg', -26.204, 28.047, 'South African Futures Exchange'),
        ('DGCX', 'Middle East', 'Metals, Currency Futures', 'me-central-1', 'Asia/Dubai', 25.204, 55.270, 'Dubai Gold & Commodities Exchange'),
        ('DME', 'Middle East', 'Energy Futures', 'me-central-1', 'Asia/Dubai', 25.204, 55.270, 'Dubai Mercantile Exchange'),
        ('TURDEX', 'Middle East', 'Agriculture, Financial Futures', 'eu-central-1', 'Europe/Istanbul', 41.008, 28.978, 'Turkish Derivatives Market');
"""
insert_exc_x_con = """
    INSERT INTO exc_x_con VALUES
        ('CME', 200001),
        ('CME', 200002),
        ('CME', 200003),
        ('CME', 200004),
        ('NYMEX', 200005),
        ('COMEX', 200006),
        ('COMEX', 200007),
        ('SGX', 200008),
        ('OSE', 200009),
        ('HKEX', 200010);
"""

insert_contracts = """
    INSERT INTO contracts VALUES
        (200001, 'ES', 'CME', 'CONTFUT', 'USD', 'ES', 'E-mini S&P 500 Continuous', 'CME', 0.25, 'ES', 'America/Chicago', 'CME', '20240625:1700-1600;', '20240625:1730-1600;', '26', 'MKT,LMT,STP', 'FUT', NULL, '50', TRUE, TRUE),
        (200002, 'NQ', 'CME', 'CONTFUT', 'USD', 'NQ', 'E-mini NASDAQ 100 Continuous', 'CME', 0.25, 'NQ', 'America/Chicago', 'CME', '20240625:1700-1600;', '20240625:1730-1600;', '26', 'MKT,LMT,STP', 'FUT', NULL, '20', TRUE, TRUE),
        (200003, 'YM', 'CME', 'CONTFUT', 'USD', 'YM', 'E-mini Dow Continuous', 'CME', 1.0, 'YM', 'America/Chicago', 'CME', '20240625:1700-1600;', '20240625:1730-1600;', '26', 'MKT,LMT,STP', 'FUT', NULL, '5', TRUE, TRUE),
        (200004, 'RTY', 'CME', 'CONTFUT', 'USD', 'RTY', 'E-mini Russell 2000 Continuous', 'CME', 0.1, 'RTY', 'America/Chicago', 'CME', '20240625:1700-1600;', '20240625:1730-1600;', '26', 'MKT,LMT,STP', 'FUT', NULL, '50', TRUE, TRUE),
        (200005, 'CL', 'NYMEX', 'CONTFUT', 'USD', 'CL', 'Crude Oil WTI Continuous', 'NYMEX', 0.01, 'CL', 'America/Chicago', 'NYMEX', '20240625:1700-1600;', '20240625:1730-1600;', '27', 'MKT,LMT,STP', 'FUT', NULL, '1000', TRUE, TRUE),
        (200006, 'GC', 'COMEX', 'CONTFUT', 'USD', 'GC', 'Gold Continuous', 'COMEX', 0.1, 'GC', 'America/New_York', 'COMEX', '20240625:1800-1700;', '20240625:1900-1700;', '27', 'MKT,LMT,STP', 'FUT', NULL, '100', TRUE, TRUE),
        (200007, 'SI', 'COMEX', 'CONTFUT', 'USD', 'SI', 'Silver Continuous', 'COMEX', 0.005, 'SI', 'America/New_York', 'COMEX', '20240625:1800-1700;', '20240625:1900-1700;', '27', 'MKT,LMT,STP', 'FUT', NULL, '5000', TRUE, TRUE),
        (200008, 'A50', 'SGX', 'CONTFUT', 'USD', 'A50', 'FTSE China A50 Continuous', 'SGX', 2.0, 'CN', 'Asia/Singapore', 'SGX', '20240625:0900-1715;', '20240625:0915-1700;', '28', 'MKT,LMT', 'FUT', NULL, '1', TRUE, TRUE),
        (200009, 'NK225', 'OSE', 'CONTFUT', 'JPY', 'NK225', 'Nikkei 225 Continuous', 'OSE', 10.0, 'NI225', 'Asia/Tokyo', 'OSE', '20240625:0900-1530;', '20240625:0915-1515;', '29', 'MKT,LMT', 'FUT', NULL, '1000', TRUE, TRUE),
        (200010, 'HSI', 'HKEX', 'CONTFUT', 'HKD', 'HSI', 'Hang Seng Index Continuous', 'HKEX', 1.0, 'HSI', 'Asia/Hong_Kong', 'HKEX', '20240625:0915-1615;', '20240625:0930-1600;', '30', 'MKT,LMT', 'FUT', NULL, '50', TRUE, TRUE);
"""

insert_con_x_data = """
    INSERT INTO con_x_data (contract, con_id, data_path, interval, is_active, is_live) VALUES
        ('ES',     200001, 'US.sqlite.ES',     '5s,1m,1R', 'Y', 'Y'),
        ('NQ',     200002, 'US.sqlite.NQ',     '5s,1m,1R', 'Y', 'Y'),
        ('YM',     200003, 'US.sqlite.YM',     '5s,1m,1R', 'Y', 'Y'),
        ('RTY',    200004, 'US.sqlite.RTY',    '5s,1m,1R', 'Y', 'Y'),
        ('CL',     200005, 'US.sqlite.CL',     '5s,1m,1R', 'Y', 'Y'),
        ('GC',     200006, 'US.sqlite.GC',     '5s,1m,1R', 'Y', 'Y'),
        ('SI',     200007, 'US.sqlite.SI',     '5s,1m,1R', 'Y', 'Y'),
        ('A50',    200008, 'CN.sqlite.A50',    '5s,1m,1R', 'Y', 'Y'),
        ('NK225',  200009, 'JP.sqlite.NK225',  '5s,1m,1R', 'Y', 'Y'),
        ('HSI',    200010, 'HK.sqlite.HSI',    '5s,1m,1R', 'Y', 'Y');
"""
