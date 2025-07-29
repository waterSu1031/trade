
--ㅁㅁㅁ 테이블 생성 ㅁㅁㅁ
CREATE TABLE IF NOT EXISTS symbol_from_csv (
    sec_type TEXT,
    ibkr_symbol TEXT,
    symbol TEXT,
    exchange TEXT,
    currency TEXT,
    description TEXT
);

CREATE TABLE contract (
    con_id                  INTEGER PRIMARY KEY,
    symbol                  VARCHAR(16)  NOT NULL,
    sec_type                VARCHAR(8)   NOT NULL,

    last_trade_date_or_contract_month VARCHAR(16),
    crt_month_con_id        INTEGER,
    last_trade_date         VARCHAR(16),
    strike                  DOUBLE PRECISION,
    right_                  VARCHAR(2),
    multiplier              VARCHAR(8),
    exchange                VARCHAR(16)  NOT NULL,
    primary_exch            VARCHAR(16),
    currency                VARCHAR(8)   NOT NULL,
    local_symbol            VARCHAR(32),
    trading_class           VARCHAR(16),
    sec_id_type             VARCHAR(16),
    sec_id                  VARCHAR(32),
    description             VARCHAR(128),
    issuer_id               VARCHAR(32),
    delta_neutral_conid     INTEGER,      -- DeltaNeutralContract: 참조용 conid (별도 테이블로 확장 가능)
    include_expired         BOOLEAN DEFAULT FALSE
    -- combo_legs_descrip      VARCHAR(256)
    -- combo_legs            는 별도 테이블/관계로 설계 (보통 N:1 구조)
);

CREATE TABLE con_x_data (
    symbol        VARCHAR(16) NOT NULL,
    exchange      VARCHAR(16) NOT NULL,
    data_type     VARCHAR(8) NOT NULL,     -- 'TIME', 'RANGE', 'VOLUME'
    size          DECIMAL(16,4),           -- range/volume 공통 기준치 (time이면 NULL)
    stt_date_loc  TIMESTAMP NOT NULL,
    end_date_loc  TIMESTAMP NOT NULL,
    row_count     BIGINT,
    data_status   VARCHAR(16),             -- 'COMPLETE', 'PARTIAL', 'ERROR', 'BACKUP', 'IN PROGRESS' 등
    last_update   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, exchange, data_type, size)
);


CREATE TABLE contract_detail (
    con_id               INTEGER PRIMARY KEY,              -- FK to contract(conid)
    market_name         VARCHAR(32),
    min_tick            DOUBLE PRECISION,
    price_magnifier     INTEGER,
    order_types         VARCHAR(128),
    valid_exchanges     VARCHAR(128),
    long_name           VARCHAR(128),
    time_zone_id        VARCHAR(64),
    trading_hours       VARCHAR(128),
    liquid_hours        VARCHAR(128),
    agg_group           INTEGER,
    market_rule_ids     VARCHAR(64),
    FOREIGN KEY (con_id) REFERENCES contract(con_id)
);

CREATE TABLE contract_detail_stock (
    con_id          INTEGER PRIMARY KEY,
    industry        VARCHAR(64),
    category        VARCHAR(64),
    subcategory     VARCHAR(64),
    stock_type      VARCHAR(16),     -- 예: COMMON, PREFERRED
    FOREIGN KEY (con_id) REFERENCES contract(con_id)
);

CREATE TABLE contract_detail_future (
    con_id               INTEGER PRIMARY KEY,
    contract_month       VARCHAR(8),     -- 예: 202409
    real_expiration_date VARCHAR(16),    -- 예: 20240918
    last_trade_time      VARCHAR(32),
    ev_rule              VARCHAR(32),
    ev_multiplier        DOUBLE PRECISION,
    under_conid          INTEGER,
    under_symbol         VARCHAR(32),
    under_sec_type       VARCHAR(16),
    FOREIGN KEY (con_id) REFERENCES contract(con_id)
);

CREATE TABLE contract_detail_option (
    con_id               INTEGER PRIMARY KEY,
    contract_month       VARCHAR(8),       -- 예: 202409
    real_expiration_date VARCHAR(16),      -- 예: 20240920
    last_trade_time      VARCHAR(32),
    ev_rule              VARCHAR(32),
    ev_multiplier        DOUBLE PRECISION,
    under_conid          INTEGER,
    under_symbol         VARCHAR(32),
    under_sec_type       VARCHAR(16),
    FOREIGN KEY (con_id) REFERENCES contract(con_id)
);

CREATE TABLE contract_detail_bond (
    con_id          INTEGER PRIMARY KEY,
    bond_type       VARCHAR(32),
    coupon_type     VARCHAR(32),
    coupon          DOUBLE PRECISION,
    callable        BOOLEAN,
    putable         BOOLEAN,
    convertible     BOOLEAN,
    maturity        VARCHAR(16),
    issue_date      VARCHAR(16),
    ratings         VARCHAR(32),
    cusip           VARCHAR(32),
    desc_append     VARCHAR(128),
    FOREIGN KEY (con_id) REFERENCES contract(con_id)
);

CREATE TABLE contract_detail_fund (
    con_id                    INTEGER PRIMARY KEY,
    fund_name                 VARCHAR(128),
    fund_family               VARCHAR(128),
    fund_type                 VARCHAR(64),
    fund_front_load           VARCHAR(16),
    fund_back_load            VARCHAR(16),
    fund_management_fee       VARCHAR(16),
    fund_minimum_initial_purchase   VARCHAR(16),
    fund_subsequent_minimum_purchase VARCHAR(16),
    fund_closed               BOOLEAN,
    fund_closed_for_new_investors BOOLEAN,
    fund_closed_for_new_money BOOLEAN,
    FOREIGN KEY (con_id) REFERENCES contract(con_id)
);

CREATE TABLE contract_detail_fx (
    con_id           INTEGER PRIMARY KEY,
    under_symbol     VARCHAR(32),    -- 예: USD
    under_sec_type   VARCHAR(16),    -- 예: CASH
    FOREIGN KEY (con_id) REFERENCES contract(con_id)
);

CREATE TABLE contract_detail_index (
    con_id         INTEGER PRIMARY KEY,
    industry       VARCHAR(64),
    category       VARCHAR(64),
    FOREIGN KEY (con_id) REFERENCES contract(con_id)
);

--ㅁㅁㅁ 코멘트 생성 ㅁㅁㅁ

COMMENT ON TABLE contract IS '종목 기본정보(IBKR Contract 객체 1:1 대응)';
COMMENT ON COLUMN contract.con_id IS '고유 종목번호(PK, IBKR에서 부여하는 불변 ID)';
COMMENT ON COLUMN contract.symbol IS '심볼(티커) 코드, 예: AAPL, ES';
COMMENT ON COLUMN contract.sec_type IS '자산유형(주식: STK, 선물: FUT, 옵션: OPT 등)';
COMMENT ON COLUMN contract.last_trade_date_or_contract_month IS '최종거래일 또는 만기월(선물/옵션: YYYYMM 혹은 YYYYMMDD)';
COMMENT ON COLUMN contract.last_trade_date IS '최종거래일(YYYYMMDD, 옵션/선물 등 파생)';
COMMENT ON COLUMN contract.strike IS '행사가(옵션/파생상품)';
COMMENT ON COLUMN contract.right_ IS '옵션 권리 구분(C: 콜, P: 풋)';
COMMENT ON COLUMN contract.multiplier IS '계약 승수(한 계약당 기초자산 수량, 예: 100)';
COMMENT ON COLUMN contract.exchange IS '주요 거래소(SMART, NYSE, CME 등)';
COMMENT ON COLUMN contract.primary_exch IS '기본 거래소(주식의 기본 거래소, 예: NASDAQ)';
COMMENT ON COLUMN contract.currency IS '거래 통화(USD, KRW, EUR 등)';
COMMENT ON COLUMN contract.local_symbol IS '로컬(거래소) 심볼, 옵션/선물의 복합심볼 등';
COMMENT ON COLUMN contract.trading_class IS '트레이딩 클래스(거래소별 종목 그룹 구분 코드)';
COMMENT ON COLUMN contract.sec_id_type IS '종목 식별자 유형(ISIN, CUSIP, SEDOL 등)';
COMMENT ON COLUMN contract.sec_id IS '종목 식별자 값(예: ISIN 번호 등)';
COMMENT ON COLUMN contract.description IS '종목 설명(부가 정보)';
COMMENT ON COLUMN contract.issuer_id IS '발행자(issuer) ID, 주로 채권 등에서 사용';
COMMENT ON COLUMN contract.delta_neutral_conid IS 'DeltaNeutral 전략용 참조 conid(옵션, 스프레드 등)';
COMMENT ON COLUMN contract.include_expired IS '만기/폐지 종목 포함 여부(true: 포함, false: 미포함)';
--COMMENT ON COLUMN contract.combo_legs_descrip IS '콤보/스프레드 상품의 leg 설명 문자열';

-- 테이블 코멘트
COMMENT ON TABLE con_x_data IS '종목별 데이터 타입/기간/상태 등 메타 정보 테이블';
-- 컬럼 코멘트
COMMENT ON COLUMN con_x_data.symbol IS '종목코드(Symbol)';
COMMENT ON COLUMN con_x_data.exchange IS '거래소코드(Exchange)';
COMMENT ON COLUMN con_x_data.data_type IS '데이터 종류(TIME, RANGE, VOLUME)';
COMMENT ON COLUMN con_x_data.size IS '범위/볼륨 기준치 (타입별)';
COMMENT ON COLUMN con_x_data.stt_date_loc IS '데이터 시작 UTC';
COMMENT ON COLUMN con_x_data.end_date_loc IS '데이터 종료 UTC';
COMMENT ON COLUMN con_x_data.row_count IS '해당 구간의 데이터 건수';
COMMENT ON COLUMN con_x_data.data_status IS '데이터 상태(COMPELTE, PARTIAL, ERROR, BACKUP, IN_PROGRESS)';
COMMENT ON COLUMN con_x_data.last_update IS '메타 갱신 일시(UTC)';


COMMENT ON TABLE contract_detail IS '종목 상세정보(공통, ContractDetails 객체 기본 필드 대응)';
COMMENT ON COLUMN contract_detail.con_id IS '종목 고유번호(PK, contract.con_id 참조)';
COMMENT ON COLUMN contract_detail.market_name IS 'IBKR 내부 마켓명(예: NYSE, CME, NASDAQ 등)';
COMMENT ON COLUMN contract_detail.min_tick IS '최소 호가 단위(틱 크기, 예: 0.01)';
COMMENT ON COLUMN contract_detail.price_magnifier IS '가격 소수점 조정 배수(특정 파생/지수 등)';
COMMENT ON COLUMN contract_detail.order_types IS '허용 주문타입(쉼표로 구분, 예: LMT,MKT)';
COMMENT ON COLUMN contract_detail.valid_exchanges IS '주문 가능한 거래소(쉼표구분)';
COMMENT ON COLUMN contract_detail.long_name IS '종목 공식명칭(예: Apple Inc.)';
COMMENT ON COLUMN contract_detail.time_zone_id IS '거래시간대(예: America/New_York)';
COMMENT ON COLUMN contract_detail.trading_hours IS '거래시간(복수 세션일 수 있음, 콤마 구분)';
COMMENT ON COLUMN contract_detail.liquid_hours IS '유동성(시장가 가능) 시간대(콤마구분)';
COMMENT ON COLUMN contract_detail.agg_group IS '집계 그룹(IBKR 내부 grouping, 일반적으론 미사용)';
COMMENT ON COLUMN contract_detail.market_rule_ids IS '마켓룰ID(호가단위 등 내부 규칙 ID, 쉼표구분)';

COMMENT ON TABLE contract_detail_stock IS '주식(Stock) 상세정보 테이블(자산별)';
COMMENT ON COLUMN contract_detail_stock.con_id IS '종목 고유번호(PK, contract.con_id 참조)';
COMMENT ON COLUMN contract_detail_stock.industry IS '산업분류(예: Technology, Energy)';
COMMENT ON COLUMN contract_detail_stock.category IS '업종 카테고리(예: Software, Oil & Gas)';
COMMENT ON COLUMN contract_detail_stock.subcategory IS '세부 업종/테마(예: SaaS, Refining)';
COMMENT ON COLUMN contract_detail_stock.stock_type IS '주식종류(COMMON: 보통주, PREFERRED: 우선주 등)';

COMMENT ON TABLE contract_detail_future IS '선물(Futures) 상세정보 테이블(자산별)';
COMMENT ON COLUMN contract_detail_future.con_id IS '종목 고유번호(PK, contract.con_id 참조)';
COMMENT ON COLUMN contract_detail_future.contract_month IS '만기월(YYYYMM, 예: 202409)';
COMMENT ON COLUMN contract_detail_future.real_expiration_date IS '실제 만기일(YYYYMMDD, 예: 20240918)';
COMMENT ON COLUMN contract_detail_future.last_trade_time IS '최종거래일/마감시간';
COMMENT ON COLUMN contract_detail_future.ev_rule IS '이벤트 룰(파생상품 거래규칙, IBKR 내부)';
COMMENT ON COLUMN contract_detail_future.ev_multiplier IS '이벤트 멀티플라이어(계약 단위, 승수 등)';
COMMENT ON COLUMN contract_detail_future.under_conid IS '기초자산의 con_id(연계상품 con_id)';
COMMENT ON COLUMN contract_detail_future.under_symbol IS '기초자산 심볼(코드)';
COMMENT ON COLUMN contract_detail_future.under_sec_type IS '기초자산 유형(예: STK, FUT)';

COMMENT ON TABLE contract_detail_option IS '옵션(Option) 상세정보 테이블(자산별)';
COMMENT ON COLUMN contract_detail_option.con_id IS '종목 고유번호(PK, contract.con_id 참조)';
COMMENT ON COLUMN contract_detail_option.contract_month IS '옵션 만기월(YYYYMM, 예: 202409)';
COMMENT ON COLUMN contract_detail_option.real_expiration_date IS '실제 만기일(YYYYMMDD, 예: 20240920)';
COMMENT ON COLUMN contract_detail_option.last_trade_time IS '최종거래일/마감시간';
COMMENT ON COLUMN contract_detail_option.ev_rule IS '이벤트 룰(옵션 거래규칙, IBKR 내부)';
COMMENT ON COLUMN contract_detail_option.ev_multiplier IS '이벤트 멀티플라이어(계약 단위, 승수 등)';
COMMENT ON COLUMN contract_detail_option.under_conid IS '기초자산의 con_id(연계상품 con_id)';
COMMENT ON COLUMN contract_detail_option.under_symbol IS '기초자산 심볼(코드)';
COMMENT ON COLUMN contract_detail_option.under_sec_type IS '기초자산 유형(예: STK, FUT)';

COMMENT ON TABLE contract_detail_bond IS '채권(Bond) 상세정보 테이블(자산별)';
COMMENT ON COLUMN contract_detail_bond.con_id IS '종목 고유번호(PK, contract.con_id 참조)';
COMMENT ON COLUMN contract_detail_bond.bond_type IS '채권 유형(예: GOVT, CORP)';
COMMENT ON COLUMN contract_detail_bond.coupon_type IS '쿠폰(이자) 유형';
COMMENT ON COLUMN contract_detail_bond.coupon IS '쿠폰(이자)율(%)';
COMMENT ON COLUMN contract_detail_bond.callable IS '조기상환(Call Option) 가능여부';
COMMENT ON COLUMN contract_detail_bond.putable IS 'Put Option(조기상환, 투자자 요청) 가능여부';
COMMENT ON COLUMN contract_detail_bond.convertible IS '전환사채(주식 전환 가능여부)';
COMMENT ON COLUMN contract_detail_bond.maturity IS '만기일(YYYYMMDD)';
COMMENT ON COLUMN contract_detail_bond.issue_date IS '발행일(YYYYMMDD)';
COMMENT ON COLUMN contract_detail_bond.ratings IS '신용등급(문자열, 예: AA+)';
COMMENT ON COLUMN contract_detail_bond.cusip IS 'CUSIP 코드(미국채권 식별자)';
COMMENT ON COLUMN contract_detail_bond.desc_append IS '부가 설명(설명 추가)';

COMMENT ON TABLE contract_detail_fund IS '펀드(Fund, ETF 등) 상세정보 테이블(자산별)';
COMMENT ON COLUMN contract_detail_fund.con_id IS '종목 고유번호(PK, contract.con_id 참조)';
COMMENT ON COLUMN contract_detail_fund.fund_name IS '펀드 명칭(공식명)';
COMMENT ON COLUMN contract_detail_fund.fund_family IS '펀드 운용사/패밀리 명';
COMMENT ON COLUMN contract_detail_fund.fund_type IS '펀드 유형(예: Equity, Bond, MMF)';
COMMENT ON COLUMN contract_detail_fund.fund_front_load IS '선취수수료(%)';
COMMENT ON COLUMN contract_detail_fund.fund_back_load IS '후취수수료(%)';
COMMENT ON COLUMN contract_detail_fund.fund_management_fee IS '운용보수(연 %, 또는 고정)';
COMMENT ON COLUMN contract_detail_fund.fund_minimum_initial_purchase IS '최소 최초 매입금액';
COMMENT ON COLUMN contract_detail_fund.fund_subsequent_minimum_purchase IS '추가 매입 최소금액';
COMMENT ON COLUMN contract_detail_fund.fund_closed IS '펀드 청산/폐쇄 여부';
COMMENT ON COLUMN contract_detail_fund.fund_closed_for_new_investors IS '신규 투자자 모집 중단 여부';
COMMENT ON COLUMN contract_detail_fund.fund_closed_for_new_money IS '신규 자금 모집 중단 여부';

COMMENT ON TABLE contract_detail_fx IS '외환(FX/Cash) 상세정보 테이블(자산별)';
COMMENT ON COLUMN contract_detail_fx.con_id IS '종목 고유번호(PK, contract.con_id 참조)';
COMMENT ON COLUMN contract_detail_fx.under_symbol IS '기초 통화 심볼(예: USD, EUR)';
COMMENT ON COLUMN contract_detail_fx.under_sec_type IS '자산 유형(예: CASH, FX)';

COMMENT ON TABLE contract_detail_index IS '지수(Index) 상세정보 테이블(자산별)';
COMMENT ON COLUMN contract_detail_index.con_id IS '종목 고유번호(PK, contract.con_id 참조)';
COMMENT ON COLUMN contract_detail_index.industry IS '지수의 산업분류(예: Equity, Commodity)';
COMMENT ON COLUMN contract_detail_index.category IS '지수 카테고리(예: Market, Sector 등)';
