package com.trade.batch.job;

import com.trade.batch.service.DailyStatisticsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.*;
import org.springframework.batch.core.configuration.annotation.StepScope;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.batch.item.support.ListItemReader;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.lang.NonNull;
import org.springframework.transaction.PlatformTransactionManager;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 일별 통계 집계 배치 Job
 * - trade_events 테이블에서 일별 거래 통계 집계
 * - daily_statistics 테이블에 저장
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class DailyStatisticsJob {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;
    private final DailyStatisticsService dailyStatisticsService;

    /**
     * 일별 통계 집계 메인 Job
     * 1. 일별 거래 통계 집계
     * 2. 종목별 통계 집계
     * 3. 전체 포트폴리오 통계 집계
     */
    @Bean
    public Job calculateDailyStatisticsJob() {
        return new JobBuilder("calculateDailyStatisticsJob", jobRepository)
                .start(aggregateDailyTradeStep())         // 일별 거래 통계
                .next(aggregateSymbolStatisticsStep())     // 종목별 통계
                .next(calculatePortfolioMetricsStep())     // 포트폴리오 메트릭
                .listener(dailyStatisticsJobListener())
                .build();
    }

    // ========== Step 1: 일별 거래 통계 집계 ==========

    /**
     * 일별 거래 통계 집계 Step
     */
    @Bean
    public Step aggregateDailyTradeStep() {
        return new StepBuilder("aggregateDailyTradeStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(10, transactionManager)
                .reader(dailyTradeReader())
                .processor(dailyTradeProcessor())
                .writer(dailyStatisticsWriter())
                .listener(dailyTradeStepListener())
                .build();
    }

    /**
     * 집계할 날짜 목록 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> dailyTradeReader() {
        // 아직 집계되지 않은 날짜 또는 최근 7일간의 데이터 재집계
        List<Map<String, Object>> dates = dailyStatisticsService.findDatesToAggregate();
        log.info("일별 통계 집계 대상 날짜 수: {}", dates.size());
        return new ListItemReader<>(dates);
    }

    /**
     * 일별 거래 통계 처리
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> dailyTradeProcessor() {
        return dateInfo -> {
            LocalDate tradeDate = (LocalDate) dateInfo.get("trade_date");
            log.debug("일별 통계 집계 중: {}", tradeDate);
            
            // trade_events에서 해당 날짜의 통계 집계
            Map<String, Object> dailyStats = dailyStatisticsService.aggregateDailyStatistics(tradeDate);
            
            // 추가 메트릭 계산
            dailyStats.put("win_rate", calculateWinRate(dailyStats));
            dailyStats.put("profit_factor", calculateProfitFactor(dailyStats));
            
            return dailyStats;
        };
    }

    /**
     * 일별 통계 저장
     */
    @Bean
    public ItemWriter<Map<String, Object>> dailyStatisticsWriter() {
        return statisticsList -> {
            for (Map<String, Object> statistics : statisticsList) {
                try {
                    dailyStatisticsService.saveDailyStatistics(statistics);
                    log.info("일별 통계 저장 완료: {}", statistics.get("date"));
                } catch (Exception e) {
                    log.error("일별 통계 저장 실패: {}", statistics.get("date"), e);
                }
            }
        };
    }

    // ========== Step 2: 종목별 통계 집계 ==========

    /**
     * 종목별 통계 집계 Step
     */
    @Bean
    public Step aggregateSymbolStatisticsStep() {
        return new StepBuilder("aggregateSymbolStatisticsStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(20, transactionManager)
                .reader(symbolStatisticsReader())
                .processor(symbolStatisticsProcessor())
                .writer(symbolStatisticsWriter())
                .build();
    }

    /**
     * 통계 집계할 종목 목록 조회
     */
    @Bean
    @StepScope
    public ItemReader<Map<String, Object>> symbolStatisticsReader() {
        // 최근 거래가 있었던 종목들
        List<Map<String, Object>> symbols = dailyStatisticsService.findActiveSymbols();
        log.info("종목별 통계 집계 대상: {} 종목", symbols.size());
        return new ListItemReader<>(symbols);
    }

    /**
     * 종목별 통계 처리
     */
    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> symbolStatisticsProcessor() {
        return symbolInfo -> {
            String symbol = (String) symbolInfo.get("symbol");
            
            // 종목별 통계 집계
            Map<String, Object> symbolStats = dailyStatisticsService.aggregateSymbolStatistics(symbol);
            
            // 추가 지표 계산
            symbolStats.put("sharpe_ratio", calculateSharpeRatio(symbolStats));
            symbolStats.put("max_drawdown", calculateMaxDrawdown(symbolStats));
            
            return symbolStats;
        };
    }

    /**
     * 종목별 통계 저장
     */
    @Bean
    public ItemWriter<Map<String, Object>> symbolStatisticsWriter() {
        return symbolStatsList -> {
            for (Map<String, Object> symbolStats : symbolStatsList) {
                try {
                    // 종목별 통계는 별도 테이블이나 daily_statistics에 통합 저장
                    dailyStatisticsService.saveSymbolStatistics(symbolStats);
                    log.debug("종목별 통계 저장 완료: {}", symbolStats.get("symbol"));
                } catch (Exception e) {
                    log.error("종목별 통계 저장 실패: {}", symbolStats.get("symbol"), e);
                }
            }
        };
    }

    // ========== Step 3: 포트폴리오 메트릭 계산 ==========

    /**
     * 포트폴리오 전체 메트릭 계산 Step
     */
    @Bean
    public Step calculatePortfolioMetricsStep() {
        return new StepBuilder("calculatePortfolioMetricsStep", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    log.info("포트폴리오 메트릭 계산 시작");
                    
                    try {
                        // 전체 포트폴리오 성과 계산
                        Map<String, Object> portfolioMetrics = dailyStatisticsService.calculatePortfolioMetrics();
                        
                        // 리스크 메트릭 계산
                        portfolioMetrics.put("portfolio_var", calculateVaR(portfolioMetrics));
                        portfolioMetrics.put("portfolio_beta", calculateBeta(portfolioMetrics));
                        
                        // 저장
                        dailyStatisticsService.savePortfolioMetrics(portfolioMetrics);
                        
                        log.info("포트폴리오 메트릭 계산 완료 - Sharpe: {}, MaxDD: {}", 
                            portfolioMetrics.get("sharpe_ratio"),
                            portfolioMetrics.get("max_drawdown"));
                            
                    } catch (Exception e) {
                        log.error("포트폴리오 메트릭 계산 실패", e);
                        throw e;
                    }
                    
                    return RepeatStatus.FINISHED;
                }, transactionManager)
                .build();
    }

    // ========== 유틸리티 메서드 ==========

    /**
     * 승률 계산
     */
    private Double calculateWinRate(Map<String, Object> stats) {
        Integer winTrades = (Integer) stats.getOrDefault("winTrades", 0);
        Integer totalTrades = (Integer) stats.getOrDefault("totalTrades", 0);
        
        if (totalTrades == 0) return 0.0;
        return (double) winTrades / totalTrades * 100;
    }

    /**
     * Profit Factor 계산
     */
    private Double calculateProfitFactor(Map<String, Object> stats) {
        Double grossProfit = (Double) stats.getOrDefault("grossProfit", 0.0);
        Double grossLoss = Math.abs((Double) stats.getOrDefault("grossLoss", 0.0));
        
        if (grossLoss == 0) return grossProfit > 0 ? 999.99 : 0.0;
        return grossProfit / grossLoss;
    }

    /**
     * Sharpe Ratio 계산 (간단 버전)
     */
    private Double calculateSharpeRatio(Map<String, Object> stats) {
        Double avgReturn = (Double) stats.getOrDefault("avgReturn", 0.0);
        Double stdDev = (Double) stats.getOrDefault("stdDev", 0.0);
        Double riskFreeRate = 0.02; // 연 2% 가정
        
        if (stdDev == 0) return 0.0;
        return (avgReturn - riskFreeRate) / stdDev * Math.sqrt(252); // 연율화
    }

    /**
     * 최대 낙폭 계산
     */
    private Double calculateMaxDrawdown(Map<String, Object> stats) {
        // 실제로는 시계열 데이터에서 계산해야 함
        return (Double) stats.getOrDefault("maxDrawdown", 0.0);
    }

    /**
     * VaR (Value at Risk) 계산
     */
    private Double calculateVaR(Map<String, Object> metrics) {
        // 95% 신뢰수준 VaR 계산 (간단 버전)
        Double portfolioValue = (Double) metrics.getOrDefault("totalValue", 0.0);
        Double volatility = (Double) metrics.getOrDefault("volatility", 0.0);
        return portfolioValue * volatility * 1.645; // 95% z-score
    }

    /**
     * 베타 계산
     */
    private Double calculateBeta(Map<String, Object> metrics) {
        // 벤치마크 대비 베타 계산 (간단 버전)
        return (Double) metrics.getOrDefault("beta", 1.0);
    }

    // ========== Listeners ==========

    @Bean
    public StepExecutionListener dailyTradeStepListener() {
        return new StepExecutionListener() {
            @Override
            public void beforeStep(@NonNull StepExecution stepExecution) {
                log.info("🔹 [일별 거래 통계 집계] 시작");
            }
            
            @Override
            public ExitStatus afterStep(@NonNull StepExecution stepExecution) {
                log.info("🔸 [일별 거래 통계 집계] 종료 - 처리: {} 건", 
                    stepExecution.getWriteCount());
                return stepExecution.getExitStatus();
            }
        };
    }

    @Bean
    public JobExecutionListener dailyStatisticsJobListener() {
        return new JobExecutionListener() {
            @Override
            public void beforeJob(@NonNull JobExecution jobExecution) {
                log.info("===== 일별 통계 집계 Job 시작 =====");
            }
            
            @Override
            public void afterJob(@NonNull JobExecution jobExecution) {
                log.info("===== 일별 통계 집계 Job 종료: {} =====", jobExecution.getStatus());
                
                // Job 파라미터에서 처리 날짜 정보 출력
                JobParameters params = jobExecution.getJobParameters();
                if (params.getString("targetDate") != null) {
                    log.info("처리 날짜: {}", params.getString("targetDate"));
                }
            }
        };
    }
}