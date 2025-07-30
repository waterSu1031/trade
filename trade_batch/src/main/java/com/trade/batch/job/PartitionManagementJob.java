package com.trade.batch.job;

import com.trade.batch.service.PartitionManagementService;
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
 * 파티션 관리 배치 Job
 * - 새로운 심볼에 대한 파티션 자동 생성
 * - 파티션 상태 모니터링 및 최적화
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class PartitionManagementJob {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;
    private final PartitionManagementService partitionManagementService;

    /**
     * 파티션 관리 메인 Job
     * 1. 새 심볼 파티션 생성
     * 2. 파티션 상태 체크
     * 3. 파티션 최적화
     */
    @Bean
    public Job managePartitionJob() {
        return new JobBuilder("managePartitionJob", jobRepository)
                .start(createNewPartitionStep())      // 새 파티션 생성
                .next(checkPartitionHealthStep())      // 파티션 상태 체크
                .next(optimizePartitionStep())         // 파티션 최적화
                .listener(partitionJobListener())
                .build();
    }

    // ========== Step 1: 새 심볼 파티션 생성 ==========
    
    /**
     * 새로운 심볼에 대한 파티션 생성 Step
     */
    @Bean
    public Step createNewPartitionStep() {
        return new StepBuilder("createNewPartitionStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(10, transactionManager)
                .reader(newSymbolReader())
                .processor(partitionCreateProcessor())
                .writer(partitionCreateWriter())
                .listener(createPartitionListener())
                .build();
    }

    /**
     * 파티션이 없는 새 심볼 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> newSymbolReader() {
        // price_range, price_volume 테이블에 파티션이 없는 심볼 조회
        List<Map<String, Object>> newSymbols = partitionManagementService.findSymbolsWithoutPartition();
        log.info("파티션 생성 대상 심볼 수: {}", newSymbols.size());
        return new ListItemReader<>(newSymbols);
    }

    /**
     * 파티션 생성 정보 처리
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> partitionCreateProcessor() {
        return symbol -> {
            // 파티션 생성 준비
            Map<String, Object> partitionInfo = partitionManagementService.preparePartitionInfo(symbol);
            log.debug("파티션 생성 준비: {}", partitionInfo);
            return partitionInfo;
        };
    }

    /**
     * 파티션 실제 생성
     */
    @Bean
    public ItemWriter<Map<String, Object>> partitionCreateWriter() {
        return partitionInfos -> {
            for (Map<String, Object> partitionInfo : partitionInfos) {
                try {
                    // price_range 파티션 생성
                    partitionManagementService.createRangePartition(partitionInfo);
                    // price_volume 파티션 생성
                    partitionManagementService.createVolumePartition(partitionInfo);
                    log.info("파티션 생성 완료: {}", partitionInfo.get("symbol"));
                } catch (Exception e) {
                    log.error("파티션 생성 실패: {}", partitionInfo.get("symbol"), e);
                }
            }
        };
    }

    // ========== Step 2: 파티션 상태 체크 ==========

    /**
     * 파티션 상태 체크 Step (Tasklet)
     */
    @Bean
    public Step checkPartitionHealthStep() {
        return new StepBuilder("checkPartitionHealthStep", jobRepository)
                .tasklet(checkPartitionHealthTasklet(), transactionManager)
                .build();
    }

    /**
     * 파티션 상태 체크 Tasklet
     */
    @Bean
    @StepScope
    public Tasklet checkPartitionHealthTasklet() {
        return (contribution, chunkContext) -> {
            log.info("파티션 상태 체크 시작");
            
            // 파티션 크기 체크
            List<Map<String, Object>> partitionSizes = partitionManagementService.checkPartitionSizes();
            for (Map<String, Object> partition : partitionSizes) {
                String tableName = (String) partition.get("table_name");
                Long sizeBytes = (Long) partition.get("size_bytes");
                Long rowCount = (Long) partition.get("row_count");
                
                log.info("파티션 상태 - 테이블: {}, 크기: {} MB, 행수: {}", 
                    tableName, 
                    sizeBytes / 1024 / 1024,
                    rowCount
                );
                
                // 파티션이 너무 크면 경고
                if (sizeBytes > 10L * 1024 * 1024 * 1024) { // 10GB
                    log.warn("파티션 크기 경고 - 테이블: {}, 크기: {} GB", 
                        tableName, sizeBytes / 1024 / 1024 / 1024);
                }
            }
            
            // TimescaleDB 청크 상태 체크
            partitionManagementService.checkTimescaleChunks();
            
            log.info("파티션 상태 체크 완료");
            return RepeatStatus.FINISHED;
        };
    }

    // ========== Step 3: 파티션 최적화 ==========

    /**
     * 파티션 최적화 Step (Tasklet)
     */
    @Bean
    public Step optimizePartitionStep() {
        return new StepBuilder("optimizePartitionStep", jobRepository)
                .tasklet(optimizePartitionTasklet(), transactionManager)
                .build();
    }

    /**
     * 파티션 최적화 Tasklet
     */
    @Bean
    @StepScope
    public Tasklet optimizePartitionTasklet() {
        return (contribution, chunkContext) -> {
            log.info("파티션 최적화 시작");
            
            // VACUUM 실행 (데드 튜플 정리)
            partitionManagementService.vacuumPartitions();
            
            // 인덱스 재구성
            partitionManagementService.reindexPartitions();
            
            // 통계 업데이트
            partitionManagementService.analyzePartitions();
            
            log.info("파티션 최적화 완료");
            return RepeatStatus.FINISHED;
        };
    }

    // ========== Listeners ==========

    @Bean
    public StepExecutionListener createPartitionListener() {
        return new StepExecutionListener() {
            @Override
            public void beforeStep(@NonNull StepExecution stepExecution) {
                log.info("🔹 [파티션 생성] 시작");
            }
            
            @Override
            public ExitStatus afterStep(@NonNull StepExecution stepExecution) {
                log.info("🔸 [파티션 생성] 종료 - 상태: {}", stepExecution.getStatus());
                return stepExecution.getExitStatus();
            }
        };
    }

    @Bean
    public JobExecutionListener partitionJobListener() {
        return new JobExecutionListener() {
            @Override
            public void beforeJob(@NonNull JobExecution jobExecution) {
                log.info("===== 파티션 관리 Job 시작 =====");
            }
            
            @Override
            public void afterJob(@NonNull JobExecution jobExecution) {
                log.info("===== 파티션 관리 Job 종료: {} =====", jobExecution.getStatus());
                if (jobExecution.getStatus() == BatchStatus.FAILED) {
                    log.error("파티션 관리 Job 실패!");
                }
            }
        };
    }
}