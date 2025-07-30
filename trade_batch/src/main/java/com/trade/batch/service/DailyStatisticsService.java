package com.trade.batch.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 일별 통계 집계 서비스
 * - trade_events에서 통계 집계
 * - daily_statistics 테이블 관리
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DailyStatisticsService {

    private final JdbcTemplate jdbcTemplate;

    /**
     * 집계할 날짜 목록 조회
     * - 아직 집계되지 않은 날짜
     * - 최근 7일간 재집계
     */
    public List<Map<String, Object>> findDatesToAggregate() {
        String sql = """
            WITH trade_dates AS (
                SELECT DISTINCT DATE(time) as trade_date
                FROM trade_events
                WHERE time >= CURRENT_DATE - INTERVAL '30 days'
            ),
            existing_stats AS (
                SELECT DISTINCT date
                FROM daily_statistics
                WHERE date >= CURRENT_DATE - INTERVAL '30 days'
            )
            SELECT t.trade_date
            FROM trade_dates t
            LEFT JOIN existing_stats s ON t.trade_date = s.date
            WHERE s.date IS NULL
               OR t.trade_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY t.trade_date
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 특정 날짜의 거래 통계 집계
     */
    @Transactional(readOnly = true)
    public Map<String, Object> aggregateDailyStatistics(LocalDate tradeDate) {
        Map<String, Object> stats = new HashMap<>();
        stats.put("date", tradeDate);
        
        // 기본 거래 통계
        String tradeSql = """
            SELECT 
                COUNT(DISTINCT execId) as totalTrades,
                SUM(shares) as totalVolume,
                SUM(CASE WHEN realizedPNL > 0 THEN realizedPNL ELSE 0 END) as grossProfit,
                SUM(CASE WHEN realizedPNL < 0 THEN realizedPNL ELSE 0 END) as grossLoss,
                SUM(realizedPNL) as netPnl,
                SUM(commission) as totalCommission,
                COUNT(DISTINCT CASE WHEN realizedPNL > 0 THEN execId END) as winTrades,
                COUNT(DISTINCT CASE WHEN realizedPNL < 0 THEN execId END) as lossTrades,
                COUNT(DISTINCT symbol) as tradedSymbols,
                COUNT(DISTINCT secType) as tradedSecTypes
            FROM trade_events
            WHERE DATE(time) = ?
        """;
        
        Map<String, Object> tradeStats = jdbcTemplate.queryForMap(tradeSql, tradeDate);
        stats.putAll(tradeStats);
        
        // secType별 통계 (가장 많이 거래된 타입)
        String secTypeSql = """
            SELECT secType, COUNT(*) as cnt
            FROM trade_events
            WHERE DATE(time) = ?
            GROUP BY secType
            ORDER BY cnt DESC
            LIMIT 1
        """;
        
        try {
            Map<String, Object> secTypeStats = jdbcTemplate.queryForMap(secTypeSql, tradeDate);
            stats.put("secType", secTypeStats.get("secType"));
        } catch (Exception e) {
            stats.put("secType", "MIXED");
        }
        
        // 총 PnL 계산
        Double grossPnl = ((Number) stats.getOrDefault("grossProfit", 0)).doubleValue() + 
                         ((Number) stats.getOrDefault("grossLoss", 0)).doubleValue();
        Double commission = ((Number) stats.getOrDefault("totalCommission", 0)).doubleValue();
        stats.put("grossPnl", grossPnl);
        stats.put("netPnl", grossPnl - commission);
        
        return stats;
    }

    /**
     * 일별 통계 저장
     */
    @Transactional
    public void saveDailyStatistics(Map<String, Object> statistics) {
        // UPSERT (있으면 업데이트, 없으면 삽입)
        String sql = """
            INSERT INTO daily_statistics (
                date, secType, totalTrades, totalVolume,
                grossPnl, netPnl, commission,
                winTrades, lossTrades, winRate, profitFactor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (date, secType) 
            DO UPDATE SET
                totalTrades = EXCLUDED.totalTrades,
                totalVolume = EXCLUDED.totalVolume,
                grossPnl = EXCLUDED.grossPnl,
                netPnl = EXCLUDED.netPnl,
                commission = EXCLUDED.commission,
                winTrades = EXCLUDED.winTrades,
                lossTrades = EXCLUDED.lossTrades,
                winRate = EXCLUDED.winRate,
                profitFactor = EXCLUDED.profitFactor,
                created_at = CURRENT_TIMESTAMP
        """;
        
        jdbcTemplate.update(sql,
            statistics.get("date"),
            statistics.getOrDefault("secType", "ALL"),
            statistics.get("totalTrades"),
            statistics.get("totalVolume"),
            statistics.get("grossPnl"),
            statistics.get("netPnl"),
            statistics.get("totalCommission"),
            statistics.get("winTrades"),
            statistics.get("lossTrades"),
            statistics.get("win_rate"),
            statistics.get("profit_factor")
        );
    }

    /**
     * 활성 종목 목록 조회
     */
    public List<Map<String, Object>> findActiveSymbols() {
        String sql = """
            SELECT DISTINCT 
                symbol,
                COUNT(*) as trade_count,
                MAX(time) as last_trade_time
            FROM trade_events
            WHERE time >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY symbol
            HAVING COUNT(*) >= 5  -- 최소 5번 이상 거래된 종목
            ORDER BY trade_count DESC
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 종목별 통계 집계
     */
    @Transactional(readOnly = true)
    public Map<String, Object> aggregateSymbolStatistics(String symbol) {
        Map<String, Object> stats = new HashMap<>();
        stats.put("symbol", symbol);
        stats.put("date", LocalDate.now());
        
        // 종목별 거래 통계
        String sql = """
            WITH symbol_trades AS (
                SELECT 
                    time,
                    shares,
                    price,
                    side,
                    realizedPNL,
                    commission
                FROM trade_events
                WHERE symbol = ?
                AND time >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY time
            ),
            daily_returns AS (
                SELECT 
                    DATE(time) as trade_date,
                    SUM(realizedPNL) as daily_pnl,
                    SUM(shares * price * CASE WHEN side = 'BOT' THEN 1 ELSE -1 END) as daily_volume
                FROM symbol_trades
                GROUP BY DATE(time)
            )
            SELECT 
                COUNT(DISTINCT DATE(time)) as trading_days,
                COUNT(*) as total_trades,
                AVG(daily_pnl) as avg_daily_pnl,
                STDDEV(daily_pnl) as pnl_stddev,
                MAX(daily_pnl) as max_daily_gain,
                MIN(daily_pnl) as max_daily_loss,
                SUM(shares) as total_volume,
                SUM(realizedPNL) as total_pnl,
                SUM(commission) as total_commission
            FROM symbol_trades, daily_returns
        """;
        
        try {
            Map<String, Object> symbolStats = jdbcTemplate.queryForMap(sql, symbol);
            stats.putAll(symbolStats);
            
            // 추가 계산
            Double avgReturn = ((Number) stats.getOrDefault("avg_daily_pnl", 0)).doubleValue();
            Double stdDev = ((Number) stats.getOrDefault("pnl_stddev", 0)).doubleValue();
            stats.put("avgReturn", avgReturn);
            stats.put("stdDev", stdDev);
            
        } catch (Exception e) {
            log.error("종목 통계 집계 실패: {}", symbol, e);
        }
        
        return stats;
    }

    /**
     * 종목별 통계 저장
     */
    @Transactional
    public void saveSymbolStatistics(Map<String, Object> symbolStats) {
        // 종목별 통계는 별도 테이블에 저장하거나
        // daily_statistics에 종목별로 저장 가능
        log.debug("종목별 통계 저장: {}", symbolStats);
    }

    /**
     * 포트폴리오 메트릭 계산
     */
    @Transactional(readOnly = true)
    public Map<String, Object> calculatePortfolioMetrics() {
        Map<String, Object> metrics = new HashMap<>();
        
        // 전체 포트폴리오 성과
        String portfolioSql = """
            WITH daily_performance AS (
                SELECT 
                    DATE(time) as trade_date,
                    SUM(realizedPNL) as daily_pnl,
                    SUM(shares * price * CASE WHEN side = 'BOT' THEN 1 ELSE -1 END) as daily_invested
                FROM trade_events
                WHERE time >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY DATE(time)
            ),
            cumulative_performance AS (
                SELECT 
                    trade_date,
                    daily_pnl,
                    daily_invested,
                    SUM(daily_pnl) OVER (ORDER BY trade_date) as cumulative_pnl,
                    SUM(daily_invested) OVER (ORDER BY trade_date) as cumulative_invested
                FROM daily_performance
            )
            SELECT 
                COUNT(DISTINCT trade_date) as trading_days,
                SUM(daily_pnl) as total_pnl,
                AVG(daily_pnl) as avg_daily_pnl,
                STDDEV(daily_pnl) as daily_volatility,
                MAX(cumulative_pnl) as peak_pnl,
                MIN(cumulative_pnl - LAG(MAX(cumulative_pnl) OVER (ORDER BY trade_date)) OVER (ORDER BY trade_date)) as max_drawdown
            FROM cumulative_performance
        """;
        
        try {
            Map<String, Object> performance = jdbcTemplate.queryForMap(portfolioSql);
            metrics.putAll(performance);
            
            // 현재 포지션 가치
            String positionSql = """
                SELECT 
                    COUNT(DISTINCT symbol) as active_positions,
                    SUM(position * avgCost) as total_position_value
                FROM (
                    SELECT 
                        symbol,
                        SUM(CASE WHEN side = 'BOT' THEN shares ELSE -shares END) as position,
                        AVG(CASE WHEN side = 'BOT' THEN price END) as avgCost
                    FROM trade_events
                    GROUP BY symbol
                    HAVING SUM(CASE WHEN side = 'BOT' THEN shares ELSE -shares END) != 0
                ) current_positions
            """;
            
            Map<String, Object> positions = jdbcTemplate.queryForMap(positionSql);
            metrics.putAll(positions);
            
        } catch (Exception e) {
            log.error("포트폴리오 메트릭 계산 실패", e);
        }
        
        return metrics;
    }

    /**
     * 포트폴리오 메트릭 저장
     */
    @Transactional
    public void savePortfolioMetrics(Map<String, Object> metrics) {
        // performance_metrics 테이블이나 별도 저장소에 저장
        log.info("포트폴리오 메트릭 저장: Total PnL: {}, Volatility: {}", 
            metrics.get("total_pnl"), 
            metrics.get("daily_volatility"));
    }
}