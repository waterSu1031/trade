package com.trade.batch.ibkr;

import com.ib.client.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

@Slf4j
@Component
public class ClientIBKR extends ListenIBKR {

    private final EClientSocket client;
    private final EJavaSignal signal;
    private volatile Thread readerThread;
    private final AtomicBoolean connected = new AtomicBoolean(false);
    private final Object connectLock = new Object();

    private final String host;
    private final int port;
    private final int clientId;

    @Autowired
    public ClientIBKR(@Value("${ibkr.api.host}") String host,
                      @Value("${ibkr.api.port}") int port,
                      @Value("${ibkr.api.clientId}") int clientId) {
        this.signal = new EJavaSignal();
        this.client = new EClientSocket(this, signal);
        this.host = host;
        this.port = port;
        this.clientId = clientId;
    }

    public void connect() {
        synchronized (connectLock) {
            if (connected.get()) {
                log.info("이미 연결되어 있습니다.");
                return;
            }
            client.eConnect(host, port, clientId);

            // 콜백(nextValidId)에서 진짜 연결성공 여부를 판정하는 것이 더 안전!
            // 아래는 최소한의 연결성 확인(즉시 false일 수 있음에 유의)
            if (!client.isConnected()) {
                log.warn("eConnect 호출 후 아직 연결이 안 됨 (콜백 대기)");
                // 필요시 대기 로직 구현 가능
            }

            // readerThread 최초 1회만 시작
            if (readerThread == null || !readerThread.isAlive()) {
                EReader reader = new EReader(client, signal);
                reader.start();
                readerThread = new Thread(() -> {
                    while (client.isConnected()) {
                        try {
                            signal.waitForSignal();
                            reader.processMsgs();
                        } catch (Exception e) {
                            log.error("EReader processing error", e);
                        }
                    }
                    log.info("EReader 스레드 종료");
                }, "ibkr-reader");
                readerThread.setDaemon(true);
                readerThread.start();
                log.info("EReader 스레드 시작");
            }
        }
    }

    // 다음과 같이 콜백에서 상태를 판정(예시)
    @Override
    public void nextValidId(int orderId) {
        connected.set(true);
        log.info("IBKR 연결 정상(nextValidId). 주문ID: {}", orderId);
        // 추가 연결후처리 가능
    }
    
    @Override
    public void connectAck() {
        log.info("IBKR connectAck 받음 - 연결 확인");
    }

    public void disconnect() {
        synchronized (connectLock) {
            if (client.isConnected()) {
                client.eDisconnect();
                log.info("IBKR 연결 해제 시도");
            }
            connected.set(false);

            // readerThread 안전 종료
            if (readerThread != null && readerThread.isAlive()) {
                try {
                    readerThread.interrupt();
                    readerThread.join(2000); // 최대 2초 대기
                } catch (InterruptedException e) {
                    log.warn("EReader 스레드 종료 대기 중 인터럽트");
                }
                readerThread = null;
            }
            log.info("리더 스레드 종료 및 연결상태 플래그 초기화");
        }
    }

    @Override
    public void connectionClosed() {
        log.warn("IBKR 서버 연결이 종료되었습니다.");
        connected.set(false);

        // readerThread 강제 종료(이미 종료되어 있을 수 있으나 안전하게)
        if (readerThread != null && readerThread.isAlive()) {
            readerThread.interrupt();
            try {
                readerThread.join(1000); // 최대 1초 대기
            } catch (InterruptedException e) {
                log.warn("connectionClosed 중 스레드 종료 대기 인터럽트");
            }
            readerThread = null;
        }
        // 필요시 자동 재연결/알림 등 추가 가능
        log.info("연결 종료 후 정리 완료");
    }

    // ----------------------------------------------------------------------------------------

    private final Map<Integer, CompletableFuture<ContractDetails>> contractFutureMap = new ConcurrentHashMap<>();

    public CompletableFuture<ContractDetails> requestContractDetailsAsync(int reqId, Contract contract) {
        CompletableFuture<ContractDetails> future = new CompletableFuture<>();
        contractFutureMap.put(reqId, future);
        client.reqContractDetails(reqId, contract);
        return future;
    }
    @Override
    public void contractDetails(int reqId, ContractDetails details) {
        CompletableFuture<ContractDetails> future = contractFutureMap.get(reqId);
        if (future != null && !future.isDone()) {
            future.complete(details);
            contractFutureMap.remove(reqId); // 바로 제거해도 됨 (원하는 정책에 따라)
        }
    }
    @Override
    public void contractDetailsEnd(int reqId) {
        contractFutureMap.remove(reqId);
    }

    private final Map<Integer, CompletableFuture<List<Bar>>> histFutureMap = new ConcurrentHashMap<>();
    private final Map<Integer, List<Bar>> historicalDataMap = new ConcurrentHashMap<>();

    public CompletableFuture<List<Bar>> requestHistoricalDataAsync(int reqId, Contract contract, String endDateTime) {
        CompletableFuture<List<Bar>> future = new CompletableFuture<>();
        histFutureMap.put(reqId, future);
        historicalDataMap.put(reqId, new ArrayList<>());
        client.reqHistoricalData(reqId, contract, endDateTime, "1 D", "1 min", "TRADES", 0, 1, false, null);
        return future;
    }
    @Override
    public void historicalData(int reqId, Bar bar) {
//        historicalDataMap.computeIfAbsent(reqId, k -> new ArrayList<>()).add(bar);
        List<Bar> list = historicalDataMap.get(reqId);
        if (list == null) {
            list = new ArrayList<>();
            historicalDataMap.put(reqId, list);
        }
        list.add(bar);
    }
    @Override
    public void historicalDataEnd(int reqId, String startDateStr, String endDateStr) {
        List<Bar> bars = historicalDataMap.remove(reqId);
        CompletableFuture<List<Bar>> future = histFutureMap.remove(reqId);
        if (future != null) {
            future.complete(bars != null ? bars : Collections.emptyList());
        }
    }
    
    // Connection status check
    public boolean isConnected() {
        return connected.get() && client.isConnected();
    }
    
    // Getter for clientId
    public int getClientId() {
        return clientId;
    }

}
