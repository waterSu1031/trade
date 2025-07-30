package com.trade.batch.service;

import com.trade.batch.ibkr.ClientIBKR;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import javax.annotation.PreDestroy;
import java.util.concurrent.atomic.AtomicInteger;

@Slf4j
@Service
@RequiredArgsConstructor
public class IBKRConnectionMonitor {

    private final ClientIBKR clientIBKR;
    private final AtomicInteger reconnectAttempts = new AtomicInteger(0);
    private static final int MAX_RECONNECT_ATTEMPTS = 3;
    private static final long RECONNECT_DELAY = 30000; // 30초

    /**
     * 1분마다 연결 상태를 확인하고 필요시 재연결 시도
     */
    @Scheduled(fixedDelay = 60000, initialDelay = 60000)
    public void checkConnection() {
        try {
            boolean isConnected = clientIBKR.isConnected();
            
            if (!isConnected) {
                log.warn("IB Gateway connection lost. Attempting to reconnect...");
                attemptReconnection();
            } else {
                // 연결이 정상이면 재연결 시도 횟수 초기화
                if (reconnectAttempts.get() > 0) {
                    log.info("IB Gateway connection restored.");
                    reconnectAttempts.set(0);
                }
            }
        } catch (Exception e) {
            log.error("Error during connection check", e);
        }
    }

    /**
     * 재연결 시도
     */
    private void attemptReconnection() {
        int attempts = reconnectAttempts.incrementAndGet();
        
        if (attempts > MAX_RECONNECT_ATTEMPTS) {
            log.error("Maximum reconnection attempts ({}) reached. Manual intervention required.", MAX_RECONNECT_ATTEMPTS);
            // 여기서 알림을 보내거나 다른 조치를 취할 수 있음
            return;
        }
        
        log.info("Reconnection attempt {} of {}", attempts, MAX_RECONNECT_ATTEMPTS);
        
        try {
            // 기존 연결이 있다면 먼저 종료
            if (clientIBKR.isConnected()) {
                clientIBKR.disconnect();
                Thread.sleep(2000); // 2초 대기
            }
            
            // 재연결 시도
            clientIBKR.connect();
            
            // 연결 확인 (최대 10초 대기)
            int waitCount = 0;
            while (!clientIBKR.isConnected() && waitCount < 100) {
                Thread.sleep(100);
                waitCount++;
            }
            
            if (clientIBKR.isConnected()) {
                log.info("✅ Reconnection successful");
                reconnectAttempts.set(0);
            } else {
                log.error("❌ Reconnection failed");
                
                // 다음 재연결 시도까지 대기
                if (attempts < MAX_RECONNECT_ATTEMPTS) {
                    log.info("Next reconnection attempt in {} seconds", RECONNECT_DELAY / 1000);
                }
            }
            
        } catch (Exception e) {
            log.error("Error during reconnection attempt", e);
        }
    }

    /**
     * 애플리케이션 종료 시 연결 해제
     */
    @PreDestroy
    public void cleanup() {
        try {
            if (clientIBKR.isConnected()) {
                log.info("Closing IB Gateway connection...");
                clientIBKR.disconnect();
                log.info("IB Gateway connection closed.");
            }
        } catch (Exception e) {
            log.error("Error during cleanup", e);
        }
    }

    /**
     * 현재 연결 상태 정보 반환
     */
    public ConnectionStatus getConnectionStatus() {
        return ConnectionStatus.builder()
            .connected(clientIBKR.isConnected())
            .reconnectAttempts(reconnectAttempts.get())
            .maxReconnectAttempts(MAX_RECONNECT_ATTEMPTS)
            .clientId(clientIBKR.getClientId())
            .service("trade_batch")
            .build();
    }

    /**
     * 연결 상태 정보 DTO
     */
    @lombok.Data
    @lombok.Builder
    public static class ConnectionStatus {
        private boolean connected;
        private int reconnectAttempts;
        private int maxReconnectAttempts;
        private int clientId;
        private String service;
    }
}