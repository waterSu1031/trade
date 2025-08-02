package com.trade.batch.service;

import com.ib.client.Contract;
import com.ib.client.ContractDetails;
import com.trade.batch.ibkr.ClientIBKR;
import com.trade.batch.repository.TradingHourRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.sql.Timestamp;

@Service
@Slf4j
public class TradingHourService {
    
    @Autowired
    private TradingHourRepository repository;
    
    @Autowired
    private ClientIBKR clientIBKR;
    
    // 거래소별 대표 종목 (IBKR 거래시간 조회용)
    public static final Map<String, String> EXCHANGE_SYMBOLS = new HashMap<>();
    static {
        EXCHANGE_SYMBOLS.put("CME", "ES");      // E-mini S&P 500
        EXCHANGE_SYMBOLS.put("EUREX", "FDAX");  // DAX Future
        EXCHANGE_SYMBOLS.put("KSE", "101S6");   // KOSPI200
        EXCHANGE_SYMBOLS.put("HKFE", "HSI");    // Hang Seng
        EXCHANGE_SYMBOLS.put("SGX", "NK225M");  // Nikkei 225 Mini
        EXCHANGE_SYMBOLS.put("JPX", "NK225");   // Nikkei 225
        EXCHANGE_SYMBOLS.put("CBOT", "ZC");     // Corn
        EXCHANGE_SYMBOLS.put("NYMEX", "CL");    // Crude Oil
        EXCHANGE_SYMBOLS.put("COMEX", "GC");    // Gold
        EXCHANGE_SYMBOLS.put("ICEEU", "BRN");   // Brent Oil
        EXCHANGE_SYMBOLS.put("NSE", "NIFTY50"); // Nifty 50
        EXCHANGE_SYMBOLS.put("OSE", "NK225");   // Osaka Nikkei 225
    }
    
    // 거래소별 시간대
    public static final Map<String, String> EXCHANGE_TIMEZONES = new HashMap<>();
    static {
        EXCHANGE_TIMEZONES.put("CME", "America/Chicago");
        EXCHANGE_TIMEZONES.put("CBOT", "America/Chicago");
        EXCHANGE_TIMEZONES.put("NYMEX", "America/New_York");
        EXCHANGE_TIMEZONES.put("COMEX", "America/New_York");
        EXCHANGE_TIMEZONES.put("EUREX", "Europe/Berlin");
        EXCHANGE_TIMEZONES.put("ICEEU", "Europe/London");
        EXCHANGE_TIMEZONES.put("KSE", "Asia/Seoul");
        EXCHANGE_TIMEZONES.put("JPX", "Asia/Tokyo");
        EXCHANGE_TIMEZONES.put("OSE", "Asia/Tokyo");
        EXCHANGE_TIMEZONES.put("SGX", "Asia/Singapore");
        EXCHANGE_TIMEZONES.put("HKFE", "Asia/Hong_Kong");
        EXCHANGE_TIMEZONES.put("NSE", "Asia/Kolkata");
    }
    
    /**
     * 주간 거래시간 업데이트 (일주일치)
     */
    public void updateWeeklyTradingHours() {
        LocalDate today = LocalDate.now();
        LocalDate endDate = today.plusDays(7);
        
        for (Map.Entry<String, String> entry : EXCHANGE_SYMBOLS.entrySet()) {
            String exchange = entry.getKey();
            String symbol = entry.getValue();
            
            try {
                log.info("Updating trading hours for {} ({})", exchange, symbol);
                updateTradingHoursForExchange(exchange, symbol, today, endDate);
                Thread.sleep(1000); // IBKR API 요청 제한 고려
            } catch (Exception e) {
                log.error("Failed to update trading hours for {}: {}", exchange, e.getMessage());
            }
        }
    }
    
    /**
     * 특정 거래소의 거래시간 강제 업데이트
     */
    public void forceUpdateTradingHours(String exchange) {
        String symbol = EXCHANGE_SYMBOLS.get(exchange);
        if (symbol == null) {
            log.error("No symbol found for exchange: {}", exchange);
            return;
        }
        
        LocalDate today = LocalDate.now();
        LocalDate endDate = today.plusDays(30); // 30일치 데이터 수집
        
        try {
            log.info("Force updating trading hours for {} ({}) - 30 days", exchange, symbol);
            updateTradingHoursForExchange(exchange, symbol, today, endDate);
        } catch (Exception e) {
            log.error("Failed to force update trading hours for {}: {}", exchange, e.getMessage());
        }
    }
    
    /**
     * 특정 거래소의 거래시간 업데이트
     */
    private void updateTradingHoursForExchange(String exchange, String symbol, 
                                              LocalDate startDate, LocalDate endDate) {
        try {
            // Contract 생성
            Contract contract = new Contract();
            contract.symbol(symbol);
            contract.exchange(exchange);
            contract.secType("FUT");
            
            // ContractDetails 요청 (비동기)
            try {
                int reqId = (int)(Math.random() * 10000);
                CompletableFuture<ContractDetails> future = clientIBKR.requestContractDetailsAsync(reqId, contract);
                ContractDetails details = future.get(30, TimeUnit.SECONDS);
                
                if (details != null) {
                    String tradingHours = details.tradingHours();
                    
                    if (tradingHours != null && !tradingHours.isEmpty()) {
                        parseTradingHours(exchange, symbol, tradingHours);
                    } else {
                        log.warn("No trading hours data received for {}", exchange);
                    }
                } else {
                    log.error("Failed to get contract details for {}", exchange);
                }
            } catch (Exception e) {
                log.error("Error getting contract details: {}", e.getMessage());
            }
            
        } catch (Exception e) {
            log.error("Error updating trading hours for {}: {}", exchange, e.getMessage());
        }
    }
    
    /**
     * IBKR 거래시간 문자열 파싱
     * 형식: "20251103:1700-20251104:1600;20251104:1700-20251105:1600"
     */
    private void parseTradingHours(String exchange, String symbol, String tradingHoursStr) {
        String[] sessions = tradingHoursStr.split(";");
        String timezone = EXCHANGE_TIMEZONES.get(exchange);
        boolean hasLunchBreak = repository.hasLunchBreak(exchange);
        
        for (String sessionData : sessions) {
            try {
                // CLOSED 체크
                if (sessionData.contains("CLOSED")) {
                    String dateStr = sessionData.split(":")[0];
                    LocalDate tradeDate = LocalDate.parse(dateStr, DateTimeFormatter.BASIC_ISO_DATE);
                    String dayOfWeek = tradeDate.getDayOfWeek().toString().substring(0, 3);
                    
                    repository.saveHoliday(exchange, tradeDate, dayOfWeek, timezone, sessionData);
                    continue;
                }
                
                // 시간 파싱
                String[] parts = sessionData.split("-");
                if (parts.length != 2) continue;
                
                String startStr = parts[0]; // 20251103:1700
                String endStr = parts[1];   // 20251104:1600
                
                String[] startParts = startStr.split(":");
                String[] endParts = endStr.split(":");
                
                LocalDate startDate = LocalDate.parse(startParts[0], DateTimeFormatter.BASIC_ISO_DATE);
                LocalTime startTime = LocalTime.parse(startParts[1], DateTimeFormatter.ofPattern("HHmm"));
                
                LocalDate endDate = LocalDate.parse(endParts[0], DateTimeFormatter.BASIC_ISO_DATE);
                LocalTime endTime = LocalTime.parse(endParts[1], DateTimeFormatter.ofPattern("HHmm"));
                
                // 현지 시간
                LocalDateTime startTimeLoc = LocalDateTime.of(startDate, startTime);
                LocalDateTime endTimeLoc = LocalDateTime.of(endDate, endTime);
                
                // UTC 변환
                ZonedDateTime startZoned = startTimeLoc.atZone(ZoneId.of(timezone));
                ZonedDateTime endZoned = endTimeLoc.atZone(ZoneId.of(timezone));
                
                LocalDateTime startTimeUtc = startZoned.withZoneSameInstant(ZoneOffset.UTC).toLocalDateTime();
                LocalDateTime endTimeUtc = endZoned.withZoneSameInstant(ZoneOffset.UTC).toLocalDateTime();
                
                // 요일
                String dayOfWeek = startDate.getDayOfWeek().toString().substring(0, 3);
                
                // 세션 구분
                String session = determineSession(exchange, sessions, sessionData, hasLunchBreak);
                
                // 저장
                repository.saveTradingHours(exchange, "", session, startDate, dayOfWeek,
                        startTimeUtc, endTimeUtc, startTimeLoc, endTimeLoc,
                        timezone, false, sessionData);
                        
            } catch (Exception e) {
                log.error("Error parsing session data '{}' for {}: {}", 
                         sessionData, exchange, e.getMessage());
            }
        }
    }
    
    /**
     * 세션 타입 결정
     */
    private String determineSession(String exchange, String[] allSessions, 
                                   String currentSession, boolean hasLunchBreak) {
        if (!hasLunchBreak || allSessions.length == 1) {
            return "REGULAR";
        }
        
        // 점심시간이 있는 거래소의 경우
        int index = -1;
        for (int i = 0; i < allSessions.length; i++) {
            if (allSessions[i].equals(currentSession)) {
                index = i;
                break;
            }
        }
        
        if (index == 0) return "MORNING";
        if (index == 1) return "AFTERNOON";
        return "REGULAR"; // 기타
    }
    
    /**
     * 거래 가능 여부 확인
     */
    public boolean isTradingDay(String exchange, LocalDate date) {
        return repository.isTradingDay(exchange, date);
    }
    
    /**
     * FIX 거래시간 초기화 (테스트용)
     */
    public void initializeFixTradingHours() {
        log.info("Initializing FIX trading hours...");
        
        // CME: 연속 거래 (일요일 17:00 ~ 금요일 16:00)
        repository.saveFixTradingHours("CME", "REGULAR", "SUN",
            LocalDateTime.of(2025, 1, 5, 17, 0),  // 일요일
            LocalDateTime.of(2025, 1, 6, 16, 0),  // 월요일
            "America/Chicago");
        repository.saveFixTradingHours("CME", "REGULAR", "MON",
            LocalDateTime.of(2025, 1, 6, 17, 0),
            LocalDateTime.of(2025, 1, 7, 16, 0),
            "America/Chicago");
        // ... 각 요일별로 계속
        
        // HKFE: 오전/오후 세션
        repository.saveFixTradingHours("HKFE", "MORNING", "MON",
            LocalDateTime.of(2025, 1, 6, 9, 15),
            LocalDateTime.of(2025, 1, 6, 12, 0),
            "Asia/Hong_Kong");
        repository.saveFixTradingHours("HKFE", "AFTERNOON", "MON",
            LocalDateTime.of(2025, 1, 6, 13, 0),
            LocalDateTime.of(2025, 1, 6, 16, 0),
            "Asia/Hong_Kong");
        // ... 다른 거래소들도 추가
        
        log.info("FIX trading hours initialization completed");
    }
    
    /**
     * 오래된 캐시 정리
     */
    public void cleanupOldCache() {
        LocalDate cutoffDate = LocalDate.now().minusMonths(3);
        int deleted = repository.cleanupOldData(cutoffDate);
        log.info("Deleted {} old trading hour records", deleted);
    }
    
    /**
     * 현재 거래 가능 여부 확인
     */
    public boolean isMarketOpen(String exchange, LocalDateTime now) {
        LocalDate today = now.toLocalDate();
        String dayOfWeek = now.getDayOfWeek().toString().substring(0, 3);
        String timezone = EXCHANGE_TIMEZONES.get(exchange);
        
        // 1. 먼저 오늘 날짜의 DAILY 데이터 확인 (우선순위 높음)
        List<Map<String, Object>> dailySessions = repository.getTradingHours(exchange, today);
        if (!dailySessions.isEmpty()) {
            return checkSessionsOpen(dailySessions, now, timezone);
        }
        
        // 2. DAILY 데이터가 없으면 FIX 데이터 사용
        List<Map<String, Object>> fixSessions = repository.getFixTradingHours(exchange, dayOfWeek);
        if (!fixSessions.isEmpty()) {
            return checkFixSessionsOpen(fixSessions, now, timezone);
        }
        
        return false;
    }
    
    /**
     * DAILY 세션 거래 가능 여부 확인
     */
    private boolean checkSessionsOpen(List<Map<String, Object>> sessions, LocalDateTime now, String timezone) {
        ZoneId zoneId = ZoneId.of(timezone);
        LocalDateTime nowLocal = now.atZone(ZoneOffset.UTC).withZoneSameInstant(zoneId).toLocalDateTime();
        
        for (Map<String, Object> session : sessions) {
            if (Boolean.TRUE.equals(session.get("is_holiday"))) {
                return false;
            }
            
            Timestamp startTs = (Timestamp) session.get("start_time_loc");
            Timestamp endTs = (Timestamp) session.get("end_time_loc");
            
            if (startTs == null || endTs == null) continue;
            
            LocalDateTime startTime = startTs.toLocalDateTime();
            LocalDateTime endTime = endTs.toLocalDateTime();
            
            if (nowLocal.isAfter(startTime) && nowLocal.isBefore(endTime)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * FIX 세션 거래 가능 여부 확인
     */
    private boolean checkFixSessionsOpen(List<Map<String, Object>> sessions, LocalDateTime now, String timezone) {
        ZoneId zoneId = ZoneId.of(timezone);
        LocalDateTime nowLocal = now.atZone(ZoneOffset.UTC).withZoneSameInstant(zoneId).toLocalDateTime();
        LocalTime nowTime = nowLocal.toLocalTime();
        
        for (Map<String, Object> session : sessions) {
            // FIX 데이터의 시간만 추출
            Timestamp startTs = (Timestamp) session.get("start_time_loc");
            Timestamp endTs = (Timestamp) session.get("end_time_loc");
            
            if (startTs == null || endTs == null) continue;
            
            LocalTime startTime = startTs.toLocalDateTime().toLocalTime();
            LocalTime endTime = endTs.toLocalDateTime().toLocalTime();
            
            // 날짜를 넘어가는 세션 처리 (예: 17:00 ~ 다음날 16:00)
            if (endTime.isBefore(startTime)) {
                // 현재 시간이 시작 시간 이후거나, 종료 시간 이전인 경우
                if (nowTime.isAfter(startTime) || nowTime.isBefore(endTime)) {
                    return true;
                }
            } else {
                // 같은 날 내에서 끝나는 세션
                if (nowTime.isAfter(startTime) && nowTime.isBefore(endTime)) {
                    return true;
                }
            }
        }
        
        return false;
    }
}