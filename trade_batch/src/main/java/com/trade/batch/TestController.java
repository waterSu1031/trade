package com.trade.batch;

import com.ib.client.Contract;
import com.ib.client.ContractDetails;
import com.trade.batch.ibkr.ClientIBKR;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

// Test comment for monorepo structure verification - batch project
@Slf4j
@RestController
public class TestController {

    @Autowired
    private ClientIBKR clientIBKR;

    @GetMapping("/test/ibkr-connection")
    public Map<String, Object> testIbkrConnection() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            // IB Gateway 연결 테스트
            clientIBKR.connect();
            Thread.sleep(3000); // 연결 대기
            
            boolean connected = clientIBKR.isConnected();
            result.put("connected", connected);
            result.put("message", connected ? "IBKR connection successful" : "IBKR connection failed");
            
            if (connected) {
                // 간단한 contract details 요청 테스트
                Contract contract = new Contract();
                contract.symbol("AAPL");
                contract.secType("STK");
                contract.exchange("SMART");
                contract.currency("USD");
                
                try {
                    CompletableFuture<ContractDetails> future = clientIBKR.requestContractDetailsAsync(1001, contract);
                    ContractDetails details = future.get(10, TimeUnit.SECONDS);
                    
                    result.put("test_contract", "AAPL");
                    result.put("contract_id", details.contract().conid());
                    result.put("long_name", details.longName());
                    result.put("min_tick", details.minTick());
                    result.put("api_test", "SUCCESS");
                    
                } catch (Exception e) {
                    result.put("api_test", "FAILED: " + e.getMessage());
                    log.error("Contract details request failed", e);
                }
            }
            
        } catch (Exception e) {
            result.put("connected", false);
            result.put("message", "Connection error: " + e.getMessage());
            log.error("IBKR connection test failed", e);
        }
        
        return result;
    }

    @GetMapping("/test/disconnect")
    public Map<String, Object> disconnectIbkr() {
        Map<String, Object> result = new HashMap<>();
        try {
            clientIBKR.disconnect();
            result.put("status", "disconnected");
            result.put("message", "IBKR connection closed");
        } catch (Exception e) {
            result.put("status", "error");
            result.put("message", "Disconnect error: " + e.getMessage());
        }
        return result;
    }
}