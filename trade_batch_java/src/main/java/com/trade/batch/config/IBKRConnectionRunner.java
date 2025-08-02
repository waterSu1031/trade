package com.trade.batch.config;

import com.trade.batch.ibkr.ClientIBKR;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@Order(1)
@RequiredArgsConstructor
public class IBKRConnectionRunner implements ApplicationRunner {

    private final ClientIBKR clientIBKR;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        log.info("========================================");
        log.info("Starting IB Gateway Connection...");
        log.info("========================================");
        
        try {
            // IB Gateway 연결 시작
            clientIBKR.connect();
            
            // 연결 대기 (최대 10초)
            int waitCount = 0;
            while (!clientIBKR.isConnected() && waitCount < 100) {
                Thread.sleep(100);
                waitCount++;
            }
            
            if (clientIBKR.isConnected()) {
                log.info("✅ IB Gateway Connection SUCCESS");
                log.info("Client ID: 30 (trade_batch)");
                log.info("========================================");
            } else {
                log.error("❌ IB Gateway Connection FAILED");
                log.error("Please check IB Gateway is running and API settings are correct");
                log.error("========================================");
                // 연결 실패 시에도 애플리케이션은 계속 실행되도록 함
                // 필요시 System.exit(1) 호출하여 종료 가능
            }
            
        } catch (Exception e) {
            log.error("Error during IB Gateway connection", e);
            log.error("========================================");
            // 예외 발생 시에도 애플리케이션은 계속 실행
        }
    }
}