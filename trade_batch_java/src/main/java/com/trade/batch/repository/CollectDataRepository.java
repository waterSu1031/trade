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
        String sql = "SELECT exchange, timezone FROM exchanges";
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public List<Map<String, Object>> selectSymbolFromAddCSV() {
        String sql = """
            SELECT sfc.*
              FROM symbol_import sfc
             WHERE NOT EXISTS (
                   SELECT 1 FROM contracts s
                    WHERE s.exchange = sfc.exchange
                      AND s.symbol = sfc.symbol
                      AND s.sectype = sfc.sec_type
                      AND s.currency = sfc.currency
               )
        """;
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public List<Map<String, Object>> selectSymbolFromFullCSV() {
        String sql = """
            SELECT sfc.*
              FROM symbol_import sfc
        """;
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public void insertExcXCon(Map<String, Object> row) {
        String sql = """
            INSERT INTO exc_x_con (exchange, symbol)
            VALUES (:exchange, :symbol)
        """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertConXData(Map<String, Object> row) {
        String sql = """
            INSERT INTO con_x_data (contract, exchange, data_type, size, stt_date_loc, end_date_loc, row_count, data_status)
            VALUES (:contract, :exchange, :data_type, :size, :stt_date_loc, :end_date_loc, :row_count, :data_status)
            ON CONFLICT(contract, exchange, data_type, size) DO UPDATE SET
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
            INSERT INTO contracts (
                conid, symbol, sectype, lasttradedateorcontractmonth, 
                strike, right, multiplier, exchange, primaryexchange, currency,
                localsymbol, tradingclass, description
            ) VALUES (
                :conid, :symbol, :sectype, :lasttradedateorcontractmonth,
                :strike, :right, :multiplier, :exchange, :primaryexchange, :currency,
                :localsymbol, :tradingclass, :description
            )
            ON CONFLICT(conid)
            DO UPDATE SET
                symbol = EXCLUDED.symbol,
                sectype = EXCLUDED.sectype,
                lasttradedateorcontractmonth = EXCLUDED.lasttradedateorcontractmonth,
                strike = EXCLUDED.strike,
                right = EXCLUDED.right,
                multiplier = EXCLUDED.multiplier,
                exchange = EXCLUDED.exchange,
                primaryexchange = EXCLUDED.primaryexchange,
                currency = EXCLUDED.currency,
                localsymbol = EXCLUDED.localsymbol,
                tradingclass = EXCLUDED.tradingclass,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP;
        """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertContractDetail(Map<String, Object> row) {
        String sql = """
                INSERT INTO contract_details (
                    con_id, market_name, min_tick, price_magnifier,
                    order_types, valid_exchanges, desc,
                    time_zone_id, trading_hours, liquid_hours,
                    agg_group, market_rule_ids
                ) VALUES (
                    :con_id, :market_name, :min_tick, :price_magnifier,
                    :order_types, :valid_exchanges, :desc,
                    :time_zone_id, :trading_hours, :liquid_hours,
                    :agg_group, :market_rule_ids
                )
                ON CONFLICT(con_id)
                DO UPDATE SET
                    market_name = EXCLUDED.market_name,
                    min_tick = EXCLUDED.min_tick,
                    price_magnifier = EXCLUDED.price_magnifier,
                    order_types = EXCLUDED.order_types,
                    valid_exchanges = EXCLUDED.valid_exchanges,
                    desc = EXCLUDED.desc,
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
                INSERT INTO contract_details_stock (
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
                INSERT INTO contract_details_future (
                    con_id, contract_month, last_trade_date, multiplier,
                    ev_rule, ev_multiplier, underlying_con_id, expiry_date
                ) VALUES (
                    :con_id, :contract_month, :last_trade_date, :multiplier,
                    :ev_rule, :ev_multiplier, :underlying_con_id, :expiry_date
                )
                ON CONFLICT(con_id)
                DO UPDATE SET
                    contract_month = EXCLUDED.contract_month,
                    last_trade_date = EXCLUDED.last_trade_date,
                    multiplier = EXCLUDED.multiplier,
                    ev_rule = EXCLUDED.ev_rule,
                    ev_multiplier = EXCLUDED.ev_multiplier,
                    underlying_con_id = EXCLUDED.underlying_con_id,
                    expiry_date = EXCLUDED.expiry_date;
                """;
        namedJdbcTemplate.update(sql, row);
    }

    public void upsertContractDetailOption(Map<String, Object> row) {
        String sql = """
                INSERT INTO contract_details_option (
                    con_id, option_type, strike, expiry_date,
                    multiplier, underlying_con_id, underlying_symbol, exercise_style
                ) VALUES (
                    :con_id, :option_type, :strike, :expiry_date,
                    :multiplier, :underlying_con_id, :underlying_symbol, :exercise_style
                )
                ON CONFLICT(con_id)
                DO UPDATE SET
                    option_type = EXCLUDED.option_type,
                    strike = EXCLUDED.strike,
                    expiry_date = EXCLUDED.expiry_date,
                    multiplier = EXCLUDED.multiplier,
                    underlying_con_id = EXCLUDED.underlying_con_id,
                    underlying_symbol = EXCLUDED.underlying_symbol,
                    exercise_style = EXCLUDED.exercise_style;
                """;
        namedJdbcTemplate.update(sql, row);
    }

    // Bond, Fund, FX 관련 메서드는 현재 필요하지 않으므로 제거됨

    public void upsertContractDetailIndex(Map<String, Object> row) {
        String sql = """
                INSERT INTO contract_details_index (
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
                SELECT * FROM contracts
                WHERE sectype = 'CONTFUT'
                AND lasttradedateorcontractmonth IS NOT NULL
                AND lasttradedateorcontractmonth <> ''
                AND CURRENT_DATE BETWEEN TO_DATE(lasttradedateorcontractmonth, 'YYYYMMDD') - INTERVAL '7 day' AND TO_DATE(lasttradedateorcontractmonth, 'YYYYMMDD')
                """;
        return namedJdbcTemplate.queryForList(sql, Map.of());
    }

    public void upsertNextFutureMonth(Map<String, Object> row) {
        String sql = """
            UPDATE contracts SET
                lasttradedateorcontractmonth = :lasttradedateorcontractmonth
            WHERE conid = :conid
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
            WHERE contract = :contract AND exchange = :exchange AND data_type = :data_type
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
        String sql = "SELECT * FROM contracts";
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
