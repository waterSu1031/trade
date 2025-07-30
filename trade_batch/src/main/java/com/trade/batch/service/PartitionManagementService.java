package com.trade.batch.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 파티션 관리 서비스
 * - 파티션 생성, 모니터링, 최적화 담당
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PartitionManagementService {

    private final JdbcTemplate jdbcTemplate;

    /**
     * 파티션이 없는 심볼 조회
     */
    public List<Map<String, Object>> findSymbolsWithoutPartition() {
        String sql = """
            WITH active_symbols AS (
                SELECT DISTINCT symbol 
                FROM contracts 
                WHERE symbol IS NOT NULL
            ),
            existing_partitions AS (
                SELECT DISTINCT split_part(tablename, '_', 3) as symbol
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND (tablename LIKE 'price_range_%' OR tablename LIKE 'price_volume_%')
                AND tablename NOT LIKE '%_default'
            )
            SELECT s.symbol, c.conId, c.secType, c.exchange
            FROM active_symbols s
            JOIN contracts c ON s.symbol = c.symbol
            LEFT JOIN existing_partitions p ON LOWER(s.symbol) = p.symbol
            WHERE p.symbol IS NULL
            ORDER BY s.symbol
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * 파티션 생성 정보 준비
     */
    public Map<String, Object> preparePartitionInfo(Map<String, Object> symbol) {
        Map<String, Object> info = new HashMap<>(symbol);
        info.put("partition_name_range", "price_range_" + symbol.get("symbol").toString().toLowerCase());
        info.put("partition_name_volume", "price_volume_" + symbol.get("symbol").toString().toLowerCase());
        return info;
    }

    /**
     * Range 파티션 생성
     */
    @Transactional
    public void createRangePartition(Map<String, Object> partitionInfo) {
        String symbol = (String) partitionInfo.get("symbol");
        String partitionName = (String) partitionInfo.get("partition_name_range");
        
        String sql = String.format("""
            CREATE TABLE IF NOT EXISTS %s 
            PARTITION OF price_range 
            FOR VALUES IN ('%s')
        """, partitionName, symbol);
        
        try {
            jdbcTemplate.execute(sql);
            log.info("Range 파티션 생성 완료: {} for symbol: {}", partitionName, symbol);
        } catch (Exception e) {
            log.error("Range 파티션 생성 실패: {}", partitionName, e);
            throw e;
        }
    }

    /**
     * Volume 파티션 생성
     */
    @Transactional
    public void createVolumePartition(Map<String, Object> partitionInfo) {
        String symbol = (String) partitionInfo.get("symbol");
        String partitionName = (String) partitionInfo.get("partition_name_volume");
        
        String sql = String.format("""
            CREATE TABLE IF NOT EXISTS %s 
            PARTITION OF price_volume 
            FOR VALUES IN ('%s')
        """, partitionName, symbol);
        
        try {
            jdbcTemplate.execute(sql);
            log.info("Volume 파티션 생성 완료: {} for symbol: {}", partitionName, symbol);
        } catch (Exception e) {
            log.error("Volume 파티션 생성 실패: {}", partitionName, e);
            throw e;
        }
    }

    /**
     * 파티션 크기 체크
     */
    public List<Map<String, Object>> checkPartitionSizes() {
        String sql = """
            SELECT 
                schemaname || '.' || tablename as table_name,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND (tablename LIKE 'price_range_%' 
                OR tablename LIKE 'price_volume_%'
                OR tablename = 'price_time'
                OR tablename = 'trade_events')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """;
        
        return jdbcTemplate.queryForList(sql);
    }

    /**
     * TimescaleDB 청크 상태 체크
     */
    public void checkTimescaleChunks() {
        try {
            String sql = """
                SELECT 
                    hypertable_name,
                    chunk_name,
                    range_start,
                    range_end,
                    is_compressed,
                    pg_size_pretty(total_bytes) as chunk_size
                FROM timescaledb_information.chunks
                WHERE hypertable_schema = 'public'
                ORDER BY hypertable_name, range_start DESC
                LIMIT 20
            """;
            
            List<Map<String, Object>> chunks = jdbcTemplate.queryForList(sql);
            
            for (Map<String, Object> chunk : chunks) {
                log.debug("TimescaleDB 청크 - 테이블: {}, 청크: {}, 크기: {}, 압축: {}", 
                    chunk.get("hypertable_name"),
                    chunk.get("chunk_name"),
                    chunk.get("chunk_size"),
                    chunk.get("is_compressed")
                );
            }
        } catch (Exception e) {
            log.warn("TimescaleDB 청크 체크 실패 (TimescaleDB가 설치되지 않았을 수 있음): {}", e.getMessage());
        }
    }

    /**
     * VACUUM 실행 (데드 튜플 정리)
     */
    @Transactional
    public void vacuumPartitions() {
        log.info("VACUUM 시작...");
        
        // 파티션 테이블들 VACUUM
        List<Map<String, Object>> tables = jdbcTemplate.queryForList("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND (tablename LIKE 'price_%' OR tablename = 'trade_events')
        """);
        
        for (Map<String, Object> table : tables) {
            String tableName = (String) table.get("tablename");
            try {
                jdbcTemplate.execute("VACUUM ANALYZE " + tableName);
                log.debug("VACUUM 완료: {}", tableName);
            } catch (Exception e) {
                log.error("VACUUM 실패: {}", tableName, e);
            }
        }
    }

    /**
     * 인덱스 재구성
     */
    @Transactional
    public void reindexPartitions() {
        log.info("인덱스 재구성 시작...");
        
        // 파티션 테이블의 인덱스들 재구성
        List<Map<String, Object>> indexes = jdbcTemplate.queryForList("""
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND (tablename LIKE 'price_%' OR tablename = 'trade_events')
            AND indexname NOT LIKE '%_pkey'  -- Primary key는 제외
        """);
        
        for (Map<String, Object> index : indexes) {
            String indexName = (String) index.get("indexname");
            try {
                jdbcTemplate.execute("REINDEX INDEX " + indexName);
                log.debug("인덱스 재구성 완료: {}", indexName);
            } catch (Exception e) {
                log.error("인덱스 재구성 실패: {}", indexName, e);
            }
        }
    }

    /**
     * 통계 업데이트
     */
    @Transactional
    public void analyzePartitions() {
        log.info("통계 업데이트 시작...");
        
        // 전체 데이터베이스 통계 업데이트
        jdbcTemplate.execute("ANALYZE");
        
        log.info("통계 업데이트 완료");
    }
}