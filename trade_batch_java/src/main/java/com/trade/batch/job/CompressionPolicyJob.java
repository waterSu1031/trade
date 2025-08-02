package com.trade.batch.job;

import com.trade.batch.service.CompressionPolicyService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.*;
import org.springframework.batch.core.configuration.annotation.StepScope;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.core.step.tasklet.Tasklet;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.batch.item.support.ListItemReader;
import org.springframework.batch.repeat.RepeatStatus;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.lang.NonNull;
import org.springframework.transaction.PlatformTransactionManager;

import java.util.List;
import java.util.Map;

/**
 * TimescaleDB 압축 정책 관리 배치 Job
 * - 오래된 데이터 압축
 * - 청크 관리 및 최적화
 * - 압축 정책 실행
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class CompressionPolicyJob {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;
    private final CompressionPolicyService compressionPolicyService;

    /**
     * 압축 정책 실행 메인 Job
     * 1. 압축 대상 청크 확인
     * 2. 청크 압축 실행
     * 3. 오래된 청크 정리
     * 4. 압축 통계 리포트
     */
    @Bean
    public Job executeCompressionPolicyJob() {
        return new JobBuilder("executeCompressionPolicyJob", jobRepository)
                .start(identifyCompressionCandidatesStep())    // 압축 대상 확인
                .next(compressChunksStep())                     // 청크 압축
                .next(dropOldChunksStep())                      // 오래된 청크 삭제
                .next(generateCompressionReportStep())          // 압축 리포트
                .listener(compressionJobListener())
                .build();
    }

    // ========== Step 1: 압축 대상 청크 확인 ==========

    /**
     * 압축 대상 청크 확인 Step
     */
    @Bean
    public Step identifyCompressionCandidatesStep() {
        return new StepBuilder("identifyCompressionCandidatesStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(50, transactionManager)
                .reader(compressionCandidateReader())
                .processor(compressionCandidateProcessor())
                .writer(compressionCandidateWriter())
                .listener(compressionCandidateListener())
                .build();
    }

    /**
     * 압축 대상 청크 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> compressionCandidateReader() {
        // 30일 이상된 압축되지 않은 청크들 조회
        List<Map<String, Object>> candidates = compressionPolicyService.findCompressionCandidates();
        log.info("압축 대상 청크 수: {}", candidates.size());
        return new ListItemReader<>(candidates);
    }

    /**
     * 압축 대상 청크 정보 처리
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> compressionCandidateProcessor() {
        return chunk -> {
            // 청크 상세 정보 조회
            Map<String, Object> chunkDetail = compressionPolicyService.getChunkDetail(chunk);
            
            // 압축 예상 효과 계산
            Long currentSize = (Long) chunkDetail.get("total_bytes");
            Double compressionRatio = compressionPolicyService.estimateCompressionRatio(chunkDetail);
            chunkDetail.put("estimated_compressed_size", (long)(currentSize * compressionRatio));
            chunkDetail.put("estimated_savings", currentSize - (long)(currentSize * compressionRatio));
            
            log.debug("청크 압축 예상 - 테이블: {}, 청크: {}, 현재: {} MB, 예상: {} MB", 
                chunkDetail.get("hypertable_name"),
                chunkDetail.get("chunk_name"),
                currentSize / 1024 / 1024,
                (long)(currentSize * compressionRatio) / 1024 / 1024
            );
            
            return chunkDetail;
        };
    }

    /**
     * 압축 대상 정보 저장
     */
    @Bean
    public ItemWriter<Map<String, Object>> compressionCandidateWriter() {
        return chunks -> {
            // 압축 대상 목록을 임시 저장 (다음 Step에서 사용)
            for (Map<String, Object> chunk : chunks) {
                compressionPolicyService.markForCompression(chunk);
            }
        };
    }

    // ========== Step 2: 청크 압축 실행 ==========

    /**
     * 청크 압축 실행 Step
     */
    @Bean
    public Step compressChunksStep() {
        return new StepBuilder("compressChunksStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(5, transactionManager) // 압축은 무거운 작업이므로 작은 chunk
                .reader(markedChunksReader())
                .processor(chunkCompressProcessor())
                .writer(chunkCompressWriter())
                .build();
    }

    /**
     * 압축 대상으로 표시된 청크 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> markedChunksReader() {
        List<Map<String, Object>> markedChunks = compressionPolicyService.getMarkedChunks();
        return new ListItemReader<>(markedChunks);
    }

    /**
     * 청크 압축 처리
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> chunkCompressProcessor() {
        return chunk -> {
            String chunkName = (String) chunk.get("chunk_name");
            log.info("청크 압축 시작: {}", chunkName);
            
            // 압축 전 상태 기록
            chunk.put("compression_start_time", System.currentTimeMillis());
            chunk.put("size_before", chunk.get("total_bytes"));
            
            return chunk;
        };
    }

    /**
     * 청크 압축 실행
     */
    @Bean
    public ItemWriter<Map<String, Object>> chunkCompressWriter() {
        return chunks -> {
            for (Map<String, Object> chunk : chunks) {
                try {
                    // TimescaleDB 압축 실행
                    Map<String, Object> result = compressionPolicyService.compressChunk(chunk);
                    
                    Long sizeBefore = (Long) chunk.get("size_before");
                    Long sizeAfter = (Long) result.get("size_after");
                    Double actualRatio = sizeAfter.doubleValue() / sizeBefore.doubleValue();
                    
                    log.info("청크 압축 완료 - {}: {} MB → {} MB ({}% 압축)", 
                        chunk.get("chunk_name"),
                        sizeBefore / 1024 / 1024,
                        sizeAfter / 1024 / 1024,
                        Math.round((1 - actualRatio) * 100)
                    );
                    
                } catch (Exception e) {
                    log.error("청크 압축 실패: {}", chunk.get("chunk_name"), e);
                }
            }
        };
    }

    // ========== Step 3: 오래된 청크 정리 ==========

    /**
     * 오래된 청크 삭제 Step (Tasklet)
     */
    @Bean
    public Step dropOldChunksStep() {
        return new StepBuilder("dropOldChunksStep", jobRepository)
                .tasklet(dropOldChunksTasklet(), transactionManager)
                .build();
    }

    /**
     * 오래된 청크 삭제 Tasklet
     */
    @Bean
    @StepScope
    public Tasklet dropOldChunksTasklet() {
        return (contribution, chunkContext) -> {
            log.info("오래된 청크 정리 시작");
            
            try {
                // 설정된 보관 기간을 초과한 청크들 조회
                List<Map<String, Object>> oldChunks = compressionPolicyService.findOldChunks();
                
                if (oldChunks.isEmpty()) {
                    log.info("삭제할 오래된 청크가 없습니다.");
                    return RepeatStatus.FINISHED;
                }
                
                log.info("삭제 대상 청크 수: {}", oldChunks.size());
                
                // 삭제 전 백업 확인
                for (Map<String, Object> chunk : oldChunks) {
                    if (compressionPolicyService.isBackupRequired(chunk)) {
                        log.info("청크 백업 중: {}", chunk.get("chunk_name"));
                        compressionPolicyService.backupChunk(chunk);
                    }
                }
                
                // 청크 삭제
                int droppedCount = compressionPolicyService.dropOldChunks(oldChunks);
                log.info("오래된 청크 {} 개 삭제 완료", droppedCount);
                
            } catch (Exception e) {
                log.error("오래된 청크 정리 실패", e);
                throw e;
            }
            
            return RepeatStatus.FINISHED;
        };
    }

    // ========== Step 4: 압축 통계 리포트 ==========

    /**
     * 압축 통계 리포트 생성 Step (Tasklet)
     */
    @Bean
    public Step generateCompressionReportStep() {
        return new StepBuilder("generateCompressionReportStep", jobRepository)
                .tasklet(compressionReportTasklet(), transactionManager)
                .build();
    }

    /**
     * 압축 리포트 생성 Tasklet
     */
    @Bean
    @StepScope
    public Tasklet compressionReportTasklet() {
        return (contribution, chunkContext) -> {
            log.info("압축 통계 리포트 생성");
            
            // 전체 압축 통계
            Map<String, Object> compressionStats = compressionPolicyService.getCompressionStatistics();
            
            // 하이퍼테이블별 통계
            List<Map<String, Object>> tableStats = compressionPolicyService.getTableCompressionStats();
            
            log.info("========== TimescaleDB 압축 리포트 ==========");
            log.info("전체 청크 수: {}", compressionStats.get("total_chunks"));
            log.info("압축된 청크 수: {}", compressionStats.get("compressed_chunks"));
            log.info("압축되지 않은 청크 수: {}", compressionStats.get("uncompressed_chunks"));
            log.info("전체 크기: {} GB", compressionStats.get("total_size_gb"));
            log.info("압축된 크기: {} GB", compressionStats.get("compressed_size_gb"));
            log.info("절약된 공간: {} GB", compressionStats.get("saved_space_gb"));
            log.info("평균 압축률: {}%", compressionStats.get("avg_compression_ratio"));
            
            log.info("\n테이블별 압축 현황:");
            for (Map<String, Object> table : tableStats) {
                log.info("  {} - 청크: {}, 압축: {}, 크기: {} GB, 압축률: {}%",
                    table.get("hypertable_name"),
                    table.get("total_chunks"),
                    table.get("compressed_chunks"),
                    table.get("size_gb"),
                    table.get("compression_ratio")
                );
            }
            log.info("==========================================");
            
            // 압축 정책 권장사항
            compressionPolicyService.generateRecommendations(compressionStats);
            
            return RepeatStatus.FINISHED;
        };
    }

    // ========== Listeners ==========

    @Bean
    public StepExecutionListener compressionCandidateListener() {
        return new StepExecutionListener() {
            @Override
            public void beforeStep(@NonNull StepExecution stepExecution) {
                log.info("🔹 [압축 대상 확인] 시작");
            }
            
            @Override
            public ExitStatus afterStep(@NonNull StepExecution stepExecution) {
                log.info("🔸 [압축 대상 확인] 완료 - {} 개 청크 확인", 
                    stepExecution.getReadCount());
                return stepExecution.getExitStatus();
            }
        };
    }

    @Bean
    public JobExecutionListener compressionJobListener() {
        return new JobExecutionListener() {
            @Override
            public void beforeJob(@NonNull JobExecution jobExecution) {
                log.info("===== TimescaleDB 압축 정책 Job 시작 =====");
                
                // TimescaleDB 버전 확인
                try {
                    String version = compressionPolicyService.getTimescaleDBVersion();
                    log.info("TimescaleDB 버전: {}", version);
                } catch (Exception e) {
                    log.warn("TimescaleDB 버전 확인 실패: {}", e.getMessage());
                }
            }
            
            @Override
            public void afterJob(@NonNull JobExecution jobExecution) {
                log.info("===== TimescaleDB 압축 정책 Job 종료: {} =====", 
                    jobExecution.getStatus());
                
                if (jobExecution.getStatus() == BatchStatus.COMPLETED) {
                    // 압축 후 디스크 공간 확인
                    compressionPolicyService.checkDiskSpace();
                }
            }
        };
    }
}