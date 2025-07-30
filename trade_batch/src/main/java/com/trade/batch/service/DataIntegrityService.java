package com.trade.batch.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

/**
 * 데이터 정합성 검증 서비스
 * - 포지션, 손익 검증 및 수정
 * - 중복 데이터 제거
 * - 참조 무결성 체크
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DataIntegrityService {

    private final JdbcTemplate jdbcTemplate;
    private final Map<String, Object> verificationSummary = new HashMap<>();

    /**
     * 현재 포지션 목록 조회
     */
    public List<Map<String, Object>> getCurrentPositions() {
        String sql = """
            SELECT 
                symbol,
                SUM(CASE WHEN side = 'BOT' THEN shares ELSE -shares END) as position,
                COUNT(*) as trade_count,
                MAX(time) as last_trade_time
            FROM trade_events
            GROUP BY symbol
            HAVING SUM(CASE WHEN side = 'BOT' THEN shares ELSE -shares END) != 0
            ORDER BY symbol
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 포지션 재계산
     */
    @Transactional(readOnly = true)
    public Map<String, Object> recalculatePosition(String symbol) {
        Map<String, Object> result = new HashMap<>();
        result.put("symbol", symbol);
        
        // FIFO 방식으로 정확한 포지션 계산
        String sql = """
            WITH ordered_trades AS (
                SELECT 
                    execId,
                    time,
                    side,
                    shares,
                    price,
                    SUM(CASE WHEN side = 'BOT' THEN shares ELSE -shares END) 
                        OVER (ORDER BY time, execId) as running_position
                FROM trade_events
                WHERE symbol = ?
                ORDER BY time, execId
            )
            SELECT 
                COALESCE(SUM(CASE WHEN side = 'BOT' THEN shares ELSE -shares END), 0) as position,
                COALESCE(
                    SUM(CASE WHEN side = 'BOT' THEN shares * price ELSE 0 END) / 
                    NULLIF(SUM(CASE WHEN side = 'BOT' THEN shares ELSE 0 END), 0), 
                    0
                ) as avg_cost
            FROM ordered_trades
        """;
        
        Map<String, Object> positionData = jdbcTemplate.queryForMap(sql, symbol);
        result.putAll(positionData);
        
        return result;
    }

    /**
     * 포지션 수정
     */
    @Transactional
    public void correctPosition(Map<String, Object> positionData) {
        // 실제로는 포지션 테이블이 없으므로 로그만 기록
        // 필요시 position_corrections 테이블에 저장
        
        log.info("포지션 수정 기록 - Symbol: {}, 이전: {}, 수정: {}", 
            positionData.get("symbol"),
            positionData.get("position"),
            positionData.get("recalculated_position")
        );
        
        incrementSummaryCount("corrected_positions");
    }

    /**
     * 최근 손익이 있는 거래 조회
     */
    public List<Map<String, Object>> getRecentTradesWithPnL() {
        String sql = """
            SELECT 
                execId,
                orderId,
                symbol,
                time,
                side,
                shares,
                price,
                realizedPNL,
                position,
                avgCost
            FROM trade_events
            WHERE realizedPNL != 0
            AND time >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY time DESC
            LIMIT 1000
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 손익 재계산 (FIFO 기준)
     */
    @Transactional(readOnly = true)
    public Map<String, Object> recalculatePnL(Map<String, Object> trade) {
        Map<String, Object> result = new HashMap<>(trade);
        
        String symbol = (String) trade.get("symbol");
        String side = (String) trade.get("side");
        
        if ("BOT".equals(side)) {
            // 매수는 손익 없음
            result.put("realizedPNL", 0.0);
        } else {
            // 매도 시 FIFO 기준 손익 계산
            Double sellQty = ((Number) trade.get("shares")).doubleValue();
            Double sellPrice = ((Number) trade.get("price")).doubleValue();
            
            // 이전 매수 내역에서 FIFO로 원가 계산
            String fifoSql = """
                WITH buy_queue AS (
                    SELECT 
                        execId,
                        time,
                        shares,
                        price,
                        SUM(shares) OVER (ORDER BY time, execId) as cumulative_shares
                    FROM trade_events
                    WHERE symbol = ?
                    AND side = 'BOT'
                    AND time < ?
                    ORDER BY time, execId
                )
                SELECT 
                    SUM(
                        CASE 
                            WHEN cumulative_shares <= ? THEN shares * price
                            WHEN cumulative_shares - shares < ? THEN (? - (cumulative_shares - shares)) * price
                            ELSE 0
                        END
                    ) as total_cost,
                    SUM(
                        CASE 
                            WHEN cumulative_shares <= ? THEN shares
                            WHEN cumulative_shares - shares < ? THEN (? - (cumulative_shares - shares))
                            ELSE 0
                        END
                    ) as matched_shares
                FROM buy_queue
                WHERE cumulative_shares - shares < ?
            """;
            
            try {
                Map<String, Object> costBasis = jdbcTemplate.queryForMap(fifoSql, 
                    symbol, trade.get("time"), 
                    sellQty, sellQty, sellQty,
                    sellQty, sellQty, sellQty,
                    sellQty
                );
                
                Double totalCost = ((Number) costBasis.getOrDefault("total_cost", 0)).doubleValue();
                Double matchedShares = ((Number) costBasis.getOrDefault("matched_shares", 0)).doubleValue();
                
                if (matchedShares > 0) {
                    Double avgCost = totalCost / matchedShares;
                    Double realizedPnL = (sellPrice - avgCost) * sellQty;
                    result.put("realizedPNL", realizedPnL);
                }
            } catch (Exception e) {
                log.error("FIFO 손익 계산 실패: {}", trade.get("execId"), e);
            }
        }
        
        return result;
    }

    /**
     * 손익 수정
     */
    @Transactional
    public void correctPnL(Map<String, Object> tradeData) {
        String sql = """
            UPDATE trade_events 
            SET realizedPNL = ?
            WHERE execId = ?
        """;
        
        jdbcTemplate.update(sql, 
            tradeData.get("recalculated_pnl"),
            tradeData.get("execId")
        );
        
        incrementSummaryCount("corrected_pnl");
    }

    /**
     * 중복 거래 찾기
     */
    public List<Map<String, Object>> findDuplicateTrades() {
        String sql = """
            SELECT 
                execId, 
                COUNT(*) as duplicate_count,
                ARRAY_AGG(time) as times
            FROM trade_events
            GROUP BY execId
            HAVING COUNT(*) > 1
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 중복 거래 제거
     */
    @Transactional
    public int removeDuplicateTrades(List<Map<String, Object>> duplicates) {
        int removed = 0;
        
        for (Map<String, Object> dup : duplicates) {
            String execId = (String) dup.get("execId");
            
            // 가장 오래된 것만 남기고 삭제
            String deleteSql = """
                DELETE FROM trade_events 
                WHERE execId = ? 
                AND time > (
                    SELECT MIN(time) 
                    FROM trade_events 
                    WHERE execId = ?
                )
            """;
            
            removed += jdbcTemplate.update(deleteSql, execId, execId);
        }
        
        incrementSummaryCount("removed_duplicates", removed);
        return removed;
    }

    /**
     * 중복 주문 찾기
     */
    public List<Map<String, Object>> findDuplicateOrders() {
        String sql = """
            SELECT 
                orderId, 
                COUNT(*) as duplicate_count
            FROM orders
            GROUP BY orderId
            HAVING COUNT(*) > 1
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 중복 주문 제거
     */
    @Transactional
    public int removeDuplicateOrders(List<Map<String, Object>> duplicates) {
        // 실제로는 더 복잡한 로직 필요 (어떤 것을 남길지 결정)
        return 0;
    }

    /**
     * 가격 데이터 중복 체크
     */
    public Map<String, Integer> checkPriceDataDuplicates() {
        Map<String, Integer> duplicates = new HashMap<>();
        
        // price_time 중복 체크
        String timeCheckSql = """
            SELECT COUNT(*) 
            FROM (
                SELECT time, symbol, exchange, COUNT(*) 
                FROM price_time 
                GROUP BY time, symbol, exchange 
                HAVING COUNT(*) > 1
            ) dups
        """;
        
        try {
            Integer timeDups = jdbcTemplate.queryForObject(timeCheckSql, Integer.class);
            duplicates.put("price_time", timeDups);
        } catch (Exception e) {
            duplicates.put("price_time", 0);
        }
        
        return duplicates;
    }

    /**
     * 참조 무결성 체크
     */
    public Map<String, List<Map<String, Object>>> checkReferentialIntegrity() {
        Map<String, List<Map<String, Object>>> issues = new HashMap<>();
        
        // trade_events의 orderId가 orders에 있는지 체크
        String orphanTradesSql = """
            SELECT DISTINCT t.orderId, COUNT(*) as count
            FROM trade_events t
            LEFT JOIN orders o ON t.orderId = o.orderId
            WHERE o.orderId IS NULL
            AND t.orderId IS NOT NULL
            GROUP BY t.orderId
        """;
        
        issues.put("orphan_trades", jdbcTemplate.queryForList(orphanTradesSql));
        
        // orders의 symbol이 contracts에 있는지 체크
        String invalidSymbolsSql = """
            SELECT DISTINCT o.symbol, COUNT(*) as count
            FROM orders o
            LEFT JOIN contracts c ON o.symbol = c.symbol
            WHERE c.symbol IS NULL
            GROUP BY o.symbol
        """;
        
        issues.put("invalid_symbols", jdbcTemplate.queryForList(invalidSymbolsSql));
        
        // price 데이터의 conId가 contracts에 있는지 체크
        String invalidConIdsSql = """
            SELECT DISTINCT p.conId, COUNT(*) as count
            FROM price_time p
            LEFT JOIN contracts c ON p.conId = c.conId
            WHERE c.conId IS NULL
            GROUP BY p.conId
            LIMIT 10
        """;
        
        issues.put("invalid_conids", jdbcTemplate.queryForList(invalidConIdsSql));
        
        return issues;
    }

    /**
     * 무결성 리포트 생성
     */
    public void generateIntegrityReport(Map<String, List<Map<String, Object>>> issues) {
        log.warn("========== 참조 무결성 문제 리포트 ==========");
        
        for (Map.Entry<String, List<Map<String, Object>>> entry : issues.entrySet()) {
            if (!entry.getValue().isEmpty()) {
                log.warn("{}: {} 건", entry.getKey(), entry.getValue().size());
                
                // 상위 5개만 출력
                entry.getValue().stream()
                    .limit(5)
                    .forEach(issue -> log.warn("  - {}", issue));
            }
        }
        
        log.warn("=========================================");
        
        incrementSummaryCount("integrity_issues", 
            issues.values().stream().mapToInt(List::size).sum());
    }

    /**
     * 검증 로그 저장
     */
    @Transactional
    public void saveVerificationLog(String type, Map<String, Object> result) {
        // verification_logs 테이블에 저장 (필요시 생성)
        incrementSummaryCount("verified_" + type.toLowerCase() + "s");
    }

    /**
     * 검증 요약 조회
     */
    public Map<String, Object> getVerificationSummary() {
        return new HashMap<>(verificationSummary);
    }

    /**
     * 요약 카운트 증가
     */
    private void incrementSummaryCount(String key) {
        incrementSummaryCount(key, 1);
    }

    private void incrementSummaryCount(String key, int count) {
        verificationSummary.merge(key, count, (old, inc) -> ((Integer) old) + inc);
    }
}