package com.trade.batch.ibkr;

import com.ib.client.*;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class SimpleIBConnectionTest implements EWrapper {
    
    private EClientSocket client;
    private EJavaSignal signal;
    private boolean connected = false;
    private CountDownLatch connectionLatch = new CountDownLatch(1);
    
    public SimpleIBConnectionTest() {
        signal = new EJavaSignal();
        client = new EClientSocket(this, signal);
    }
    
    public void connect() {
        System.out.println("IB Gateway 연결 시도 - Paper Trading (port: 4002, clientId: 30)");
        client.eConnect("localhost", 4002, 30);
        
        // Reader thread 시작
        EReader reader = new EReader(client, signal);
        reader.start();
        
        new Thread(() -> {
            while (client.isConnected()) {
                signal.waitForSignal();
                try {
                    reader.processMsgs();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }).start();
    }
    
    public boolean waitForConnection(int timeoutSeconds) throws InterruptedException {
        return connectionLatch.await(timeoutSeconds, TimeUnit.SECONDS);
    }
    
    public void testContractDetails() {
        if (!connected) {
            System.out.println("연결되지 않았습니다.");
            return;
        }
        
        Contract contract = new Contract();
        contract.symbol("SPY");
        contract.secType("STK");
        contract.currency("USD");
        contract.exchange("SMART");
        
        System.out.println("SPY 계약 정보 요청...");
        client.reqContractDetails(1001, contract);
    }
    
    public void disconnect() {
        if (client.isConnected()) {
            client.eDisconnect();
            System.out.println("연결 해제됨");
        }
    }
    
    // EWrapper 구현
    @Override
    public void nextValidId(int orderId) {
        connected = true;
        connectionLatch.countDown();
        System.out.println("✓ 연결 성공! Next Valid Order ID: " + orderId);
    }
    
    @Override
    public void connectAck() {
        System.out.println("✓ 연결 확인됨 (connectAck)");
    }
    
    @Override
    public void connectionClosed() {
        connected = false;
        System.out.println("연결이 종료되었습니다.");
    }
    
    @Override
    public void error(int id, int errorCode, String errorMsg, String advancedOrderRejectJson) {
        System.err.println("Error - ID: " + id + ", Code: " + errorCode + ", Msg: " + errorMsg);
    }
    
    @Override
    public void contractDetails(int reqId, ContractDetails contractDetails) {
        System.out.println("\n=== 계약 정보 수신 ===");
        System.out.println("Symbol: " + contractDetails.contract().symbol());
        System.out.println("Long Name: " + contractDetails.longName());
        System.out.println("Contract ID: " + contractDetails.contract().conid());
        System.out.println("Exchange: " + contractDetails.contract().exchange());
        System.out.println("Market Name: " + contractDetails.marketName());
    }
    
    @Override
    public void contractDetailsEnd(int reqId) {
        System.out.println("=== 계약 정보 끝 ===\n");
    }
    
    // 나머지 EWrapper 메서드들은 빈 구현
    @Override public void tickPrice(int tickerId, int field, double price, TickAttrib attrib) {}
    @Override public void tickSize(int tickerId, int field, Decimal size) {}
    @Override public void tickOptionComputation(int tickerId, int field, int tickAttrib, double impliedVol, double delta, double optPrice, double pvDividend, double gamma, double vega, double theta, double undPrice) {}
    @Override public void tickGeneric(int tickerId, int tickType, double value) {}
    @Override public void tickString(int tickerId, int tickType, String value) {}
    @Override public void tickEFP(int tickerId, int tickType, double basisPoints, String formattedBasisPoints, double impliedFuture, int holdDays, String futureLastTradeDate, double dividendImpact, double dividendsToLastTradeDate) {}
    @Override public void orderStatus(int orderId, String status, Decimal filled, Decimal remaining, double avgFillPrice, int permId, int parentId, double lastFillPrice, int clientId, String whyHeld, double mktCapPrice) {}
    @Override public void openOrder(int orderId, Contract contract, Order order, OrderState orderState) {}
    @Override public void openOrderEnd() {}
    @Override public void updateAccountValue(String key, String value, String currency, String accountName) {}
    @Override public void updatePortfolio(Contract contract, Decimal position, double marketPrice, double marketValue, double averageCost, double unrealizedPNL, double realizedPNL, String accountName) {}
    @Override public void updateAccountTime(String timeStamp) {}
    @Override public void accountDownloadEnd(String accountName) {}
    @Override public void updateNewsBulletin(int msgId, int msgType, String newsMessage, String originExch) {}
    @Override public void managedAccounts(String accountsList) {}
    @Override public void receiveFA(int faDataType, String xml) {}
    @Override public void historicalData(int reqId, Bar bar) {}
    @Override public void historicalDataEnd(int reqId, String startDateStr, String endDateStr) {}
    @Override public void scannerParameters(String xml) {}
    @Override public void scannerData(int reqId, int rank, ContractDetails contractDetails, String distance, String benchmark, String projection, String legsStr) {}
    @Override public void scannerDataEnd(int reqId) {}
    @Override public void realtimeBar(int reqId, long time, double open, double high, double low, double close, Decimal volume, Decimal wap, int count) {}
    @Override public void currentTime(long time) {}
    @Override public void fundamentalData(int reqId, String data) {}
    @Override public void deltaNeutralValidation(int reqId, DeltaNeutralContract deltaNeutralContract) {}
    @Override public void tickSnapshotEnd(int reqId) {}
    @Override public void marketDataType(int reqId, int marketDataType) {}
    @Override public void commissionReport(CommissionReport commissionReport) {}
    @Override public void position(String account, Contract contract, Decimal pos, double avgCost) {}
    @Override public void positionEnd() {}
    @Override public void accountSummary(int reqId, String account, String tag, String value, String currency) {}
    @Override public void accountSummaryEnd(int reqId) {}
    @Override public void verifyMessageAPI(String apiData) {}
    @Override public void verifyCompleted(boolean isSuccessful, String errorText) {}
    @Override public void verifyAndAuthMessageAPI(String apiData, String xyzChallenge) {}
    @Override public void verifyAndAuthCompleted(boolean isSuccessful, String errorText) {}
    @Override public void displayGroupList(int reqId, String groups) {}
    @Override public void displayGroupUpdated(int reqId, String contractInfo) {}
    @Override public void error(Exception e) { e.printStackTrace(); }
    @Override public void error(String str) { System.err.println("Error: " + str); }
    @Override public void error(int id, int errorCode, String errorMsg) { error(id, errorCode, errorMsg, ""); }
    @Override public void positionMulti(int reqId, String account, String modelCode, Contract contract, Decimal pos, double avgCost) {}
    @Override public void positionMultiEnd(int reqId) {}
    @Override public void accountUpdateMulti(int reqId, String account, String modelCode, String key, String value, String currency) {}
    @Override public void accountUpdateMultiEnd(int reqId) {}
    @Override public void securityDefinitionOptionalParameter(int reqId, String exchange, int underlyingConId, String tradingClass, String multiplier, Set<String> expirations, Set<Double> strikes) {}
    @Override public void securityDefinitionOptionalParameterEnd(int reqId) {}
    @Override public void softDollarTiers(int reqId, SoftDollarTier[] tiers) {}
    @Override public void familyCodes(FamilyCode[] familyCodes) {}
    @Override public void symbolSamples(int reqId, ContractDescription[] contractDescriptions) {}
    @Override public void historicalDataUpdate(int reqId, Bar bar) {}
    @Override public void mktDepthExchanges(DepthMktDataDescription[] depthMktDataDescriptions) {}
    @Override public void tickNews(int tickerId, long timeStamp, String providerCode, String articleId, String headline, String extraData) {}
    @Override public void smartComponents(int reqId, Map<Integer, Map.Entry<String, Character>> theMap) {}
    @Override public void tickReqParams(int tickerId, double minTick, String bboExchange, int snapshotPermissions) {}
    @Override public void newsProviders(NewsProvider[] newsProviders) {}
    @Override public void newsArticle(int requestId, int articleType, String articleText) {}
    @Override public void historicalNews(int requestId, String time, String providerCode, String articleId, String headline) {}
    @Override public void historicalNewsEnd(int requestId, boolean hasMore) {}
    @Override public void headTimestamp(int reqId, String headTimestamp) {}
    @Override public void histogramData(int reqId, List<HistogramEntry> items) {}
    @Override public void historicalDataEnd(int reqId, String startDate, String endDate) {}
    @Override public void rerouteMktDataReq(int reqId, int conId, String exchange) {}
    @Override public void rerouteMktDepthReq(int reqId, int conId, String exchange) {}
    @Override public void marketRule(int marketRuleId, PriceIncrement[] priceIncrements) {}
    @Override public void pnl(int reqId, double dailyPnL, double unrealizedPnL, double realizedPnL) {}
    @Override public void pnlSingle(int reqId, Decimal pos, double dailyPnL, double unrealizedPnL, double realizedPnL, double value) {}
    @Override public void historicalTicks(int reqId, List<HistoricalTick> ticks, boolean done) {}
    @Override public void historicalTicksBidAsk(int reqId, List<HistoricalTickBidAsk> ticks, boolean done) {}
    @Override public void historicalTicksLast(int reqId, List<HistoricalTickLast> ticks, boolean done) {}
    @Override public void tickByTickAllLast(int reqId, int tickType, long time, double price, Decimal size, TickAttribLast tickAttribLast, String exchange, String specialConditions) {}
    @Override public void tickByTickBidAsk(int reqId, long time, double bidPrice, double askPrice, Decimal bidSize, Decimal askSize, TickAttribBidAsk tickAttribBidAsk) {}
    @Override public void tickByTickMidPoint(int reqId, long time, double midPoint) {}
    @Override public void orderBound(long orderId, int apiClientId, int apiOrderId) {}
    @Override public void completedOrder(Contract contract, Order order, OrderState orderState) {}
    @Override public void completedOrdersEnd() {}
    @Override public void replaceFAEnd(int reqId, String text) {}
    @Override public void wshMetaData(int reqId, String dataJson) {}
    @Override public void wshEventData(int reqId, String dataJson) {}
    @Override public void historicalSchedule(int reqId, String startDateTime, String endDateTime, String timeZone, List<HistoricalSession> sessions) {}
    @Override public void userInfo(int reqId, String whiteBrandingId) {}
    
    // 메인 메서드
    public static void main(String[] args) {
        System.out.println("=== IB Gateway 연결 테스트 시작 ===");
        System.out.println("MSA 환경 클라이언트 ID 정보:");
        System.out.println("- trade_batch: 30 (현재 테스트)");
        System.out.println("- trade_engine: 20");
        System.out.println("- trade_dashboard: 10");
        System.out.println();
        
        SimpleIBConnectionTest test = new SimpleIBConnectionTest();
        
        try {
            // 1. 연결
            test.connect();
            
            // 2. 연결 대기 (최대 10초)
            if (test.waitForConnection(10)) {
                System.out.println("\n연결 성공! 테스트 진행...");
                
                // 3. 계약 정보 테스트
                Thread.sleep(1000);
                test.testContractDetails();
                
                // 4. 잠시 대기 후 종료
                Thread.sleep(3000);
            } else {
                System.err.println("연결 실패: 시간 초과");
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            // 5. 연결 해제
            test.disconnect();
        }
        
        System.out.println("\n=== 테스트 완료 ===");
    }
}