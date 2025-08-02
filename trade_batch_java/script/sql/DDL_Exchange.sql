
-- exchange definition
CREATE TABLE exchange (
    exchange VARCHAR(32) PRIMARY KEY,
    country VARCHAR(16),
    sec_type VARCHAR(8),
    aws_coverage VARCHAR(12),
    timezone VARCHAR(24),
    location_lat REAL,
    location_lon REAL,
    description VARCHAR(100),
    symbol_cnt INTEGER
);

CREATE TABLE exc_x_con (
    con_id INTEGER PRIMARY KEY,
    exchange VARCHAR(16),
    symbol VARCHAR(16),
    sec_type VARCHAR(16)
);

INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('NSE', 'India', 'FUT', 'CN', 'Asia/Kolkata', 19.0822, 72.7411, '인도 뭄바이에 위치한 국가증권거래소(National Stock Exchange of India)', 228);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('EUREX', 'Germany', 'FUT', 'EU', 'Europe/Berlin', 50.1109, 8.6821, '유럽 최대 파생상품 거래소, Deutsche Börse가 운영', 163);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('KSE', 'South Korea', 'FUT', 'CN', 'Asia/Seoul', 37.5665, 126.978, '한국거래소(Korea Exchange), KOSPI, KOSDAQ, 선물/옵션 시장 포함', 162);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('CME', 'United States', 'FUT', 'US', 'America/Chicago', 41.8781, -87.6298, '미국 시카고 소재 CME Group 소속 세계 최대 파생상품 거래소', 150);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('HKFE', 'Hong Kong', 'FUT', 'CN', 'Asia/Hong_Kong', 22.2855, 114.1577, '홍콩 선물거래소 (Hong Kong Futures Exchange), HKEX 산하', 123);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('SGX', 'Singapore', 'FUT', 'CN', 'Asia/Singapore', 1.3521, 103.8198, '싱가포르거래소 (Singapore Exchange), 주식과 파생상품 포함', 94);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('OMS', 'Japan', 'FUT', 'CN', 'Asia/Tokyo', 34.6937, 135.5023, '일본 오사카(Osaka Mercantile Securities) 중심의 거래소', 62);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('CBOT', 'United States', 'FUT', 'US', 'America/Chicago', 41.8781, -87.6298, '시카고상품거래소 (Chicago Board of Trade), CME Group에 속함', 55);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('ICEEU', 'United Kingdom', 'FUT', 'EU', 'Europe/London', 51.5074, -0.1278, 'Intercontinental Exchange Europe, 런던에 위치한 ICE 계열 파생상품 거래소', 36);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('MEFFRV', 'Spain', 'FUT', 'EU', 'Europe/Madrid', 40.4168, -3.7038, 'MEFF (Mercado Español de Futuros Financieros), 스페인 금융 선물 거래소', 28);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('IDEM', 'Italy', 'FUT', 'EU', 'Europe/Rome', 45.4642, 9.19, '이탈리아 파생상품 거래소, Borsa Italiana의 IDEM 시장', 24);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('FTA', 'United Kingdom', 'FUT', 'EU', 'Europe/London', 37.9838, 23.7275, 'FTA (Financial Times Stock Exchange) 기반 파생상품 거래소로 추정됨', 22);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('OSE', 'Japan', 'FUT', 'CN', 'Asia/Tokyo', 34.6913, 135.5046, '오사카거래소 (Osaka Exchange, OSE), 일본을 대표하는 파생상품 거래소', 21);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('NYMEX', 'United States', 'FUT', 'US', 'America/New_York', 40.7069, -74.0113, 'NYMEX (New York Mercantile Exchange), 에너지 및 원자재 중심 거래소, CME 소속', 21);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('NYBOT', 'United States', 'FUT', 'US', 'America/New_York', 40.7069, -74.0113, 'NYBOT (New York Board of Trade), 농산물/원자재 파생상품 거래소, ICE 소속', 19);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('COMEX', 'United States', 'FUT', 'US', 'America/New_York', 40.7069, -74.0113 , 'COMEX (Commodity Exchange Inc.), 금속 중심의 파생상품 거래소, CME 소속', 15);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('ICEUS', 'United States', 'FUT', 'US', 'America/New_York', 33.749, -84.388, 'ICEUS (Intercontinental Exchange US), 뉴욕 기반 ICE 미국 거래소', 13);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('NYSELIFFE', 'United Kingdom', 'FUT', 'EU', 'Europe/London', 51.5074, -0.1278, 'NYSE LIFFE (London International Financial Futures and Options Exchange), 유럽 기반 파생상품 거래소', 11);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('MEXDER', 'Mexico', 'FUT', 'US', 'America/Mexico_City', 19.4326, -99.1332, 'MEXDER (Mexican Derivatives Exchange), 멕시코 파생상품 거래소', 9);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('IPE', 'United Kingdom', 'FUT', 'EU', 'Europe/London', 51.5074, -0.1278, 'IPE (International Petroleum Exchange), 에너지 거래 전문, 현재 ICE 소속', 9);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('CFE', 'United States', 'FUT', 'US', 'America/Chicago', 41.8781, -87.6298, 'CFE (CBOE Futures Exchange), 시카고 기반 변동성 지수(VIX) 거래소', 9);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('CDE', 'Canada', 'FUT', 'US', 'America/Toronto', 43.6532, -79.3832, 'CDE (Canadian Derivatives Exchange), 캐나다 파생상품 거래소 (Montreal Exchange)', 9);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('SNFE', 'South Korea', 'FUT', 'CN', 'Asia/Seoul', -33.8688, 151.2093, 'SNFE (Seoul National Futures Exchange), 한국 파생상품 거래소 (KRX 계열)', 6);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('LMEOTC', 'United Kingdom', 'FUT', 'EU', 'Europe/London', 51.5074, -0.1278, 'LME OTC (London Metal Exchange Over-the-Counter), 금속 장외파생상품 거래소', 6);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('MONEP', 'France', 'FUT', 'EU', 'Europe/Paris', 48.8566, 2.3522, 'MONEP (Marché des Options Négociables de Paris), 프랑스 옵션 거래소', 5);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('ICEEUSOFT', 'United Kingdom', 'FUT', 'EU', 'Europe/London', 51.5074, -0.1278, 'ICE Europe Soft Commodities, 영국 기반 소프트 커머디티(커피, 코코아 등) 거래소', 4);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('MATIF', 'France', 'FUT', 'EU', 'Europe/Paris', 48.8566, 2.3522, 'MATIF (Marché à Terme International de France), 프랑스 선물거래소, 현재 Euronext Paris에 통합', 3);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('ENDEX', 'Netherlands', 'FUT', 'EU', 'Europe/Amsterdam', 52.3676, 4.9041, 'ENDEX (European Energy Derivatives Exchange), 에너지 중심 파생상품 거래소', 2);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('BURSAMY', 'Malaysia', 'FUT', 'CN', 'Asia/Kuala_Lumpur', 3.139, 101.6869, 'BURSAMY (Bursa Malaysia Derivatives), 말레이시아 선물 및 옵션 거래소', 2);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('SGXCME', 'Singapore', 'FUT', 'CN', 'Asia/Singapore', 1.3521, 103.8198, 'SGX-CME Link (SGXCME), 싱가포르 거래소와 CME 간 파생상품 연계 시장', 1);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('CFETAS', 'Austria', 'FUT', 'EU', 'Europe/Vienna', 31.2304, 121.4737, 'CFETAS (Central Futures Exchange of Austria), 오스트리아 기반의 파생상품 거래 플랫폼', 1);
INSERT INTO exchange
(exchange, country, sec_type, aws_coverage, timezone, location_lat, location_lon, description, symbol_cnt)
VALUES('BELFOX', 'Belgium', 'FUT', 'EU', 'Europe/Brussels', 50.8503, 4.3517, 'BELFOX (Belgian Futures and Options Exchange), 벨기에 선물 및 옵션 거래소, Euronext Brussels로 통합', 1);

