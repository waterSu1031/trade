package com.trade.batch.service;

import com.trade.batch.ibkr.ClientIBKR;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;

/**
 * 시장 시간대를 고려한 IBKR 연결 모니터링
 * 주요 시장 개장 시간대에는 더 자주 체크합니다.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MarketAwareConnectionMonitor {

    private final ClientIBKR clientIBKR;
    private final IBKRConnectionMonitor connectionMonitor;

    /**
     * 시장 개장 30분 전 연결 확인 및 준비
     */
    @Scheduled(cron = "0 30 8 * * ?") // KST 08:30 - 한국/일본 시장 개장 30분 전
    public void checkBeforeAsiaOpen() {
        log.info("Checking IBKR connection before Asia market open...");
        ensureConnection("Asia market opening");
    }

    @Scheduled(cron = "0 30 15 * * ?") // KST 15:30 - 유럽 시장 개장 30분 전
    public void checkBeforeEuropeOpen() {
        log.info("Checking IBKR connection before Europe market open...");
        ensureConnection("Europe market opening");
    }

    @Scheduled(cron = "0 0 22 * * ?") // KST 22:00 - 미국 시장 개장 30분 전
    public void checkBeforeUSOpen() {
        log.info("Checking IBKR connection before US market open...");
        ensureConnection("US market opening");
    }

    /**
     * 주요 거래 시간대에는 1분마다 체크
     * - 아시아: 09:00-15:30 KST
     * - 유럽: 16:00-00:30 KST
     * - 미국: 22:30-05:00 KST
     */
    @Scheduled(fixedDelay = 60000)
    public void intensiveMonitoring() {
        if (isActiveTrading()) {
            log.debug("Active trading hours - checking connection...");
            connectionMonitor.checkConnection();
        }
    }

    /**
     * 비활성 시간대에는 5분마다 체크
     */
    @Scheduled(cron = "0 */5 * * * ?")
    public void regularMonitoring() {
        if (!isActiveTrading()) {
            log.debug("Off-peak hours - regular connection check...");
            connectionMonitor.checkConnection();
        }
    }

    /**
     * 현재 시간이 주요 거래 시간대인지 확인
     */
    private boolean isActiveTrading() {
        ZonedDateTime now = ZonedDateTime.now(ZoneId.of("Asia/Seoul"));
        LocalTime currentTime = now.toLocalTime();
        
        // 아시아 시장 (09:00-15:30)
        if (currentTime.isAfter(LocalTime.of(9, 0)) && 
            currentTime.isBefore(LocalTime.of(15, 30))) {
            return true;
        }
        
        // 유럽 시장 (16:00-00:30)
        if (currentTime.isAfter(LocalTime.of(16, 0)) || 
            currentTime.isBefore(LocalTime.of(0, 30))) {
            return true;
        }
        
        // 미국 시장 (22:30-05:00)
        if (currentTime.isAfter(LocalTime.of(22, 30)) || 
            currentTime.isBefore(LocalTime.of(5, 0))) {
            return true;
        }
        
        return false;
    }

    /**
     * 연결 상태 확인 및 필요시 재연결
     */
    private void ensureConnection(String reason) {
        IBKRConnectionMonitor.ConnectionStatus status = connectionMonitor.getConnectionStatus();
        
        if (!status.isConnected()) {
            log.warn("IBKR not connected for {}. Attempting connection...", reason);
            connectionMonitor.checkConnection();
        } else {
            log.info("IBKR connection ready for {}. Client ID: {}", reason, status.getClientId());
        }
    }

    /**
     * 시장 전환 시간대 추가 체크
     */
    @Scheduled(cron = "0 0 9 * * ?") // KST 09:00 - 아시아 개장
    public void asiaMarketTransition() {
        log.info("Asia market transition - verifying connection stability...");
        verifyConnectionStability();
    }

    @Scheduled(cron = "0 0 16 * * ?") // KST 16:00 - 유럽 개장
    public void europeMarketTransition() {
        log.info("Europe market transition - verifying connection stability...");
        verifyConnectionStability();
    }

    @Scheduled(cron = "0 30 22 * * ?") // KST 22:30 - 미국 개장
    public void usMarketTransition() {
        log.info("US market transition - verifying connection stability...");
        verifyConnectionStability();
    }

    private void verifyConnectionStability() {
        try {
            // 연결 상태 체크
            if (!clientIBKR.isConnected()) {
                log.error("Connection lost during market transition!");
                connectionMonitor.checkConnection();
                return;
            }

            // 간단한 요청으로 연결 상태 검증
            log.info("Connection verified during market transition");
            
        } catch (Exception e) {
            log.error("Connection verification failed during market transition", e);
            connectionMonitor.checkConnection();
        }
    }
}