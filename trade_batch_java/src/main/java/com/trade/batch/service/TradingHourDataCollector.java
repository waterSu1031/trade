package com.trade.batch.service;

import com.ib.client.Contract;
import com.ib.client.ContractDetails;
import com.trade.batch.ibkr.ClientIBKR;
import com.trade.batch.repository.TradingHourRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

@Service
@Slf4j
@RequiredArgsConstructor
public class TradingHourDataCollector {
    
    private final TradingHourRepository repository;
    private final ClientIBKR clientIBKR;
    
    // 거래소별 대표 상품 정보
    private static final Map<String, ContractInfo> EXCHANGE_CONTRACTS = new HashMap<>();
    static {
        // 주요 선물 거래소
        EXCHANGE_CONTRACTS.put("CME", new ContractInfo("ES", "FUT", "USD", "202503"));      // E-mini S&P 500
        EXCHANGE_CONTRACTS.put("EUREX", new ContractInfo("FDAX", "FUT", "EUR", "202503"));  // DAX Future
        EXCHANGE_CONTRACTS.put("HKFE", new ContractInfo("HSI", "FUT", "HKD", "202501"));    // Hang Seng
        EXCHANGE_CONTRACTS.put("KSE", new ContractInfo("101S6", "FUT", "KRW", "202503"));   // KOSPI200
        EXCHANGE_CONTRACTS.put("JPX", new ContractInfo("NK225M", "FUT", "JPY", "202503"));  // Nikkei 225 Mini
        EXCHANGE_CONTRACTS.put("SGX", new ContractInfo("NK225M", "FUT", "JPY", "202503"));  // SGX Nikkei
        EXCHANGE_CONTRACTS.put("CBOT", new ContractInfo("ZC", "FUT", "USD", "202503"));     // Corn
        EXCHANGE_CONTRACTS.put("NYMEX", new ContractInfo("CL", "FUT", "USD", "202502"));    // Crude Oil
        EXCHANGE_CONTRACTS.put("COMEX", new ContractInfo("GC", "FUT", "USD", "202502"));    // Gold
        EXCHANGE_CONTRACTS.put("ICEEU", new ContractInfo("BRN", "FUT", "USD", "202502"));   // Brent Oil
        EXCHANGE_CONTRACTS.put("NSE", new ContractInfo("NIFTY50", "IND", "INR", ""));      // Nifty 50 Index
        EXCHANGE_CONTRACTS.put("OSE", new ContractInfo("NK225", "FUT", "JPY", "202503"));   // Osaka Nikkei
    }
    
    // 거래소별 시간대
    private static final Map<String, String> EXCHANGE_TIMEZONES = Map.ofEntries(
        Map.entry("CME", "America/Chicago"),
        Map.entry("CBOT", "America/Chicago"),
        Map.entry("NYMEX", "America/New_York"),
        Map.entry("COMEX", "America/New_York"),
        Map.entry("EUREX", "Europe/Berlin"),
        Map.entry("ICEEU", "Europe/London"),
        Map.entry("HKFE", "Asia/Hong_Kong"),
        Map.entry("KSE", "Asia/Seoul"),
        Map.entry("JPX", "Asia/Tokyo"),
        Map.entry("OSE", "Asia/Tokyo"),
        Map.entry("SGX", "Asia/Singapore"),
        Map.entry("NSE", "Asia/Kolkata")
    );
    
    /**
     * 모든 거래소의 거래시간 수집
     */
    public void collectAllExchangeTradingHours() {
        log.info("=== Starting Trading Hours Collection for All Exchanges ===");
        
        for (Map.Entry<String, ContractInfo> entry : EXCHANGE_CONTRACTS.entrySet()) {
            String exchange = entry.getKey();
            ContractInfo info = entry.getValue();
            
            try {
                log.info("Collecting trading hours for {} exchange...", exchange);
                collectExchangeTradingHours(exchange, info);
                
                // API 요청 제한을 위한 대기
                Thread.sleep(2000);
            } catch (Exception e) {
                log.error("Failed to collect trading hours for {}: {}", exchange, e.getMessage());
            }
        }
        
        log.info("=== Trading Hours Collection Completed ===");
    }
    
    /**
     * 특정 거래소의 거래시간 수집
     */
    public void collectExchangeTradingHours(String exchange, ContractInfo contractInfo) {
        try {
            Contract contract = new Contract();
            contract.symbol(contractInfo.symbol);
            contract.secType(contractInfo.secType);
            contract.exchange(exchange);
            contract.currency(contractInfo.currency);
            
            if (contractInfo.secType.equals("FUT") && !contractInfo.lastTradeDateOrContractMonth.isEmpty()) {
                contract.lastTradeDateOrContractMonth(contractInfo.lastTradeDateOrContractMonth);
            }
            
            // ContractDetails 요청
            int reqId = (int)(Math.random() * 10000);
            CompletableFuture<ContractDetails> future = clientIBKR.requestContractDetailsAsync(reqId, contract);
            ContractDetails details = future.get(30, TimeUnit.SECONDS);
            
            if (details != null) {
                // 거래시간 정보 파싱
                String tradingHours = details.tradingHours();
                String liquidHours = details.liquidHours();
                
                log.info("{} Trading Hours: {}", exchange, tradingHours);
                log.info("{} Liquid Hours: {}", exchange, liquidHours);
                
                // 거래시간 파싱 및 저장
                parseTradingHours(exchange, tradingHours, false);
                
                // 표준 거래시간 생성 및 저장
                generateFixTradingHours(exchange, tradingHours);
            }
        } catch (Exception e) {
            log.error("Error collecting trading hours for {}: {}", exchange, e.getMessage());
        }
    }
    
    /**
     * IBKR 거래시간 문자열 파싱
     */
    private void parseTradingHours(String exchange, String tradingHoursStr, boolean isLiquid) {
        if (tradingHoursStr == null || tradingHoursStr.isEmpty()) {
            return;
        }
        
        String timezone = EXCHANGE_TIMEZONES.get(exchange);
        String[] sessions = tradingHoursStr.split(";");
        
        for (String session : sessions) {
            try {
                if (session.contains("CLOSED")) {
                    // 휴일 처리
                    String dateStr = session.split(":")[0];
                    LocalDate date = LocalDate.parse(dateStr, DateTimeFormatter.BASIC_ISO_DATE);
                    String dayOfWeek = date.getDayOfWeek().toString().substring(0, 3);
                    
                    repository.saveHoliday(exchange, date, dayOfWeek, timezone, session);
                    continue;
                }
                
                // 정규 거래시간 파싱
                parseRegularSession(exchange, session, timezone);
                
            } catch (Exception e) {
                log.error("Error parsing session '{}' for {}: {}", session, exchange, e.getMessage());
            }
        }
    }
    
    /**
     * 정규 세션 파싱
     */
    private void parseRegularSession(String exchange, String sessionData, String timezone) {
        String[] parts = sessionData.split("-");
        if (parts.length != 2) return;
        
        // 시작 시간 파싱
        String[] startParts = parts[0].split(":");
        LocalDate startDate = LocalDate.parse(startParts[0], DateTimeFormatter.BASIC_ISO_DATE);
        LocalTime startTime = LocalTime.parse(startParts[1], DateTimeFormatter.ofPattern("HHmm"));
        
        // 종료 시간 파싱
        String[] endParts = parts[1].split(":");
        LocalDate endDate = LocalDate.parse(endParts[0], DateTimeFormatter.BASIC_ISO_DATE);
        LocalTime endTime = LocalTime.parse(endParts[1], DateTimeFormatter.ofPattern("HHmm"));
        
        // 현지 시간
        LocalDateTime startLoc = LocalDateTime.of(startDate, startTime);
        LocalDateTime endLoc = LocalDateTime.of(endDate, endTime);
        
        // UTC 변환
        ZoneId zoneId = ZoneId.of(timezone);
        LocalDateTime startUtc = startLoc.atZone(zoneId)
            .withZoneSameInstant(ZoneOffset.UTC).toLocalDateTime();
        LocalDateTime endUtc = endLoc.atZone(zoneId)
            .withZoneSameInstant(ZoneOffset.UTC).toLocalDateTime();
        
        // 세션 타입 결정
        String sessionType = determineSessionType(exchange, startTime, endTime);
        String dayOfWeek = startDate.getDayOfWeek().toString().substring(0, 3);
        
        // 저장
        repository.saveTradingHours(exchange, "", sessionType, startDate, dayOfWeek,
                                  startUtc, endUtc, startLoc, endLoc,
                                  timezone, false, sessionData);
    }
    
    /**
     * 세션 타입 결정
     */
    private String determineSessionType(String exchange, LocalTime startTime, LocalTime endTime) {
        // 점심시간이 있는 거래소들
        Set<String> lunchBreakExchanges = Set.of("HKFE", "JPX", "SGX", "OSE");
        
        if (!lunchBreakExchanges.contains(exchange)) {
            return "REGULAR";
        }
        
        // 오전/오후 세션 구분 (대략적인 시간 기준)
        if (startTime.isBefore(LocalTime.of(12, 0))) {
            return "MORNING";
        } else if (startTime.isAfter(LocalTime.of(12, 0))) {
            return "AFTERNOON";
        }
        
        return "REGULAR";
    }
    
    /**
     * FIX 거래시간 생성 (표준 거래시간)
     */
    private void generateFixTradingHours(String exchange, String tradingHoursStr) {
        if (tradingHoursStr == null || tradingHoursStr.isEmpty()) {
            return;
        }
        
        // 요일별 거래시간 패턴 분석
        Map<String, List<SessionInfo>> weeklyPattern = analyzeWeeklyPattern(tradingHoursStr);
        
        String timezone = EXCHANGE_TIMEZONES.get(exchange);
        LocalDate referenceDate = LocalDate.of(2025, 1, 1);
        
        // 각 요일별로 FIX 거래시간 저장
        for (Map.Entry<String, List<SessionInfo>> entry : weeklyPattern.entrySet()) {
            String dayOfWeek = entry.getKey();
            List<SessionInfo> sessions = entry.getValue();
            
            for (SessionInfo session : sessions) {
                // 참조 날짜 계산
                LocalDate fixDate = getNextDayOfWeek(referenceDate, dayOfWeek);
                
                // 현지 시간
                LocalDateTime startLoc = LocalDateTime.of(fixDate, session.startTime);
                LocalDateTime endLoc = LocalDateTime.of(
                    session.endTime.isBefore(session.startTime) ? fixDate.plusDays(1) : fixDate,
                    session.endTime
                );
                
                repository.saveFixTradingHours(exchange, session.sessionType, dayOfWeek,
                                             startLoc, endLoc, timezone);
            }
        }
    }
    
    /**
     * 주간 거래 패턴 분석
     */
    private Map<String, List<SessionInfo>> analyzeWeeklyPattern(String tradingHoursStr) {
        Map<String, List<SessionInfo>> pattern = new HashMap<>();
        
        String[] sessions = tradingHoursStr.split(";");
        for (String session : sessions) {
            if (session.contains("CLOSED")) continue;
            
            try {
                String[] parts = session.split("-");
                if (parts.length != 2) continue;
                
                // 시작 날짜와 시간
                String[] startParts = parts[0].split(":");
                LocalDate startDate = LocalDate.parse(startParts[0], DateTimeFormatter.BASIC_ISO_DATE);
                LocalTime startTime = LocalTime.parse(startParts[1], DateTimeFormatter.ofPattern("HHmm"));
                
                // 종료 시간
                String[] endParts = parts[1].split(":");
                LocalTime endTime = LocalTime.parse(endParts[1], DateTimeFormatter.ofPattern("HHmm"));
                
                // 요일
                String dayOfWeek = startDate.getDayOfWeek().toString().substring(0, 3);
                
                // 세션 정보 추가
                pattern.computeIfAbsent(dayOfWeek, k -> new ArrayList<>())
                       .add(new SessionInfo(startTime, endTime, "REGULAR"));
                       
            } catch (Exception e) {
                log.debug("Error analyzing session: {}", session);
            }
        }
        
        return pattern;
    }
    
    /**
     * 다음 특정 요일 날짜 계산
     */
    private LocalDate getNextDayOfWeek(LocalDate from, String dayOfWeek) {
        DayOfWeek targetDay = DayOfWeek.valueOf(dayOfWeek + "DAY");
        LocalDate date = from;
        
        while (date.getDayOfWeek() != targetDay) {
            date = date.plusDays(1);
        }
        
        return date;
    }
    
    // 내부 클래스들
    private static class ContractInfo {
        final String symbol;
        final String secType;
        final String currency;
        final String lastTradeDateOrContractMonth;
        
        ContractInfo(String symbol, String secType, String currency, String lastTradeDate) {
            this.symbol = symbol;
            this.secType = secType;
            this.currency = currency;
            this.lastTradeDateOrContractMonth = lastTradeDate;
        }
    }
    
    private static class SessionInfo {
        final LocalTime startTime;
        final LocalTime endTime;
        final String sessionType;
        
        SessionInfo(LocalTime startTime, LocalTime endTime, String sessionType) {
            this.startTime = startTime;
            this.endTime = endTime;
            this.sessionType = sessionType;
        }
    }
    
    /**
     * 수동으로 거래시간 입력 (백업용)
     */
    public void insertManualTradingHours() {
        log.info("Inserting manual trading hours...");
        
        String timezone;
        LocalDate refDate = LocalDate.of(2025, 1, 1);
        
        // CME - 일요일 저녁 ~ 금요일 오후
        timezone = "America/Chicago";
        repository.saveFixTradingHours("CME", "REGULAR", "SUN",
            LocalDateTime.of(refDate.with(DayOfWeek.SUNDAY), LocalTime.of(17, 0)),
            LocalDateTime.of(refDate.with(DayOfWeek.MONDAY), LocalTime.of(16, 0)),
            timezone);
        
        // HKFE - 오전/오후 세션
        timezone = "Asia/Hong_Kong";
        for (DayOfWeek day : List.of(DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, 
                                     DayOfWeek.THURSDAY, DayOfWeek.FRIDAY)) {
            LocalDate date = refDate.with(day);
            repository.saveFixTradingHours("HKFE", "MORNING", day.toString().substring(0, 3),
                LocalDateTime.of(date, LocalTime.of(9, 15)),
                LocalDateTime.of(date, LocalTime.of(12, 0)),
                timezone);
            repository.saveFixTradingHours("HKFE", "AFTERNOON", day.toString().substring(0, 3),
                LocalDateTime.of(date, LocalTime.of(13, 0)),
                LocalDateTime.of(date, LocalTime.of(16, 0)),
                timezone);
        }
        
        // 다른 거래소들도 추가...
        
        log.info("Manual trading hours insertion completed");
    }
}