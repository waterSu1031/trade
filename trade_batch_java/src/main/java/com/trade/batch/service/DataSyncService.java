package com.trade.batch.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Connection;
import java.sql.DriverManager;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * 데이터 동기화 서비스
 * - PostgreSQL → DuckDB 동기화
 * - 마스터 데이터 관리
 * - 동기화 상태 추적
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DataSyncService {

    private final JdbcTemplate jdbcTemplate;
    
    @Value("${duckdb.path:/home/freeksj/Workspace_Rule/trade/trade_infra/analyze_db.duckdb}")
    private String duckdbPath;
    
    private LocalDateTime jobStartTime;
    private final Map<String, Object> syncStatistics = new HashMap<>();

    /**
     * DuckDB 연결 테스트
     */
    public boolean testDuckDBConnection() {
        try (Connection conn = DriverManager.getConnection("jdbc:duckdb:" + duckdbPath)) {
            return conn.isValid(5);
        } catch (Exception e) {
            log.error("DuckDB 연결 실패: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 변경된 마스터 데이터 조회
     */
    public List<Map<String, Object>> getUpdatedMasterData() {
        // 마지막 동기화 이후 변경된 마스터 데이터
        String sql = """
            SELECT 
                'contracts' as table_name,
                conId,
                symbol,
                secType,
                exchange,
                updated_at
            FROM contracts
            WHERE updated_at > COALESCE(
                (SELECT last_sync FROM sync_metadata WHERE table_name = 'contracts'),
                '1970-01-01'::timestamp
            )
            UNION ALL
            SELECT 
                'exchanges' as table_name,
                exchange as conId,
                exchange as symbol,
                'EXCH' as secType,
                region as exchange,
                created_at as updated_at
            FROM exchanges
            WHERE created_at > COALESCE(
                (SELECT last_sync FROM sync_metadata WHERE table_name = 'exchanges'),
                '1970-01-01'::timestamp
            )
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 마스터 데이터 처리
     */
    public Map<String, Object> processMasterData(Map<String, Object> data) {
        // 데이터 클렌징 및 변환
        Map<String, Object> processed = new HashMap<>(data);
        
        // NULL 값 처리
        processed.entrySet().forEach(entry -> {
            if (entry.getValue() == null) {
                entry.setValue("");
            }
        });
        
        return processed;
    }

    /**
     * 마스터 데이터 DuckDB 동기화
     */
    @Transactional
    public void syncMasterDataToDuckDB(Map<String, Object> data) {
        String tableName = (String) data.get("table_name");
        
        try (Connection conn = DriverManager.getConnection("jdbc:duckdb:" + duckdbPath)) {
            // 테이블별 UPSERT 로직
            if ("contracts".equals(tableName)) {
                String sql = """
                    INSERT OR REPLACE INTO contracts 
                    (conId, symbol, secType, exchange, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """;
                
                try (var pstmt = conn.prepareStatement(sql)) {
                    pstmt.setObject(1, data.get("conId"));
                    pstmt.setObject(2, data.get("symbol"));
                    pstmt.setObject(3, data.get("secType"));
                    pstmt.setObject(4, data.get("exchange"));
                    pstmt.setObject(5, data.get("updated_at"));
                    pstmt.executeUpdate();
                }
            }
            
            incrementSyncCount(tableName);
            
        } catch (Exception e) {
            log.error("DuckDB 동기화 실패: {}", tableName, e);
            throw new RuntimeException(e);
        }
    }

    /**
     * 마지막 동기화 시점 조회
     */
    public LocalDateTime getLastSyncTime(String tableName) {
        try {
            String sql = "SELECT last_sync FROM sync_metadata WHERE table_name = ?";
            return jdbcTemplate.queryForObject(sql, LocalDateTime.class, tableName);
        } catch (Exception e) {
            // 동기화 이력이 없으면 30일 전부터
            return LocalDateTime.now().minusDays(30);
        }
    }

    /**
     * 거래 이벤트 동기화
     */
    @Transactional
    public int syncTradeEvents(LocalDateTime lastSyncTime) {
        String sql = """
            INSERT INTO duckdb_connection
            SELECT * FROM trade_events
            WHERE created_at > ?
            ORDER BY time
        """;
        
        // 실제로는 배치로 처리
        int totalSynced = 0;
        int batchSize = 10000;
        
        try (Connection conn = DriverManager.getConnection("jdbc:duckdb:" + duckdbPath)) {
            // PostgreSQL에서 조회
            String selectSql = """
                SELECT execId, orderId, time, symbol, side, shares, price, 
                       realizedPNL, commission, position, avgCost
                FROM trade_events
                WHERE created_at > ?
                ORDER BY time
                LIMIT ?
            """;
            
            // DuckDB에 삽입
            String insertSql = """
                INSERT INTO trade_events 
                (execId, orderId, time, symbol, side, shares, price, 
                 realizedPNL, commission, position, avgCost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """;
            
            List<Map<String, Object>> batch;
            do {
                batch = jdbcTemplate.queryForList(selectSql, lastSyncTime, batchSize);
                
                if (!batch.isEmpty()) {
                    try (var pstmt = conn.prepareStatement(insertSql)) {
                        for (Map<String, Object> row : batch) {
                            pstmt.setObject(1, row.get("execId"));
                            pstmt.setObject(2, row.get("orderId"));
                            pstmt.setObject(3, row.get("time"));
                            pstmt.setObject(4, row.get("symbol"));
                            pstmt.setObject(5, row.get("side"));
                            pstmt.setObject(6, row.get("shares"));
                            pstmt.setObject(7, row.get("price"));
                            pstmt.setObject(8, row.get("realizedPNL"));
                            pstmt.setObject(9, row.get("commission"));
                            pstmt.setObject(10, row.get("position"));
                            pstmt.setObject(11, row.get("avgCost"));
                            pstmt.addBatch();
                        }
                        pstmt.executeBatch();
                    }
                    
                    totalSynced += batch.size();
                    lastSyncTime = (LocalDateTime) batch.get(batch.size() - 1).get("created_at");
                }
                
            } while (batch.size() == batchSize);
            
        } catch (Exception e) {
            log.error("거래 이벤트 동기화 실패", e);
            throw new RuntimeException(e);
        }
        
        incrementSyncCount("trade_events", totalSynced);
        return totalSynced;
    }

    /**
     * 일별 집계 동기화
     */
    @Transactional
    public int syncDailyAggregates() {
        try (Connection conn = DriverManager.getConnection("jdbc:duckdb:" + duckdbPath)) {
            // 일별 통계 동기화
            String sql = """
                INSERT OR REPLACE INTO daily_statistics
                SELECT * FROM postgresql_scan(
                    'postgresql://freeksj:Lsld1501!@localhost:5432/trade_db',
                    'public',
                    'daily_statistics'
                )
                WHERE date >= CURRENT_DATE - INTERVAL '90 days'
            """;
            
            try (var stmt = conn.createStatement()) {
                return stmt.executeUpdate(sql);
            }
            
        } catch (Exception e) {
            log.error("일별 집계 동기화 실패", e);
            return 0;
        }
    }

    /**
     * 동기화 시점 업데이트
     */
    @Transactional
    public void updateSyncTime(String tableName, LocalDateTime syncTime) {
        String sql = """
            INSERT INTO sync_metadata (table_name, last_sync, record_count)
            VALUES (?, ?, ?)
            ON CONFLICT (table_name) 
            DO UPDATE SET 
                last_sync = EXCLUDED.last_sync,
                record_count = EXCLUDED.record_count
        """;
        
        Integer count = (Integer) syncStatistics.getOrDefault(tableName, 0);
        jdbcTemplate.update(sql, tableName, syncTime, count);
    }

    /**
     * 최근 가격 데이터 조회
     */
    public List<Map<String, Object>> getRecentPriceData() {
        // 배치 처리를 위해 제한된 수만 반환
        String sql = """
            SELECT 
                'time' as data_type,
                symbol,
                time,
                open,
                high,
                low,
                close,
                volume
            FROM price_time
            WHERE time >= CURRENT_TIMESTAMP - INTERVAL '1 day'
            ORDER BY time DESC
            LIMIT 10000
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 가격 데이터 집계
     */
    public Map<String, Object> aggregatePriceData(Map<String, Object> priceData) {
        // 1분 데이터를 5분/1시간으로 집계
        Map<String, Object> aggregated = new HashMap<>(priceData);
        
        // 집계 로직 구현
        aggregated.put("interval", "5m");
        
        return aggregated;
    }

    /**
     * 가격 데이터 벌크 삽입
     */
    @Transactional
    public void bulkInsertPriceData(List<Map<String, Object>> priceDataList) {
        if (priceDataList.isEmpty()) return;
        
        try (Connection conn = DriverManager.getConnection("jdbc:duckdb:" + duckdbPath)) {
            String sql = """
                INSERT INTO price_aggregates 
                (symbol, time, interval, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """;
            
            try (var pstmt = conn.prepareStatement(sql)) {
                for (Map<String, Object> data : priceDataList) {
                    pstmt.setObject(1, data.get("symbol"));
                    pstmt.setObject(2, data.get("time"));
                    pstmt.setObject(3, data.get("interval"));
                    pstmt.setObject(4, data.get("open"));
                    pstmt.setObject(5, data.get("high"));
                    pstmt.setObject(6, data.get("low"));
                    pstmt.setObject(7, data.get("close"));
                    pstmt.setObject(8, data.get("volume"));
                    pstmt.addBatch();
                }
                pstmt.executeBatch();
            }
            
            incrementSyncCount("price_data", priceDataList.size());
            
        } catch (Exception e) {
            log.error("가격 데이터 벌크 삽입 실패", e);
        }
    }

    /**
     * 동기화 검증
     */
    public Map<String, Object> verifySynchronization() {
        Map<String, Object> result = new HashMap<>();
        
        // 주요 테이블별 레코드 수 비교
        String[] tables = {"trade_events", "contracts", "daily_statistics"};
        
        for (String table : tables) {
            Map<String, Object> counts = new HashMap<>();
            
            // PostgreSQL 카운트
            try {
                String pgSql = "SELECT COUNT(*) FROM " + table;
                Long pgCount = jdbcTemplate.queryForObject(pgSql, Long.class);
                counts.put("postgresql_count", pgCount);
            } catch (Exception e) {
                counts.put("postgresql_count", 0L);
            }
            
            // DuckDB 카운트
            try (Connection conn = DriverManager.getConnection("jdbc:duckdb:" + duckdbPath)) {
                String duckSql = "SELECT COUNT(*) as cnt FROM " + table;
                try (var stmt = conn.createStatement(); 
                     var rs = stmt.executeQuery(duckSql)) {
                    if (rs.next()) {
                        counts.put("duckdb_count", rs.getLong("cnt"));
                    }
                }
            } catch (Exception e) {
                counts.put("duckdb_count", 0L);
            }
            
            result.put(table, counts);
        }
        
        return result;
    }

    /**
     * 데이터 품질 체크
     */
    public Map<String, Object> checkDataQuality() {
        Map<String, Object> issues = new HashMap<>();
        
        // NULL 값 체크
        try (Connection conn = DriverManager.getConnection("jdbc:duckdb:" + duckdbPath)) {
            String sql = """
                SELECT 
                    COUNT(*) FILTER (WHERE symbol IS NULL) as null_symbols,
                    COUNT(*) FILTER (WHERE time IS NULL) as null_times
                FROM trade_events
            """;
            
            try (var stmt = conn.createStatement(); 
                 var rs = stmt.executeQuery(sql)) {
                if (rs.next()) {
                    if (rs.getLong("null_symbols") > 0) {
                        issues.put("null_symbols", rs.getLong("null_symbols"));
                    }
                    if (rs.getLong("null_times") > 0) {
                        issues.put("null_times", rs.getLong("null_times"));
                    }
                }
            }
        } catch (Exception e) {
            log.error("데이터 품질 체크 실패", e);
        }
        
        return issues;
    }

    /**
     * 동기화 통계
     */
    public Map<String, Object> getSyncStatistics() {
        Map<String, Object> stats = new HashMap<>(syncStatistics);
        
        // 총 테이블 수
        stats.put("total_tables", syncStatistics.keySet().size());
        
        // 총 레코드 수
        int totalRecords = syncStatistics.values().stream()
            .filter(v -> v instanceof Integer)
            .mapToInt(v -> (Integer) v)
            .sum();
        stats.put("total_records", totalRecords);
        
        // 소요 시간
        if (jobStartTime != null) {
            long seconds = ChronoUnit.SECONDS.between(jobStartTime, LocalDateTime.now());
            stats.put("duration_seconds", seconds);
            stats.put("avg_speed", seconds > 0 ? totalRecords / seconds : 0);
        }
        
        return stats;
    }

    /**
     * 다음 동기화 예정 시간
     */
    public LocalDateTime getNextSyncSchedule() {
        // 스케줄러 설정에 따라 계산
        return LocalDateTime.now().plusHours(1);
    }

    /**
     * 동기화 카운트 증가
     */
    private void incrementSyncCount(String table) {
        incrementSyncCount(table, 1);
    }

    private void incrementSyncCount(String table, int count) {
        syncStatistics.merge(table, count, (old, inc) -> (Integer) old + (Integer) inc);
    }
}