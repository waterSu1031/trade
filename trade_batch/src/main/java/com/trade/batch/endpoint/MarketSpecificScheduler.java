package com.trade.batch.endpoint;

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

/**
 * 시장별 데이터 수집 스케줄러
 * 각 주요 시장의 마감 시간에 맞춰 데이터를 수집합니다.
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class MarketSpecificScheduler {

    private final JobLauncher jobLauncher;
    private final Job collectTypeDataJob;

    private void runMarketDataCollection(String market) {
        try {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            log.info("[{}] 시장 데이터 수집 시작 - {}", market, timestamp);

            JobExecution execution = jobLauncher.run(
                    collectTypeDataJob, 
                    new JobParametersBuilder()
                            .addString("requestTime", timestamp)
                            .addString("market", market)
                            .toJobParameters()
            );

            log.info("[{}] 시장 데이터 수집 종료 - status: {}", market, execution.getStatus());
        } catch (Exception e) {
            log.error("[{}] 시장 데이터 수집 중 오류 발생: {}", market, e.getMessage(), e);
        }
    }

    /**
     * 아시아 시장 데이터 수집 (KST 16:00)
     * - KRX, JPX, SGX, HKEX 마감 후
     */
    @Scheduled(cron = "0 0 16 * * ?") 
    public void collectAsiaMarketData() {
        runMarketDataCollection("ASIA");
    }

    /**
     * 유럽 시장 데이터 수집 (KST 01:00)
     * - Eurex, LSE, Euronext 마감 후
     */
    @Scheduled(cron = "0 0 1 * * ?")
    public void collectEuropeMarketData() {
        runMarketDataCollection("EUROPE");
    }

    /**
     * 미국 시장 데이터 수집 (KST 06:00)
     * - CME, ICE, CBOE 마감 후
     */
    @Scheduled(cron = "0 0 6 * * ?")
    public void collectUSMarketData() {
        runMarketDataCollection("US");
    }

    /**
     * 글로벌 암호화폐 시장 데이터 수집 (KST 09:00)
     * - 24시간 거래되는 암호화폐 일일 정산
     */
    @Scheduled(cron = "0 0 9 * * ?")
    public void collectCryptoMarketData() {
        runMarketDataCollection("CRYPTO");
    }
}