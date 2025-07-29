package com.trade.batch.health;

import com.trade.batch.ibkr.ClientIBKR;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component("ibkr")
@RequiredArgsConstructor
public class IBKRHealthIndicator implements HealthIndicator {

    private final ClientIBKR clientIBKR;

    @Override
    public Health health() {
        try {
            boolean isConnected = clientIBKR.isConnected();
            
            if (isConnected) {
                return Health.up()
                    .withDetail("status", "Connected")
                    .withDetail("clientId", 30)
                    .withDetail("service", "trade_batch")
                    .build();
            } else {
                return Health.down()
                    .withDetail("status", "Disconnected")
                    .withDetail("clientId", 30)
                    .withDetail("service", "trade_batch")
                    .withDetail("message", "IB Gateway connection is not active")
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("status", "Error")
                .withDetail("clientId", 30)
                .withDetail("service", "trade_batch")
                .withException(e)
                .build();
        }
    }
}