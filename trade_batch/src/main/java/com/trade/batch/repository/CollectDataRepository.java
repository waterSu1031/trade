package com.trade.batch.repository;

import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.List;
import java.util.Map;

@Repository
public class CollectDataRepository {

    private final NamedParameterJdbcTemplate namedJdbcTemplate;

    @Autowired
    public CollectDataRepository(NamedParameterJdbcTemplate namedJdbcTemplate) {
        this.namedJdbcTemplate = namedJdbcTemplate;
    }

    public List<Map<String, Object>> selectExchangeTimeZone() {
        String sql = "SELECT exchange, timezone FROM exchange";
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public List<Map<String, Object>> selectSymbolFromAddCSV() {
        String sql = """
            SELECT sfc.*
              FROM symbol_from_csv sfc
             WHERE NOT EXISTS (
                   SELECT 1 FROM contract s
                    WHERE s.exchange = sfc.exchange
                      AND s.symbol = sfc.symbol
                      AND s.sec_type = sfc.sec_type
                      AND s.currency = sfc.currency
               )
        """;
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public List<Map<String, Object>> selectSymbolFromFullCSV() {
        String sql = """
            SELECT sfc.*
              FROM symbol_from_csv sfc
        """;
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public void insertExcXSym(Map<String, Object> row) {
        String sql = """
            INSERT INTO exc_x_sym (exchange, symbol)
            VALUES (:exchange, :symbol)
        """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertSymXData(Map<String, Object> row) {
        String sql = """
            INSERT INTO sym_x_data (symbol, exchange, data_type, size, stt_date_loc, end_date_loc, row_count, data_status)
            VALUES (:symbol, :exchange, :data_type, :size, :stt_date_loc, :end_date_loc, :row_count, :data_status)
            ON CONFLICT(symbol, exchange, data_type, size) DO UPDATE SET
                stt_date_loc = EXCLUDED.stt_date_loc,
                end_date_loc = EXCLUDED.end_date_loc,
                row_count = EXCLUDED.row_count,
                data_status = EXCLUDED.data_status,
                last_update = CURRENT_TIMESTAMP
        """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertContract(Map<String, Object> row) {
        String sql = """
            INSERT INTO contract (
                con_id, symbol, sec_type, last_trade_date_or_contract_month, last_trade_date,
                strike, right_, multiplier, exchange, primary_exch, currency,
                local_symbol, trading_class, sec_id_type, sec_id,
                description, issuer_id, delta_neutral_conid,
                include_expired, combo_legs_descrip
            ) VALUES (
                :con_id, :symbol, :sec_type, :last_trade_date_or_contract_month, :last_trade_date,
                :strike, :right_, :multiplier, :exchange, :primary_exch, :currency,
                :local_symbol, :trading_class, :sec_id_type, :sec_id,
                :description, :issuer_id, :delta_neutral_conid,
                :include_expired, :combo_legs_descrip
            )
            ON CONFLICT(con_id)
            DO UPDATE SET
                symbol = EXCLUDED.symbol,
                sec_type = EXCLUDED.sec_type,
                last_trade_date_or_contract_month = EXCLUDED.last_trade_date_or_contract_month,
                last_trade_date = EXCLUDED.last_trade_date,
                strike = EXCLUDED.strike,
                right_ = EXCLUDED.right_,
                multiplier = EXCLUDED.multiplier,
                exchange = EXCLUDED.exchange,
                primary_exch = EXCLUDED.primary_exch,
                currency = EXCLUDED.currency,
                local_symbol = EXCLUDED.local_symbol,
                trading_class = EXCLUDED.trading_class,
                sec_id_type = EXCLUDED.sec_id_type,
                sec_id = EXCLUDED.sec_id,
                description = EXCLUDED.description,
                issuer_id = EXCLUDED.issuer_id,
                delta_neutral_conid = EXCLUDED.delta_neutral_conid,
                include_expired = EXCLUDED.include_expired,
                combo_legs_descrip = EXCLUDED.combo_legs_descrip;
        """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertContractDetail(Map<String, Object> row) {
        String sql = """
                INSERT INTO contract_detail (
                    conid, market_name, min_tick, price_magnifier,
                    order_types, valid_exchanges, long_name,
                    time_zone_id, trading_hours, liquid_hours,
                    agg_group, market_rule_ids
                ) VALUES (
                    :conid, :market_name, :min_tick, :price_magnifier,
                    :order_types, :valid_exchanges, :long_name,
                    :time_zone_id, :trading_hours, :liquid_hours,
                    :agg_group, :market_rule_ids
                )
                ON CONFLICT(conid)
                DO UPDATE SET
                    market_name = EXCLUDED.market_name,
                    min_tick = EXCLUDED.min_tick,
                    price_magnifier = EXCLUDED.price_magnifier,
                    order_types = EXCLUDED.order_types,
                    valid_exchanges = EXCLUDED.valid_exchanges,
                    long_name = EXCLUDED.long_name,
                    time_zone_id = EXCLUDED.time_zone_id,
                    trading_hours = EXCLUDED.trading_hours,
                    liquid_hours = EXCLUDED.liquid_hours,
                    agg_group = EXCLUDED.agg_group,
                    market_rule_ids = EXCLUDED.market_rule_ids;
                """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertContractDetailStock(Map<String, Object> row) {
        String sql = """
                INSERT INTO contract_detail_stock (
                    con_id, industry, category, subcategory, stock_type
                ) VALUES (
                    :con_id, :industry, :category, :subcategory, :stock_type
                )
                ON CONFLICT(con_id)
                DO UPDATE SET
                    industry = EXCLUDED.industry,
                    category = EXCLUDED.category,
                    subcategory = EXCLUDED.subcategory,
                    stock_type = EXCLUDED.stock_type;
                """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertContractDetailFuture(Map<String, Object> row) {
        String sql = """
                INSERT INTO contract_detail_future (
                    con_id, contract_month, real_expiration_date, last_trade_time,
                    ev_rule, ev_multiplier, under_conid, under_symbol, under_sec_type
                ) VALUES (
                    :con_id, :contract_month, :real_expiration_date, :last_trade_time,
                    :ev_rule, :ev_multiplier, :under_conid, :under_symbol, :under_sec_type
                )
                ON CONFLICT(con_id)
                DO UPDATE SET
                    contract_month = EXCLUDED.contract_month,
                    real_expiration_date = EXCLUDED.real_expiration_date,
                    last_trade_time = EXCLUDED.last_trade_time,
                    ev_rule = EXCLUDED.ev_rule,
                    ev_multiplier = EXCLUDED.ev_multiplier,
                    under_conid = EXCLUDED.under_conid,
                    under_symbol = EXCLUDED.under_symbol,
                    under_sec_type = EXCLUDED.under_sec_type;
                """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertContractDetailOption(Map<String, Object> row) {
        String sql = """
                INSERT INTO contract_detail_option (
                    con_id, contract_month, real_expiration_date, last_trade_time,
                    ev_rule, ev_multiplier, under_conid, under_symbol, under_sec_type
                ) VALUES (
                    :con_id, :contract_month, :real_expiration_date, :last_trade_time,
                    :ev_rule, :ev_multiplier, :under_conid, :under_symbol, :under_sec_type
                )
                ON CONFLICT(con_id)
                DO UPDATE SET
                    contract_month = EXCLUDED.contract_month,
                    real_expiration_date = EXCLUDED.real_expiration_date,
                    last_trade_time = EXCLUDED.last_trade_time,
                    ev_rule = EXCLUDED.ev_rule,
                    ev_multiplier = EXCLUDED.ev_multiplier,
                    under_conid = EXCLUDED.under_conid,
                    under_symbol = EXCLUDED.under_symbol,
                    under_sec_type = EXCLUDED.under_sec_type;
                """;
        namedJdbcTemplate.update(sql, row);
    }

    // Bond, Fund, FX 관련 메서드는 현재 필요하지 않으므로 제거됨

    public void upsertContractDetailIndex(Map<String, Object> row) {
        String sql = """
                INSERT INTO contract_detail_index (
                    con_id, industry, category
                ) VALUES (
                    :con_id, :industry, :category
                )
                ON CONFLICT(con_id)
                DO UPDATE SET
                    industry = EXCLUDED.industry,
                    category = EXCLUDED.category;
                """;
        namedJdbcTemplate.update(sql, row);
    }

    // --------------------------------------------------------------------------------------

    public List<Map<String, Object>> selectFutureMonthForNext() {
        String sql = """
                SELECT * FROM contract
                WHERE sec_type = 'CONTFUT'
                AND last_trade_date IS NOT NULL
                AND last_trade_date <> ''
                AND CURRENT_DATE BETWEEN TO_DATE(last_trade_date, 'YYYYMMDD') - INTERVAL '7 day' AND TO_DATE(last_trade_date, 'YYYYMMDD')
                """;
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public void upsertNextFutureMonth(Map<String, Object> row) {
        String sql = """
            UPDATE contract SET
                crt_month_con_id = :crt_month_con_id,
                last_trade_date = :last_trade_date
            WHERE con_id = :con_id";
        """;
        namedJdbcTemplate.update(sql, row);
    }

    // --------------------------------------------------------------------------------------

    public List<Map<String, Object>> selectContractForCollectTime() {
        String sql = """
                SELECT * FROM con_x_data
                WHERE data_status != 'COMPLETE'
                AND data_type = '1m'
                """;
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public void insertTimeData(Map<String,Object> row) {
        String sql = """
            INSERT INTO price_time (symbol, exchange, utc, loc, open, high, low, close, volume, count, vwap)
            VALUES (:symbol, :exchange, :utc, :loc, :open, :high, :low, :close, :volume, :count, :vwap)
            """;
        namedJdbcTemplate.update(sql, row);
    }

    public void updateStatus(Map<String,Object> row) {
        String sql = """
            UPDATE con_x_data
            SET data_status = :data_status
            WHERE symbol = :symbol AND exchange = :exchange AND data_type = :data_type
            """;
        namedJdbcTemplate.update(sql, row);
    }

    public List<Map<String, Object>> selectContractsForConvertRange() {
        String sql = """
                SELECT * FROM con_x_data 
                WHERE 1=1
                """;
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public List<Map<String,Object>> selectTimeData(Map<String,Object> param) {
        String sql = """
                SELECT * FROM price_time
                WHERE symbol = :symbol
                """;
        return namedJdbcTemplate.queryForList(sql, param);
    }

    public void insertRangeData(Map<String,Object> row) {
        String sql = """
            INSERT INTO price_range (symbol, exchange, utc, loc, range_size, idx, open, high, low, close, vol, cnt, vwap)
            VALUES (:symbol, :exchange, :utc, :loc, :range_size, :idx, :open, :high, :low, :close, :vol, :cnt, :vwap)
        """;
        namedJdbcTemplate.update(sql, row);
    }



    public List<Map<String, Object>> selectContractsForConvertVolume() {
        String sql = "SELECT * FROM contract";
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public void insertVolumeData(Map<String,Object> row) {
        String sql = """
            INSERT INTO price_volume(symbol, exchange, utc, loc, vol_size, idx, open, high, low, close, vol, cnt, vwap) 
            VALUES (:symbol, :exchange, :utc, :loc, :vol_size, :idx, :open, :high, :low, :close, :vol, :cnt, :vwap)
            """;
        namedJdbcTemplate.update(sql, row);
    }


}
