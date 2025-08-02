package com.trade.batch.endpoint;

import com.trade.batch.service.TradingHourService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Component
@Slf4j
@RequiredArgsConstructor
public class BatchScheduler {

    private final JobLauncher jobLauncher;
    private final Job setInitStructureJob;
    private final Job addFutureMonthJob;
    private final Job collectTypeDataJob;
    private final Job taskletJob;
    private final TradingHourService tradingHourService;

    public void runJob(Job job, String jobName) {
        try {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            log.info("[{}] 실행 시작 - {}", jobName, timestamp);

            JobExecution execution = jobLauncher.run(
                    job, new JobParametersBuilder()
                            .addString("requestTime", timestamp)
                            .toJobParameters()
            );

            log.info("[{}] 실행 종료 - status: {}", jobName, execution.getStatus());
        } catch (Exception e) {
            log.error("[{}] 실행 중 오류 발생: {}", jobName, e.getMessage(), e);
        }
    }

    @Scheduled(cron = "0 0 7 * * ?") // 매일 7시 - CME 일일 정산 후, 아시아 개장 전
    public void scheduleSetInitStructureJob() {
        runJob(setInitStructureJob, "setInitStructureJob");
    }

    @Scheduled(cron = "0 30 7 * * ?") // 매일 7시 30분 - 초기 구조 설정 후 선물 월물 추가
    public void scheduleAddFutureMonthJob() {
        runJob(addFutureMonthJob, "addFutureMonthJob");
    }

    @Scheduled(cron = "0 0 18 * * ?") // 매일 18시 - 아시아 마감 후, 유럽 본격 시작 전
    public void scheduleCollectTypeDataJob() {
        runJob(collectTypeDataJob, "collectTypeDataJob");
    }

    @Scheduled(cron = "0 30 6 * * ?") // 매일 6시 30분 - 미국 마감 후, 아시아 개장 전
    public void scheduleTaskletJob() {
        runJob(taskletJob, "taskletJob");
    }
    
    // 수동 실행을 위한 public 메서드들
    public void runSetInitStructureJob() {
        runJob(setInitStructureJob, "setInitStructureJob");
    }
    
    public void runAddFutureMonthJob() {
        runJob(addFutureMonthJob, "addFutureMonthJob");
    }
    
    public void runCollectTypeDataJob() {
        runJob(collectTypeDataJob, "collectTypeDataJob");
    }
    
    public void runTaskletJob() {
        runJob(taskletJob, "taskletJob");
    }

    /**
     * 매주 일요일 새벽 5시에 거래시간 업데이트
     * - 각 거래소별 1주일치 거래시간을 IBKR에서 조회
     * - 휴일 정보 자동 감지
     */
    @Scheduled(cron = "0 0 5 * * SUN")
    public void updateWeeklyTradingHours() {
        log.info("=== Weekly Trading Hours Update Started ===");
        
        try {
            // 모든 거래소의 거래시간 업데이트
            tradingHourService.updateWeeklyTradingHours();
            
            // 오래된 캐시 정리 (3개월 이상)
            tradingHourService.cleanupOldCache();
            
            log.info("=== Weekly Trading Hours Update Completed Successfully ===");
        } catch (Exception e) {
            log.error("Failed to update weekly trading hours", e);
        }
    }
    
    /**
     * 매일 자정에 거래시간 캐시 확인 (선택적)
     * - 캐시가 부족한 경우 추가 업데이트
     */
    @Scheduled(cron = "0 0 0 * * ?")
    public void checkTradingHoursCache() {
        log.debug("Checking trading hours cache status...");
        
        // 주요 거래소의 캐시 상태 확인
        for (String exchange : TradingHourService.EXCHANGE_SYMBOLS.keySet()) {
            try {
                if (!tradingHourService.isTradingDay(exchange, LocalDateTime.now().toLocalDate())) {
                    log.debug("{} is not a trading day today", exchange);
                }
            } catch (Exception e) {
                log.error("Error checking trading hours for {}", exchange, e);
            }
        }
    }
}
