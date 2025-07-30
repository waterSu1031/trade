package com.trade.batch.job;

import com.trade.batch.service.DataIntegrityService;
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
 * 데이터 정합성 검증 배치 Job
 * - 포지션 정합성 검증
 * - 손익 계산 검증
 * - 중복 데이터 제거
 * - 데이터 일관성 체크
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class DataIntegrityJob {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;
    private final DataIntegrityService dataIntegrityService;

    /**
     * 데이터 정합성 검증 메인 Job
     * 1. 포지션 정합성 검증
     * 2. 손익 재계산 및 검증
     * 3. 중복 데이터 체크
     * 4. 참조 무결성 검증
     */
    @Bean
    public Job verifyDataIntegrityJob() {
        return new JobBuilder("verifyDataIntegrityJob", jobRepository)
                .start(verifyPositionIntegrityStep())      // 포지션 정합성
                .next(verifyPnLCalculationStep())           // 손익 검증
                .next(detectDuplicateDataStep())            // 중복 체크
                .next(verifyReferentialIntegrityStep())     // 참조 무결성
                .listener(integrityJobListener())
                .build();
    }

    // ========== Step 1: 포지션 정합성 검증 ==========

    /**
     * 포지션 정합성 검증 Step
     */
    @Bean
    public Step verifyPositionIntegrityStep() {
        return new StepBuilder("verifyPositionIntegrityStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(20, transactionManager)
                .reader(positionVerificationReader())
                .processor(positionVerificationProcessor())
                .writer(positionVerificationWriter())
                .listener(positionIntegrityListener())
                .build();
    }

    /**
     * 검증할 포지션 목록 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> positionVerificationReader() {
        // 현재 포지션이 있는 모든 종목
        List<Map<String, Object>> positions = dataIntegrityService.getCurrentPositions();
        log.info("포지션 정합성 검증 대상: {} 종목", positions.size());
        return new ListItemReader<>(positions);
    }

    /**
     * 포지션 정합성 검증 처리
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> positionVerificationProcessor() {
        return position -> {
            String symbol = (String) position.get("symbol");
            
            // trade_events 기반 포지션 재계산
            Map<String, Object> recalculated = dataIntegrityService.recalculatePosition(symbol);
            
            // 현재 포지션과 비교
            Double currentPosition = ((Number) position.get("position")).doubleValue();
            Double recalculatedPosition = ((Number) recalculated.get("position")).doubleValue();
            
            position.put("recalculated_position", recalculatedPosition);
            position.put("position_diff", Math.abs(currentPosition - recalculatedPosition));
            position.put("is_valid", Math.abs(currentPosition - recalculatedPosition) < 0.0001);
            
            if (!((Boolean) position.get("is_valid"))) {
                log.warn("포지션 불일치 발견 - {}: 현재={}, 재계산={}", 
                    symbol, currentPosition, recalculatedPosition);
            }
            
            return position;
        };
    }

    /**
     * 포지션 정합성 검증 결과 저장
     */
    @Bean
    public ItemWriter<Map<String, Object>> positionVerificationWriter() {
        return verificationResults -> {
            for (Map<String, Object> result : verificationResults) {
                if (!((Boolean) result.get("is_valid"))) {
                    // 불일치 포지션 수정
                    dataIntegrityService.correctPosition(result);
                    log.info("포지션 수정 완료: {}", result.get("symbol"));
                }
                
                // 검증 로그 저장
                dataIntegrityService.saveVerificationLog("POSITION", result);
            }
        };
    }

    // ========== Step 2: 손익 재계산 및 검증 ==========

    /**
     * 손익 검증 Step
     */
    @Bean
    public Step verifyPnLCalculationStep() {
        return new StepBuilder("verifyPnLCalculationStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(50, transactionManager)
                .reader(pnlVerificationReader())
                .processor(pnlVerificationProcessor())
                .writer(pnlVerificationWriter())
                .build();
    }

    /**
     * 손익 검증 대상 거래 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> pnlVerificationReader() {
        // 최근 30일간의 거래 중 손익이 있는 거래
        List<Map<String, Object>> trades = dataIntegrityService.getRecentTradesWithPnL();
        log.info("손익 검증 대상 거래: {} 건", trades.size());
        return new ListItemReader<>(trades);
    }

    /**
     * 손익 재계산 처리
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> pnlVerificationProcessor() {
        return trade -> {
            String execId = (String) trade.get("execId");
            
            // FIFO 기반 손익 재계산
            Map<String, Object> recalculated = dataIntegrityService.recalculatePnL(trade);
            
            Double currentPnL = ((Number) trade.get("realizedPNL")).doubleValue();
            Double recalculatedPnL = ((Number) recalculated.get("realizedPNL")).doubleValue();
            
            trade.put("recalculated_pnl", recalculatedPnL);
            trade.put("pnl_diff", Math.abs(currentPnL - recalculatedPnL));
            trade.put("is_valid", Math.abs(currentPnL - recalculatedPnL) < 0.01); // 0.01 허용 오차
            
            if (!((Boolean) trade.get("is_valid"))) {
                log.warn("손익 불일치 발견 - execId={}: 현재={}, 재계산={}", 
                    execId, currentPnL, recalculatedPnL);
            }
            
            return trade;
        };
    }

    /**
     * 손익 검증 결과 저장
     */
    @Bean
    public ItemWriter<Map<String, Object>> pnlVerificationWriter() {
        return verificationResults -> {
            int correctedCount = 0;
            
            for (Map<String, Object> result : verificationResults) {
                if (!((Boolean) result.get("is_valid"))) {
                    // 손익 수정
                    dataIntegrityService.correctPnL(result);
                    correctedCount++;
                }
                
                // 검증 로그 저장
                dataIntegrityService.saveVerificationLog("PNL", result);
            }
            
            if (correctedCount > 0) {
                log.info("손익 수정 완료: {} 건", correctedCount);
            }
        };
    }

    // ========== Step 3: 중복 데이터 체크 ==========

    /**
     * 중복 데이터 검출 Step (Tasklet)
     */
    @Bean
    public Step detectDuplicateDataStep() {
        return new StepBuilder("detectDuplicateDataStep", jobRepository)
                .tasklet(detectDuplicateTasklet(), transactionManager)
                .build();
    }

    /**
     * 중복 데이터 검출 Tasklet
     */
    @Bean
    @StepScope
    public Tasklet detectDuplicateTasklet() {
        return (contribution, chunkContext) -> {
            log.info("중복 데이터 검출 시작");
            
            // trade_events 중복 체크
            List<Map<String, Object>> duplicateTrades = dataIntegrityService.findDuplicateTrades();
            if (!duplicateTrades.isEmpty()) {
                log.warn("중복 거래 발견: {} 건", duplicateTrades.size());
                
                // 중복 제거
                int removed = dataIntegrityService.removeDuplicateTrades(duplicateTrades);
                log.info("중복 거래 제거 완료: {} 건", removed);
            }
            
            // orders 중복 체크
            List<Map<String, Object>> duplicateOrders = dataIntegrityService.findDuplicateOrders();
            if (!duplicateOrders.isEmpty()) {
                log.warn("중복 주문 발견: {} 건", duplicateOrders.size());
                
                // 중복 제거
                int removed = dataIntegrityService.removeDuplicateOrders(duplicateOrders);
                log.info("중복 주문 제거 완료: {} 건", removed);
            }
            
            // price 데이터 중복 체크
            Map<String, Integer> priceDuplicates = dataIntegrityService.checkPriceDataDuplicates();
            for (Map.Entry<String, Integer> entry : priceDuplicates.entrySet()) {
                if (entry.getValue() > 0) {
                    log.warn("{} 테이블에서 {} 건의 중복 발견", 
                        entry.getKey(), entry.getValue());
                }
            }
            
            log.info("중복 데이터 검출 완료");
            return RepeatStatus.FINISHED;
        };
    }

    // ========== Step 4: 참조 무결성 검증 ==========

    /**
     * 참조 무결성 검증 Step (Tasklet)
     */
    @Bean
    public Step verifyReferentialIntegrityStep() {
        return new StepBuilder("verifyReferentialIntegrityStep", jobRepository)
                .tasklet(referentialIntegrityTasklet(), transactionManager)
                .build();
    }

    /**
     * 참조 무결성 검증 Tasklet
     */
    @Bean
    @StepScope
    public Tasklet referentialIntegrityTasklet() {
        return (contribution, chunkContext) -> {
            log.info("참조 무결성 검증 시작");
            
            Map<String, List<Map<String, Object>>> integrityIssues = 
                dataIntegrityService.checkReferentialIntegrity();
            
            boolean hasIssues = false;
            
            // trade_events의 orderId 검증
            List<Map<String, Object>> orphanTrades = integrityIssues.get("orphan_trades");
            if (!orphanTrades.isEmpty()) {
                log.error("고아 거래 발견 (orderId가 orders에 없음): {} 건", orphanTrades.size());
                hasIssues = true;
            }
            
            // orders의 symbol 검증
            List<Map<String, Object>> invalidSymbols = integrityIssues.get("invalid_symbols");
            if (!invalidSymbols.isEmpty()) {
                log.error("잘못된 심볼 발견 (contracts에 없음): {} 건", invalidSymbols.size());
                hasIssues = true;
            }
            
            // price 데이터의 conId 검증
            List<Map<String, Object>> invalidConIds = integrityIssues.get("invalid_conids");
            if (!invalidConIds.isEmpty()) {
                log.error("잘못된 conId 발견: {} 건", invalidConIds.size());
                hasIssues = true;
            }
            
            if (!hasIssues) {
                log.info("참조 무결성 검증 통과 - 문제 없음");
            } else {
                // 문제 해결 옵션 제공
                dataIntegrityService.generateIntegrityReport(integrityIssues);
            }
            
            log.info("참조 무결성 검증 완료");
            return RepeatStatus.FINISHED;
        };
    }

    // ========== Listeners ==========

    @Bean
    public StepExecutionListener positionIntegrityListener() {
        return new StepExecutionListener() {
            @Override
            public void beforeStep(@NonNull StepExecution stepExecution) {
                log.info("🔹 [포지션 정합성 검증] 시작");
            }
            
            @Override
            public ExitStatus afterStep(@NonNull StepExecution stepExecution) {
                int errorCount = (int) stepExecution.getExecutionContext()
                    .getOrDefault("position_errors", 0);
                
                if (errorCount > 0) {
                    log.warn("🔸 [포지션 정합성 검증] 완료 - {} 개 오류 수정", errorCount);
                } else {
                    log.info("🔸 [포지션 정합성 검증] 완료 - 모든 포지션 정상");
                }
                
                return stepExecution.getExitStatus();
            }
        };
    }

    @Bean
    public JobExecutionListener integrityJobListener() {
        return new JobExecutionListener() {
            @Override
            public void beforeJob(@NonNull JobExecution jobExecution) {
                log.info("===== 데이터 정합성 검증 Job 시작 =====");
                
                // 검증 전 백업 권장
                log.info("주의: 데이터 수정이 발생할 수 있습니다. 백업을 권장합니다.");
            }
            
            @Override
            public void afterJob(@NonNull JobExecution jobExecution) {
                log.info("===== 데이터 정합성 검증 Job 종료: {} =====", 
                    jobExecution.getStatus());
                
                if (jobExecution.getStatus() == BatchStatus.COMPLETED) {
                    // 전체 검증 요약 리포트
                    Map<String, Object> summary = dataIntegrityService.getVerificationSummary();
                    
                    log.info("========== 정합성 검증 요약 ==========");
                    log.info("검증된 포지션: {} 개", summary.get("verified_positions"));
                    log.info("수정된 포지션: {} 개", summary.get("corrected_positions"));
                    log.info("검증된 손익: {} 건", summary.get("verified_pnl"));
                    log.info("수정된 손익: {} 건", summary.get("corrected_pnl"));
                    log.info("제거된 중복: {} 건", summary.get("removed_duplicates"));
                    log.info("참조 무결성 문제: {} 건", summary.get("integrity_issues"));
                    log.info("=====================================");
                }
            }
        };
    }
}