-- 트레이딩 전용 DB
--CREATE DATABASE TRADE;

-- 데이터(시세) DB: 리전별
--CREATE DATABASE DATA_CN;   -- 중국 리전
--CREATE DATABASE DATA_US;   -- 미국 리전
--CREATE DATABASE DATA_EU;   -- 유럽 리전


--ㅁㅁㅁ 테이블 ㅁㅁㅁ

CREATE TABLE price_time (
    symbol      VARCHAR(16) NOT NULL,
    exchange    VARCHAR(16) NOT NULL,
    utc         TIMESTAMP NOT NULL,      -- UTC 기준 바 시작시간
    loc         TIMESTAMP,               -- 현지(로컬) 바 시작시간
    open        DECIMAL(12,4),
    high        DECIMAL(12,4),
    low         DECIMAL(12,4),
    close       DECIMAL(12,4),
    volume      BIGINT,
    count       INTEGER,
    vwap        DECIMAL(12,4),
    PRIMARY KEY (symbol, exchange, utc)
) PARTITION BY LIST (symbol);

CREATE TABLE price_range (
    symbol      VARCHAR(16) NOT NULL,
    exchange    VARCHAR(16) NOT NULL,
    utc         TIMESTAMP NOT NULL,
    loc         TIMESTAMP,
    range_size  DECIMAL(8,4) NOT NULL,
    idx         INTEGER NOT NULL,        -- 해당 조건 내 순번
    open        DECIMAL(12,4),
    high        DECIMAL(12,4),
    low         DECIMAL(12,4),
    close       DECIMAL(12,4),
    volume         BIGINT,
    cnt         INTEGER,                 -- 해당 range bar에 포함된 분봉/틱 수
    vwap        DECIMAL(12,4),
    PRIMARY KEY (symbol, exchange, utc, range_size, idx)
) PARTITION BY LIST (symbol);

CREATE TABLE price_volume (
    symbol      VARCHAR(16) NOT NULL,
    exchange    VARCHAR(16) NOT NULL,
    utc         TIMESTAMP NOT NULL,
    loc         TIMESTAMP,
    vol_size    BIGINT NOT NULL,         -- 누적 거래량 기준치
    idx         INTEGER NOT NULL,        -- 해당 조건 내 순번
    open        DECIMAL(12,4),
    high        DECIMAL(12,4),
    low         DECIMAL(12,4),
    close       DECIMAL(12,4),
    volume         BIGINT,
    cnt         INTEGER,                 -- 해당 볼륨바에 포함된 분봉/틱 수
    vwap        DECIMAL(12,4),
    PRIMARY KEY (symbol, exchange, utc, vol_size, idx)
) PARTITION BY LIST (symbol);



-- ㅁㅁㅁ 코멘트 ㅁㅁㅁ

-- 테이블 코멘트
COMMENT ON TABLE price_time IS '시계열(Time Bar) 1분봉 등 가격 데이터 테이블';
-- 컬럼 코멘트
COMMENT ON COLUMN price_time.symbol IS '종목코드(Symbol)';
COMMENT ON COLUMN price_time.exchange IS '거래소코드(Exchange)';
COMMENT ON COLUMN price_time.utc IS 'UTC 기준 바 시작시간';
COMMENT ON COLUMN price_time.loc IS '현지(로컬) 바 시작시간';
COMMENT ON COLUMN price_time.open IS '시가(Open)';
COMMENT ON COLUMN price_time.high IS '고가(High)';
COMMENT ON COLUMN price_time.low IS '저가(Low)';
COMMENT ON COLUMN price_time.close IS '종가(Close)';
COMMENT ON COLUMN price_time.volume IS '거래량(Volume)';
COMMENT ON COLUMN price_time.vwap IS '거래량가중평균가격(VWAP)';

-- 테이블 코멘트
COMMENT ON TABLE price_range IS '레인지 바(Range Bar) 기반 가격 데이터 테이블';
-- 컬럼 코멘트
COMMENT ON COLUMN price_range.symbol IS '종목코드(Symbol)';
COMMENT ON COLUMN price_range.exchange IS '거래소코드(Exchange)';
COMMENT ON COLUMN price_range.utc IS 'UTC 기준 바 시작시간';
COMMENT ON COLUMN price_range.loc IS '현지(로컬) 바 시작시간';
COMMENT ON COLUMN price_range.range_size IS '레인지 바의 크기(단위 가격)';
COMMENT ON COLUMN price_range.idx IS '동일 조건 내 바의 순번(Index)';
COMMENT ON COLUMN price_range.open IS '시가(Open)';
COMMENT ON COLUMN price_range.high IS '고가(High)';
COMMENT ON COLUMN price_range.low IS '저가(Low)';
COMMENT ON COLUMN price_range.close IS '종가(Close)';
COMMENT ON COLUMN price_range.volume IS '거래량(Volume)';
COMMENT ON COLUMN price_range.cnt IS '해당 range bar에 포함된 분봉/틱 수';
COMMENT ON COLUMN price_range.vwap IS '거래량가중평균가격(VWAP)';

-- 테이블 코멘트
COMMENT ON TABLE price_volume IS '볼륨 바(Volume Bar) 기반 가격 데이터 테이블';
-- 컬럼 코멘트
COMMENT ON COLUMN price_volume.symbol IS '종목코드(Symbol)';
COMMENT ON COLUMN price_volume.exchange IS '거래소코드(Exchange)';
COMMENT ON COLUMN price_volume.utc IS 'UTC 기준 바 시작시간';
COMMENT ON COLUMN price_volume.loc IS '현지(로컬) 바 시작시간';
COMMENT ON COLUMN price_volume.vol_size IS '볼륨바의 누적 거래량 기준치(Volume Size)';
COMMENT ON COLUMN price_volume.idx IS '동일 조건 내 바의 순번(Index)';
COMMENT ON COLUMN price_volume.open IS '시가(Open)';
COMMENT ON COLUMN price_volume.high IS '고가(High)';
COMMENT ON COLUMN price_volume.low IS '저가(Low)';
COMMENT ON COLUMN price_volume.close IS '종가(Close)';
COMMENT ON COLUMN price_volume.volume IS '해당 바의 거래량(Volume)';
COMMENT ON COLUMN price_volume.cnt IS '해당 볼륨바에 포함된 분봉/틱 수';
COMMENT ON COLUMN price_volume.vwap IS '거래량가중평균가격(VWAP)';
