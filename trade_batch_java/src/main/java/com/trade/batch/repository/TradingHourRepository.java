package com.trade.batch.repository;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Repository
@Slf4j
@RequiredArgsConstructor
public class TradingHourRepository {
    
    private final JdbcTemplate jdbcTemplate;
    
    /**
     * 거래시간 저장
     */
    public void saveTradingHours(String exchange, String type, String session, LocalDate tradeDate,
                                String dayOfWeek, LocalDateTime startTimeUtc, LocalDateTime endTimeUtc,
                                LocalDateTime startTimeLoc, LocalDateTime endTimeLoc,
                                String timezone, boolean isHoliday, String rawData) {
        String sql = """
            INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week,
                start_time_utc, end_time_utc, start_time_loc, end_time_loc,
                timezone, is_holiday, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (exchange, type, session, trade_date) 
            DO UPDATE SET
                day_of_week = EXCLUDED.day_of_week,
                start_time_utc = EXCLUDED.start_time_utc,
                end_time_utc = EXCLUDED.end_time_utc,
                start_time_loc = EXCLUDED.start_time_loc,
                end_time_loc = EXCLUDED.end_time_loc,
                is_holiday = EXCLUDED.is_holiday,
                raw_data = EXCLUDED.raw_data,
                created_at = CURRENT_TIMESTAMP
        """;
        
        jdbcTemplate.update(sql, exchange, type, session, tradeDate, dayOfWeek,
                startTimeUtc != null ? Timestamp.valueOf(startTimeUtc) : null,
                endTimeUtc != null ? Timestamp.valueOf(endTimeUtc) : null,
                startTimeLoc != null ? Timestamp.valueOf(startTimeLoc) : null,
                endTimeLoc != null ? Timestamp.valueOf(endTimeLoc) : null,
                timezone, isHoliday, rawData);
    }
    
    /**
     * FIX 거래시간 저장 (표준 거래시간)
     * - trade_date는 참조용 날짜로 사용 (실제로는 요일별 반복)
     * - UTC 시간 자동 계산
     */
    public void saveFixTradingHours(String exchange, String session, String dayOfWeek,
                                   LocalDateTime startTimeLoc, LocalDateTime endTimeLoc,
                                   String timezone) {
        // UTC 변환
        ZoneId zoneId = ZoneId.of(timezone);
        LocalDateTime startTimeUtc = startTimeLoc.atZone(zoneId)
            .withZoneSameInstant(ZoneOffset.UTC).toLocalDateTime();
        LocalDateTime endTimeUtc = endTimeLoc.atZone(zoneId)
            .withZoneSameInstant(ZoneOffset.UTC).toLocalDateTime();
        
        // trade_date는 2025-01-01을 기준으로 사용 (고정값)
        LocalDate referenceDate = LocalDate.of(2025, 1, 1);
        
        saveTradingHours(exchange, "FIX", session, referenceDate, dayOfWeek,
                        startTimeUtc, endTimeUtc, startTimeLoc, endTimeLoc,
                        timezone, false, null);
    }
    
    /**
     * 휴일 정보 저장 (CLOSED 세션)
     */
    public void saveHoliday(String exchange, LocalDate tradeDate, String dayOfWeek, 
                           String timezone, String rawData) {
        String sql = """
            INSERT INTO trading_hours (exchange, type, session, trade_date, day_of_week,
                timezone, is_holiday, raw_data)
            VALUES (?, '', 'CLOSED', ?, ?, ?, true, ?)
            ON CONFLICT (exchange, type, session, trade_date) 
            DO UPDATE SET
                day_of_week = EXCLUDED.day_of_week,
                is_holiday = EXCLUDED.is_holiday,
                raw_data = EXCLUDED.raw_data,
                created_at = CURRENT_TIMESTAMP
        """;
        
        jdbcTemplate.update(sql, exchange, tradeDate, dayOfWeek, timezone, rawData);
    }
    
    /**
     * 특정 거래소의 특정 날짜 거래시간 조회
     */
    public List<Map<String, Object>> getTradingHours(String exchange, LocalDate date) {
        String sql = """
            SELECT * FROM trading_hours
            WHERE exchange = ? AND trade_date = ? AND type = ''
            ORDER BY start_time_loc
        """;
        
        return jdbcTemplate.queryForList(sql, exchange, date);
    }
    
    /**
     * 특정 거래소의 FIX 거래시간 조회
     */
    public List<Map<String, Object>> getFixTradingHours(String exchange, String dayOfWeek) {
        String sql = """
            SELECT * FROM trading_hours
            WHERE exchange = ? AND type = 'FIX' AND day_of_week = ?
            ORDER BY start_time_loc
        """;
        
        return jdbcTemplate.queryForList(sql, exchange, dayOfWeek);
    }
    
    /**
     * 거래 가능 시간 조회 (DAILY 우선, FIX 차선)
     */
    public List<Map<String, Object>> getActiveTradingHours(String exchange, LocalDate date) {
        String dayOfWeek = date.getDayOfWeek().toString().substring(0, 3);
        
        // 1. 먼저 DAILY 데이터 확인
        List<Map<String, Object>> dailyHours = getTradingHours(exchange, date);
        if (!dailyHours.isEmpty()) {
            return dailyHours;
        }
        
        // 2. DAILY가 없으면 FIX 데이터 사용
        return getFixTradingHours(exchange, dayOfWeek);
    }
    
    /**
     * 특정 날짜가 휴일인지 확인
     */
    public boolean isHoliday(String exchange, LocalDate date) {
        String sql = """
            SELECT COUNT(*) FROM trading_hours
            WHERE exchange = ? AND trade_date = ? AND is_holiday = true
        """;
        
        Integer count = jdbcTemplate.queryForObject(sql, Integer.class, exchange, date);
        return count != null && count > 0;
    }
    
    /**
     * 날짜 범위의 거래시간 조회
     */
    public List<Map<String, Object>> getTradingHoursRange(String exchange, LocalDate startDate, LocalDate endDate) {
        String sql = """
            SELECT * FROM trading_hours
            WHERE exchange = ? AND trade_date BETWEEN ? AND ? AND type = ''
            ORDER BY trade_date, start_time_loc
        """;
        
        return jdbcTemplate.queryForList(sql, exchange, startDate, endDate);
    }
    
    /**
     * 오래된 데이터 삭제 (3개월 이상)
     */
    public int cleanupOldData(LocalDate cutoffDate) {
        String sql = """
            DELETE FROM trading_hours
            WHERE type = '' AND trade_date < ?
        """;
        
        return jdbcTemplate.update(sql, cutoffDate);
    }
    
    /**
     * 모든 거래소 목록 조회
     */
    public List<String> getAllExchanges() {
        String sql = """
            SELECT DISTINCT exchange FROM trading_hours
            WHERE type = 'FIX'
            ORDER BY exchange
        """;
        
        return jdbcTemplate.queryForList(sql, String.class);
    }
    
    /**
     * 특정 거래소가 점심시간이 있는지 확인
     */
    public boolean hasLunchBreak(String exchange) {
        String sql = """
            SELECT COUNT(*) FROM trading_hours
            WHERE exchange = ? AND type = 'FIX' AND session IN ('MORNING', 'AFTERNOON')
        """;
        
        Integer count = jdbcTemplate.queryForObject(sql, Integer.class, exchange);
        return count != null && count > 0;
    }
    
    /**
     * 거래 가능 여부 확인
     */
    public boolean isTradingDay(String exchange, LocalDate date) {
        // 1. 먼저 DAILY 데이터에서 휴일 확인
        String sql = """
            SELECT COUNT(*) FROM trading_hours
            WHERE exchange = ? AND trade_date = ? AND type = '' 
            AND (is_holiday = true OR session = 'CLOSED')
        """;
        
        Integer holidayCount = jdbcTemplate.queryForObject(sql, Integer.class, exchange, date);
        if (holidayCount != null && holidayCount > 0) {
            return false; // 휴일임
        }
        
        // 2. DAILY 거래시간 데이터 확인
        sql = """
            SELECT COUNT(*) FROM trading_hours
            WHERE exchange = ? AND trade_date = ? AND type = '' 
            AND is_holiday = false AND session != 'CLOSED'
        """;
        
        Integer count = jdbcTemplate.queryForObject(sql, Integer.class, exchange, date);
        if (count != null && count > 0) {
            return true;
        }
        
        // 3. DAILY 데이터가 없으면 FIX 데이터로 확인 (주말 제외)
        DayOfWeek dow = date.getDayOfWeek();
        if (dow == DayOfWeek.SATURDAY || dow == DayOfWeek.SUNDAY) {
            // 주말인데 FIX에 데이터가 있는지 확인
            String dayOfWeek = dow.toString().substring(0, 3);
            sql = """
                SELECT COUNT(*) FROM trading_hours
                WHERE exchange = ? AND type = 'FIX' AND day_of_week = ?
            """;
            Integer fixCount = jdbcTemplate.queryForObject(sql, Integer.class, exchange, dayOfWeek);
            return fixCount != null && fixCount > 0;
        }
        
        return true; // 평일은 기본적으로 거래일로 간주
    }
}