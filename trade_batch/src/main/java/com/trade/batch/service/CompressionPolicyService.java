package com.trade.batch.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

/**
 * TimescaleDB 압축 정책 관리 서비스
 * - 청크 압축 관리
 * - 압축 정책 실행
 * - 디스크 공간 최적화
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CompressionPolicyService {

    private final JdbcTemplate jdbcTemplate;
    private final Set<String> markedForCompression = new HashSet<>();

    /**
     * 압축 대상 청크 조회
     * - 30일 이상된 압축되지 않은 청크
     */
    public List<Map<String, Object>> findCompressionCandidates() {
        String sql = """
            SELECT 
                chunk_schema,
                chunk_name,
                hypertable_schema,
                hypertable_name,
                range_start,
                range_end,
                is_compressed,
                total_bytes,
                total_bytes / 1024 / 1024 as size_mb
            FROM timescaledb_information.chunks
            WHERE hypertable_schema = 'public'
            AND is_compressed = false
            AND range_end < NOW() - INTERVAL '30 days'
            ORDER BY range_start
        """;
        
        try {
            return jdbcTemplate.queryForList(sql);
        } catch (Exception e) {
            log.warn("TimescaleDB 압축 대상 조회 실패 (TimescaleDB가 설치되지 않았을 수 있음): {}", e.getMessage());
            return new ArrayList<>();
        }
    }

    /**
     * 청크 상세 정보 조회
     */
    public Map<String, Object> getChunkDetail(Map<String, Object> chunk) {
        Map<String, Object> detail = new HashMap<>(chunk);
        
        String chunkFullName = chunk.get("chunk_schema") + "." + chunk.get("chunk_name");
        
        // 청크 내 데이터 통계
        try {
            String statsSql = String.format("""
                SELECT 
                    COUNT(*) as row_count,
                    MIN(time) as min_time,
                    MAX(time) as max_time
                FROM %s
            """, chunkFullName);
            
            Map<String, Object> stats = jdbcTemplate.queryForMap(statsSql);
            detail.putAll(stats);
        } catch (Exception e) {
            log.debug("청크 통계 조회 실패: {}", chunkFullName);
        }
        
        return detail;
    }

    /**
     * 압축 비율 예측
     */
    public Double estimateCompressionRatio(Map<String, Object> chunkDetail) {
        // TimescaleDB는 일반적으로 60-95% 압축률을 보임
        // 데이터 타입과 패턴에 따라 다름
        
        String hypertableName = (String) chunkDetail.get("hypertable_name");
        
        // 테이블별 예상 압축률
        if ("trade_events".equals(hypertableName)) {
            return 0.15; // 85% 압축 (텍스트 필드가 많음)
        } else if ("price_time".equals(hypertableName)) {
            return 0.25; // 75% 압축 (숫자 필드 위주)
        }
        
        return 0.3; // 기본 70% 압축
    }

    /**
     * 압축 대상 표시
     */
    public void markForCompression(Map<String, Object> chunk) {
        String chunkName = (String) chunk.get("chunk_name");
        markedForCompression.add(chunkName);
        log.debug("압축 대상 표시: {}", chunkName);
    }

    /**
     * 압축 대상으로 표시된 청크 조회
     */
    public List<Map<String, Object>> getMarkedChunks() {
        if (markedForCompression.isEmpty()) {
            return new ArrayList<>();
        }
        
        String placeholders = String.join(",", 
            Collections.nCopies(markedForCompression.size(), "?"));
        
        String sql = String.format("""
            SELECT 
                chunk_schema,
                chunk_name,
                hypertable_schema,
                hypertable_name,
                total_bytes
            FROM timescaledb_information.chunks
            WHERE chunk_name IN (%s)
        """, placeholders);
        
        return jdbcTemplate.queryForList(sql, markedForCompression.toArray());
    }

    /**
     * 청크 압축 실행
     */
    @Transactional
    public Map<String, Object> compressChunk(Map<String, Object> chunk) {
        String chunkSchema = (String) chunk.get("chunk_schema");
        String chunkName = (String) chunk.get("chunk_name");
        
        Map<String, Object> result = new HashMap<>();
        result.put("chunk_name", chunkName);
        
        try {
            // TimescaleDB 압축 함수 호출
            String compressSql = String.format(
                "SELECT compress_chunk('%s.%s'::regclass) as compressed",
                chunkSchema, chunkName
            );
            
            jdbcTemplate.queryForMap(compressSql);
            
            // 압축 후 크기 확인
            String sizeSql = """
                SELECT 
                    total_bytes as size_after,
                    is_compressed
                FROM timescaledb_information.chunks
                WHERE chunk_name = ?
            """;
            
            Map<String, Object> sizeInfo = jdbcTemplate.queryForMap(sizeSql, chunkName);
            result.putAll(sizeInfo);
            
            log.info("청크 압축 성공: {}", chunkName);
            
        } catch (Exception e) {
            log.error("청크 압축 실패: {}", chunkName, e);
            throw e;
        }
        
        return result;
    }

    /**
     * 오래된 청크 조회
     */
    public List<Map<String, Object>> findOldChunks() {
        // 기본적으로 1년 이상된 데이터는 삭제 대상
        String sql = """
            SELECT 
                chunk_schema,
                chunk_name,
                hypertable_name,
                range_start,
                range_end,
                total_bytes,
                is_compressed
            FROM timescaledb_information.chunks
            WHERE hypertable_schema = 'public'
            AND range_end < NOW() - INTERVAL '1 year'
            ORDER BY range_start
            LIMIT 100
        """;
        
        try {
            return jdbcTemplate.queryForList(sql);
        } catch (Exception e) {
            log.warn("오래된 청크 조회 실패: {}", e.getMessage());
            return new ArrayList<>();
        }
    }

    /**
     * 백업 필요 여부 확인
     */
    public boolean isBackupRequired(Map<String, Object> chunk) {
        // 중요 데이터나 압축되지 않은 청크는 백업
        Boolean isCompressed = (Boolean) chunk.get("is_compressed");
        return !Boolean.TRUE.equals(isCompressed);
    }

    /**
     * 청크 백업
     */
    @Transactional
    public void backupChunk(Map<String, Object> chunk) {
        // 실제 백업 로직 구현 필요
        // 예: S3로 백업, 다른 테이블로 복사 등
        log.info("청크 백업 시뮬레이션: {}", chunk.get("chunk_name"));
    }

    /**
     * 오래된 청크 삭제
     */
    @Transactional
    public int dropOldChunks(List<Map<String, Object>> oldChunks) {
        int droppedCount = 0;
        
        for (Map<String, Object> chunk : oldChunks) {
            String chunkSchema = (String) chunk.get("chunk_schema");
            String chunkName = (String) chunk.get("chunk_name");
            
            try {
                String dropSql = String.format(
                    "SELECT drop_chunks('%s.%s'::regclass, older_than => INTERVAL '1 year')",
                    chunkSchema, chunkName
                );
                
                jdbcTemplate.execute(dropSql);
                droppedCount++;
                log.debug("청크 삭제 완료: {}", chunkName);
                
            } catch (Exception e) {
                log.error("청크 삭제 실패: {}", chunkName, e);
            }
        }
        
        return droppedCount;
    }

    /**
     * 전체 압축 통계 조회
     */
    public Map<String, Object> getCompressionStatistics() {
        Map<String, Object> stats = new HashMap<>();
        
        try {
            String sql = """
                SELECT 
                    COUNT(*) as total_chunks,
                    COUNT(*) FILTER (WHERE is_compressed) as compressed_chunks,
                    COUNT(*) FILTER (WHERE NOT is_compressed) as uncompressed_chunks,
                    SUM(total_bytes) / 1024 / 1024 / 1024 as total_size_gb,
                    SUM(total_bytes) FILTER (WHERE is_compressed) / 1024 / 1024 / 1024 as compressed_size_gb,
                    AVG(CASE WHEN is_compressed THEN 0.25 ELSE 1.0 END) * 100 as avg_compression_ratio
                FROM timescaledb_information.chunks
                WHERE hypertable_schema = 'public'
            """;
            
            Map<String, Object> result = jdbcTemplate.queryForMap(sql);
            stats.putAll(result);
            
            // 절약된 공간 계산
            Double totalSize = ((Number) stats.getOrDefault("total_size_gb", 0)).doubleValue();
            Double compressedSize = ((Number) stats.getOrDefault("compressed_size_gb", 0)).doubleValue();
            stats.put("saved_space_gb", totalSize - compressedSize);
            
        } catch (Exception e) {
            log.warn("압축 통계 조회 실패: {}", e.getMessage());
        }
        
        return stats;
    }

    /**
     * 테이블별 압축 통계
     */
    public List<Map<String, Object>> getTableCompressionStats() {
        String sql = """
            SELECT 
                hypertable_name,
                COUNT(*) as total_chunks,
                COUNT(*) FILTER (WHERE is_compressed) as compressed_chunks,
                SUM(total_bytes) / 1024 / 1024 / 1024 as size_gb,
                AVG(CASE WHEN is_compressed THEN 0.25 ELSE 1.0 END) * 100 as compression_ratio
            FROM timescaledb_information.chunks
            WHERE hypertable_schema = 'public'
            GROUP BY hypertable_name
            ORDER BY size_gb DESC
        """;
        
        try {
            return jdbcTemplate.queryForList(sql);
        } catch (Exception e) {
            log.warn("테이블별 압축 통계 조회 실패: {}", e.getMessage());
            return new ArrayList<>();
        }
    }

    /**
     * 압축 정책 권장사항 생성
     */
    public void generateRecommendations(Map<String, Object> stats) {
        Double compressedRatio = ((Number) stats.getOrDefault("compressed_chunks", 0)).doubleValue() /
                                ((Number) stats.getOrDefault("total_chunks", 1)).doubleValue();
        
        if (compressedRatio < 0.5) {
            log.warn("권장사항: 전체 청크의 {}%만 압축되어 있습니다. 압축 정책을 더 자주 실행하세요.", 
                Math.round(compressedRatio * 100));
        }
        
        Double savedSpace = ((Number) stats.getOrDefault("saved_space_gb", 0)).doubleValue();
        if (savedSpace > 100) {
            log.info("권장사항: {} GB의 공간을 절약했습니다. 압축 정책이 효과적으로 작동하고 있습니다.", 
                Math.round(savedSpace));
        }
    }

    /**
     * TimescaleDB 버전 확인
     */
    public String getTimescaleDBVersion() {
        try {
            String sql = "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'";
            return jdbcTemplate.queryForObject(sql, String.class);
        } catch (Exception e) {
            return "Unknown";
        }
    }

    /**
     * 디스크 공간 확인
     */
    public void checkDiskSpace() {
        try {
            String sql = """
                SELECT 
                    pg_database_size(current_database()) / 1024 / 1024 / 1024 as db_size_gb,
                    pg_size_pretty(pg_database_size(current_database())) as db_size_pretty
            """;
            
            Map<String, Object> diskInfo = jdbcTemplate.queryForMap(sql);
            log.info("현재 데이터베이스 크기: {}", diskInfo.get("db_size_pretty"));
            
        } catch (Exception e) {
            log.warn("디스크 공간 확인 실패: {}", e.getMessage());
        }
    }
}