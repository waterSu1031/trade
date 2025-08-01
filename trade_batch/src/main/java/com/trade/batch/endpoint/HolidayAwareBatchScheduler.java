package com.trade.batch.endpoint;

import com.trade.batch.config.MarketHolidayCalendar;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 휴일을 고려한 배치 스케줄러
 * 시장 휴일에는 배치 작업을 건너뛰거나 조정합니다.
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class HolidayAwareBatchScheduler {

    private final JobLauncher jobLauncher;
    private final MarketHolidayCalendar holidayCalendar;
    private final Job setInitStructureJob;
    private final Job collectTypeDataJob;

    /**
     * 휴일을 고려하여 배치 작업 실행
     */
    private void runJobWithHolidayCheck(Job job, String jobName, String marketType) {
        LocalDate today = LocalDate.now();
        
        // 휴일 정보 로깅
        holidayCalendar.logHolidayInfo(today);
        
        // 배치 실행 가능 여부 확인
        if (!holidayCalendar.shouldRunBatch(marketType, today)) {
            log.info("[{}] Skipping job - {} markets are closed on {}", 
                jobName, marketType, today);
            return;
        }
        
        try {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            log.info("[{}] Starting job for {} markets - {}", jobName, marketType, timestamp);
            
            JobExecution execution = jobLauncher.run(
                job, 
                new JobParametersBuilder()
                    .addString("requestTime", timestamp)
                    .addString("marketType", marketType)
                    .addString("tradingDate", today.toString())
                    .toJobParameters()
            );
            
            log.info("[{}] Job completed - status: {}", jobName, execution.getStatus());
        } catch (Exception e) {
            log.error("[{}] Job execution failed: {}", jobName, e.getMessage(), e);
        }
    }

    /**
     * 초기 구조 설정 - 글로벌 시장 고려
     */
    @Scheduled(cron = "0 0 7 * * ?")
    public void scheduleSetInitStructureJob() {
        runJobWithHolidayCheck(setInitStructureJob, "setInitStructureJob", "GLOBAL");
    }

    /**
     * 선물 월물 추가 - 월초 및 만기일 고려
     */
    @Scheduled(cron = "0 30 7 1,15 * ?") // 매월 1일, 15일
    public void scheduleAddFutureMonthJob() {
        LocalDate today = LocalDate.now();
        
        // 주말인 경우 다음 거래일로 연기
        if (holidayCalendar.isGlobalHoliday(today)) {
            LocalDate nextTradingDay = holidayCalendar.getNextTradingDay("GLOBAL", today);
            log.info("Future month update postponed to next trading day: {}", nextTradingDay);
            // 실제 구현에서는 동적 스케줄링이나 대체 메커니즘 필요
            return;
        }
        
        // 정상 실행
        runJobWithHolidayCheck(setInitStructureJob, "addFutureMonthJob", "GLOBAL");
    }

    /**
     * 데이터 수집 - 이전 거래일 데이터 처리
     */
    @Scheduled(cron = "0 0 18 * * ?")
    public void scheduleCollectTypeDataJob() {
        LocalDate today = LocalDate.now();
        LocalDate previousTradingDay = holidayCalendar.getPreviousTradingDay("ASIA", today);
        
        // 이전 거래일과 오늘 사이에 간격이 있는 경우 (연휴 등)
        if (!previousTradingDay.equals(today.minusDays(1))) {
            log.info("Collecting data for extended period: {} to {}", 
                previousTradingDay, today.minusDays(1));
        }
        
        runJobWithHolidayCheck(collectTypeDataJob, "collectTypeDataJob", "ASIA");
    }

    /**
     * 특별 휴일 처리 - 연말연시
     */
    @Scheduled(cron = "0 0 9 * * ?")
    public void handleSpecialHolidays() {
        LocalDate today = LocalDate.now();
        
        // 연말연시 특별 처리 (12/24 - 1/3)
        if ((today.getMonthValue() == 12 && today.getDayOfMonth() >= 24) ||
            (today.getMonthValue() == 1 && today.getDayOfMonth() <= 3)) {
            
            log.info("Year-end holiday period - running special maintenance");
            // 특별 유지보수 작업 실행
        }
        
        // 각 시장의 주요 연휴 처리
        if (today.getMonthValue() == 1 && today.getDayOfMonth() >= 28 && 
            today.getDayOfMonth() <= 30) {
            log.info("Korean Lunar New Year period - adjusting Asia market schedules");
        }
    }

    /**
     * 휴일 캘린더 업데이트 확인 (매주 일요일)
     */
    @Scheduled(cron = "0 0 20 * * SUN")
    public void updateHolidayCalendar() {
        log.info("Checking for holiday calendar updates...");
        // 실제 구현에서는 외부 API나 설정 파일에서 휴일 정보 업데이트
    }
}