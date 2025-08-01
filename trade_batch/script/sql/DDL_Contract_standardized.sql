-- 표준화된 Contract DDL
-- 테이블명: contracts (복수형)
-- 필드명: snake_case, right_type 사용

CREATE TABLE contracts (
    con_id                  INTEGER      PRIMARY KEY,
    symbol                  VARCHAR(16)  NOT NULL,
    sec_type                VARCHAR(8)   NOT NULL,
    last_trade_date_or_contract_month VARCHAR(16),
    crt_month_con_id        INTEGER,
    last_trade_date         VARCHAR(16),
    strike                  DECIMAL(15,8),
    right_type              VARCHAR(2),   -- 변경: right_ → right_type
    multiplier              VARCHAR(8),
    exchange                VARCHAR(16)  NOT NULL,
    primary_exchange        VARCHAR(16),  -- 변경: primary_exch → primary_exchange
    currency                VARCHAR(8)   NOT NULL,
    local_symbol            VARCHAR(32),
    trading_class           VARCHAR(16),
    sec_id_type             VARCHAR(16),
    sec_id                  VARCHAR(32),
    description             VARCHAR(256), -- 통일된 길이
    issuer_id               VARCHAR(32),
    delta_neutral_conid     INTEGER,
    include_expired         BOOLEAN DEFAULT FALSE
);

CREATE TABLE con_x_data (
    contract      VARCHAR(16) NOT NULL,  -- 변경: symbol → contract
    exchange      VARCHAR(16) NOT NULL,
    data_type     VARCHAR(8) NOT NULL,
    size          DECIMAL(16,4),
    stt_date_loc  TIMESTAMP NOT NULL,
    end_date_loc  TIMESTAMP NOT NULL,
    row_count     BIGINT,
    data_status   VARCHAR(16),
    last_update   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contract, exchange, data_type, size)
);

CREATE TABLE contract_details (
    con_id               INTEGER PRIMARY KEY REFERENCES contracts(con_id),
    market_name         VARCHAR(32),
    min_tick            DECIMAL(10,4),
    price_magnifier     INTEGER,
    order_types         VARCHAR(256),
    valid_exchanges     VARCHAR(256),
    desc                VARCHAR(256),    -- 변경: long_name → desc
    time_zone_id        VARCHAR(64),
    trading_hours       VARCHAR(256),
    liquid_hours        VARCHAR(256),
    agg_group           INTEGER,
    market_rule_ids     VARCHAR(128),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 주종별 상세 테이블들
CREATE TABLE contract_details_stock (
    con_id        INTEGER PRIMARY KEY REFERENCES contracts(con_id),
    industry      VARCHAR(64),
    category      VARCHAR(64),
    subcategory   VARCHAR(64),
    stock_type    VARCHAR(32),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contract_details_future (
    con_id                  INTEGER PRIMARY KEY REFERENCES contracts(con_id),
    contract_month          VARCHAR(8),
    real_expiration_date    DATE,
    last_trade_time         VARCHAR(32),
    ev_rule                 VARCHAR(50),
    ev_multiplier           DECIMAL(10,4),
    under_conid             INTEGER,
    under_symbol            VARCHAR(16),
    under_sec_type          VARCHAR(10),
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contract_details_option (
    con_id                  INTEGER PRIMARY KEY REFERENCES contracts(con_id),
    option_type             VARCHAR(4),    -- CALL, PUT
    strike                  DECIMAL(15,4),
    expiry_date             DATE,
    multiplier              INTEGER,
    underlying_con_id       INTEGER,
    underlying_symbol       VARCHAR(16),
    exercise_style          VARCHAR(10),   -- AMERICAN, EUROPEAN
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contract_details_index (
    con_id        INTEGER PRIMARY KEY REFERENCES contracts(con_id),
    index_family  VARCHAR(50),
    index_type    VARCHAR(50),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_contracts_symbol ON contracts(symbol);
CREATE INDEX idx_contracts_exchange ON contracts(exchange);
CREATE INDEX idx_contracts_sec_type ON contracts(sec_type);
CREATE INDEX idx_con_x_data_contract ON con_x_data(contract);
CREATE INDEX idx_con_x_data_exchange ON con_x_data(exchange);