package com.trade.batch.job;

import com.trade.batch.service.DataSyncService;
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

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 데이터 동기화 배치 Job
 * - PostgreSQL → DuckDB 동기화
 * - 마스터 데이터 갱신
 * - 실시간 데이터 백업
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class DataSyncJob {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;
    private final DataSyncService dataSyncService;

    /**
     * 데이터 동기화 메인 Job
     * 1. 마스터 데이터 동기화
     * 2. 거래 데이터 동기화 (PostgreSQL → DuckDB)
     * 3. 가격 데이터 동기화
     * 4. 동기화 검증
     */
    @Bean
    public Job synchronizeDataJob() {
        return new JobBuilder("synchronizeDataJob", jobRepository)
                .start(syncMasterDataStep())           // 마스터 데이터
                .next(syncTradeEventsStep())            // 거래 이벤트
                .next(syncPriceDataStep())              // 가격 데이터
                .next(verifySyncStep())                 // 동기화 검증
                .listener(syncJobListener())
                .build();
    }

    // ========== Step 1: 마스터 데이터 동기화 ==========

    /**
     * 마스터 데이터 동기화 Step
     */
    @Bean
    public Step syncMasterDataStep() {
        return new StepBuilder("syncMasterDataStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(100, transactionManager)
                .reader(masterDataReader())
                .processor(masterDataProcessor())
                .writer(masterDataWriter())
                .listener(masterDataSyncListener())
                .build();
    }

    /**
     * 동기화할 마스터 데이터 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> masterDataReader() {
        // contracts, exchanges 등 마스터 데이터 변경사항 조회
        List<Map<String, Object>> masterData = dataSyncService.getUpdatedMasterData();
        log.info("마스터 데이터 동기화 대상: {} 건", masterData.size());
        return new ListItemReader<>(masterData);
    }

    /**
     * 마스터 데이터 처리
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> masterDataProcessor() {
        return data -> {
            // 데이터 변환 및 검증
            Map<String, Object> processed = dataSyncService.processMasterData(data);
            processed.put("sync_timestamp", LocalDateTime.now());
            return processed;
        };
    }

    /**
     * 마스터 데이터 DuckDB 저장
     */
    @Bean
    public ItemWriter<Map<String, Object>> masterDataWriter() {
        return dataList -> {
            for (Map<String, Object> data : dataList) {
                try {
                    dataSyncService.syncMasterDataToDuckDB(data);
                    log.debug("마스터 데이터 동기화: {}", data.get("table_name"));
                } catch (Exception e) {
                    log.error("마스터 데이터 동기화 실패: {}", data.get("table_name"), e);
                }
            }
        };
    }

    // ========== Step 2: 거래 이벤트 동기화 ==========

    /**
     * 거래 이벤트 동기화 Step
     */
    @Bean
    public Step syncTradeEventsStep() {
        return new StepBuilder("syncTradeEventsStep", jobRepository)
                .tasklet(tradeEventsSyncTasklet(), transactionManager)
                .build();
    }

    /**
     * 거래 이벤트 동기화 Tasklet
     */
    @Bean
    @StepScope
    public Tasklet tradeEventsSyncTasklet() {
        return (contribution, chunkContext) -> {
            log.info("거래 이벤트 동기화 시작");
            
            // 마지막 동기화 시점 조회
            LocalDateTime lastSyncTime = dataSyncService.getLastSyncTime("trade_events");
            log.info("마지막 동기화: {}", lastSyncTime);
            
            // 증분 데이터 동기화
            int syncedCount = dataSyncService.syncTradeEvents(lastSyncTime);
            log.info("거래 이벤트 동기화 완료: {} 건", syncedCount);
            
            // 일별 집계 데이터도 동기화
            int aggregatedCount = dataSyncService.syncDailyAggregates();
            log.info("일별 집계 동기화 완료: {} 건", aggregatedCount);
            
            // 동기화 시점 업데이트
            dataSyncService.updateSyncTime("trade_events", LocalDateTime.now());
            
            return RepeatStatus.FINISHED;
        };
    }

    // ========== Step 3: 가격 데이터 동기화 ==========

    /**
     * 가격 데이터 동기화 Step
     */
    @Bean
    public Step syncPriceDataStep() {
        return new StepBuilder("syncPriceDataStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(1000, transactionManager)
                .reader(priceDataReader())
                .processor(priceDataProcessor())
                .writer(priceDataWriter())
                .build();
    }

    /**
     * 동기화할 가격 데이터 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> priceDataReader() {
        // 최근 업데이트된 가격 데이터 배치로 조회
        List<Map<String, Object>> priceData = dataSyncService.getRecentPriceData();
        log.info("가격 데이터 동기화 대상: {} 건", priceData.size());
        return new ListItemReader<>(priceData);
    }

    /**
     * 가격 데이터 처리 (집계 포함)
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> priceDataProcessor() {
        return priceData -> {
            String dataType = (String) priceData.get("data_type");
            
            // 데이터 타입별 처리
            if ("time".equals(dataType)) {
                // 시계열 데이터는 집계하여 저장
                return dataSyncService.aggregatePriceData(priceData);
            } else {
                // Range/Volume 데이터는 그대로 저장
                return priceData;
            }
        };
    }

    /**
     * 가격 데이터 DuckDB 저장
     */
    @Bean
    public ItemWriter<Map<String, Object>> priceDataWriter() {
        return priceDataList -> {
            // 배치로 DuckDB에 저장
            dataSyncService.bulkInsertPriceData(new ArrayList<>(priceDataList.getItems()));
            log.debug("가격 데이터 {} 건 동기화 완료", priceDataList.size());
        };
    }

    // ========== Step 4: 동기화 검증 ==========

    /**
     * 동기화 검증 Step
     */
    @Bean
    public Step verifySyncStep() {
        return new StepBuilder("verifySyncStep", jobRepository)
                .tasklet(verifySyncTasklet(), transactionManager)
                .build();
    }

    /**
     * 동기화 검증 Tasklet
     */
    @Bean
    @StepScope
    public Tasklet verifySyncTasklet() {
        return (contribution, chunkContext) -> {
            log.info("동기화 검증 시작");
            
            Map<String, Object> verificationResult = dataSyncService.verifySynchronization();
            
            // PostgreSQL vs DuckDB 레코드 수 비교
            log.info("========== 동기화 검증 결과 ==========");
            
            for (Map.Entry<String, Object> entry : verificationResult.entrySet()) {
                String tableName = entry.getKey();
                Map<String, Object> counts = (Map<String, Object>) entry.getValue();
                
                Long pgCount = (Long) counts.get("postgresql_count");
                Long duckCount = (Long) counts.get("duckdb_count");
                Long diff = Math.abs(pgCount - duckCount);
                
                if (diff > 0) {
                    log.warn("{} - PostgreSQL: {}, DuckDB: {} (차이: {})", 
                        tableName, pgCount, duckCount, diff);
                } else {
                    log.info("{} - 동기화 완료: {} 건", tableName, pgCount);
                }
            }
            
            // 데이터 품질 체크
            Map<String, Object> qualityCheck = dataSyncService.checkDataQuality();
            
            if (!qualityCheck.isEmpty()) {
                log.warn("데이터 품질 문제:");
                qualityCheck.forEach((k, v) -> log.warn("  - {}: {}", k, v));
            }
            
            log.info("====================================");
            
            return RepeatStatus.FINISHED;
        };
    }

    // ========== Listeners ==========

    @Bean
    public StepExecutionListener masterDataSyncListener() {
        return new StepExecutionListener() {
            @Override
            public void beforeStep(@NonNull StepExecution stepExecution) {
                log.info("🔹 [마스터 데이터 동기화] 시작");
            }
            
            @Override
            public ExitStatus afterStep(@NonNull StepExecution stepExecution) {
                log.info("🔸 [마스터 데이터 동기화] 완료 - {} 건 처리", 
                    stepExecution.getWriteCount());
                return stepExecution.getExitStatus();
            }
        };
    }

    @Bean
    public JobExecutionListener syncJobListener() {
        return new JobExecutionListener() {
            @Override
            public void beforeJob(@NonNull JobExecution jobExecution) {
                log.info("===== 데이터 동기화 Job 시작 =====");
                
                // DuckDB 연결 테스트
                if (!dataSyncService.testDuckDBConnection()) {
                    log.error("DuckDB 연결 실패! Job을 중단합니다.");
                    throw new RuntimeException("DuckDB connection failed");
                }
                
                log.info("DuckDB 연결 성공");
            }
            
            @Override
            public void afterJob(@NonNull JobExecution jobExecution) {
                log.info("===== 데이터 동기화 Job 종료: {} =====", 
                    jobExecution.getStatus());
                
                if (jobExecution.getStatus() == BatchStatus.COMPLETED) {
                    // 동기화 통계 출력
                    Map<String, Object> syncStats = dataSyncService.getSyncStatistics();
                    
                    log.info("========== 동기화 통계 ==========");
                    log.info("총 동기화 테이블: {} 개", syncStats.get("total_tables"));
                    log.info("동기화된 레코드: {} 건", syncStats.get("total_records"));
                    log.info("소요 시간: {} 초", syncStats.get("duration_seconds"));
                    log.info("평균 처리 속도: {} records/sec", syncStats.get("avg_speed"));
                    log.info("================================");
                    
                    // 다음 동기화 예정 시간
                    log.info("다음 동기화 예정: {}", dataSyncService.getNextSyncSchedule());
                }
            }
        };
    }
}