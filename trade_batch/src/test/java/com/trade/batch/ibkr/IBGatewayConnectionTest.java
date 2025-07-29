package com.trade.batch.ibkr;

import com.ib.client.Bar;
import com.ib.client.Contract;
import com.ib.client.ContractDetails;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

@Slf4j
@SpringBootTest
@ActiveProfiles("test")
public class IBGatewayConnectionTest {

    @Autowired
    private ClientIBKR clientIBKR;

    @Test
    public void testIBGatewayConnection() throws Exception {
        log.info("IB Gateway 연결 테스트 시작 - Client ID: 30");
        
        // 1. 연결 시도
        clientIBKR.connect();
        
        // 연결 대기 (최대 5초)
        int waitCount = 0;
        while (!clientIBKR.isConnected() && waitCount < 50) {
            Thread.sleep(100);
            waitCount++;
        }
        
        // 연결 상태 확인
        assertTrue(clientIBKR.isConnected(), "IB Gateway 연결 실패");
        log.info("IB Gateway 연결 성공!");
        
        // 2. 간단한 계약 정보 요청 테스트 (SPY ETF)
        Contract contract = new Contract();
        contract.symbol("SPY");
        contract.secType("STK");
        contract.currency("USD");
        contract.exchange("SMART");
        
        try {
            CompletableFuture<ContractDetails> contractFuture = 
                clientIBKR.requestContractDetailsAsync(1001, contract);
            
            ContractDetails details = contractFuture.get(10, TimeUnit.SECONDS);
            assertNotNull(details, "계약 정보를 받지 못했습니다.");
            
            log.info("계약 정보 수신 성공:");
            log.info("- Symbol: {}", contract.symbol());
            log.info("- Long Name: {}", details.longName());
            log.info("- Contract ID: {}", details.contract().conid());
            log.info("- Exchange: {}", details.contract().exchange());
            
        } catch (Exception e) {
            log.error("계약 정보 요청 중 오류: ", e);
        }
        
        // 3. 과거 데이터 요청 테스트
        try {
            CompletableFuture<List<Bar>> histDataFuture = 
                clientIBKR.requestHistoricalDataAsync(2001, contract, "");
            
            List<Bar> bars = histDataFuture.get(10, TimeUnit.SECONDS);
            assertNotNull(bars, "과거 데이터를 받지 못했습니다.");
            assertFalse(bars.isEmpty(), "과거 데이터가 비어있습니다.");
            
            log.info("과거 데이터 수신 성공: {} bars", bars.size());
            if (!bars.isEmpty()) {
                Bar firstBar = bars.get(0);
                log.info("첫 번째 Bar - Time: {}, Open: {}, High: {}, Low: {}, Close: {}", 
                    firstBar.time(), firstBar.open(), firstBar.high(), 
                    firstBar.low(), firstBar.close());
            }
            
        } catch (Exception e) {
            log.error("과거 데이터 요청 중 오류: ", e);
        }
        
        // 4. 연결 해제
        clientIBKR.disconnect();
        Thread.sleep(1000);
        
        assertFalse(clientIBKR.isConnected(), "연결 해제 실패");
        log.info("IB Gateway 연결 해제 완료");
        
        log.info("=== IB Gateway 연결 테스트 완료 ===");
    }
    
    @Test
    public void testMultipleClientConnections() throws Exception {
        log.info("다중 클라이언트 연결 시뮬레이션 테스트");
        
        // trade_batch (clientId: 30) 연결은 이미 autowired로 처리됨
        clientIBKR.connect();
        
        int waitCount = 0;
        while (!clientIBKR.isConnected() && waitCount < 50) {
            Thread.sleep(100);
            waitCount++;
        }
        
        assertTrue(clientIBKR.isConnected(), "trade_batch (clientId: 30) 연결 실패");
        log.info("trade_batch (clientId: 30) 연결 성공");
        
        // 다른 MSA 서비스들의 클라이언트 ID 정보 출력
        log.info("MSA 환경의 다른 서비스 클라이언트 ID:");
        log.info("- trade_batch: 30 (현재 연결됨)");
        log.info("- trade_engine: 20");
        log.info("- trade_dashboard: 10");
        
        clientIBKR.disconnect();
        log.info("테스트 완료");
    }
}