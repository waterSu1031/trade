package com.trade.batch.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.DayOfWeek;
import java.util.*;

/**
 * 글로벌 시장 휴일 관리
 * 각 거래소별 휴일을 관리하고 배치 작업 실행 여부를 결정합니다.
 */
@Slf4j
@Component
public class MarketHolidayCalendar {

    private static final Map<String, Set<LocalDate>> MARKET_HOLIDAYS_2025 = new HashMap<>();
    
    static {
        // 한국 시장 (KRX) 휴일
        Set<LocalDate> krxHolidays = new HashSet<>(Arrays.asList(
            LocalDate.of(2025, 1, 1),   // 신정
            LocalDate.of(2025, 1, 28),  // 설날 연휴
            LocalDate.of(2025, 1, 29),
            LocalDate.of(2025, 1, 30),
            LocalDate.of(2025, 3, 1),   // 삼일절
            LocalDate.of(2025, 5, 5),   // 어린이날
            LocalDate.of(2025, 5, 6),   // 대체휴일
            LocalDate.of(2025, 6, 3),   // 대선
            LocalDate.of(2025, 6, 6),   // 현충일
            LocalDate.of(2025, 8, 15),  // 광복절
            LocalDate.of(2025, 10, 3),  // 개천절
            LocalDate.of(2025, 10, 5),  // 추석 연휴
            LocalDate.of(2025, 10, 6),
            LocalDate.of(2025, 10, 7),
            LocalDate.of(2025, 10, 9),  // 한글날
            LocalDate.of(2025, 12, 25)  // 성탄절
        ));
        MARKET_HOLIDAYS_2025.put("KRX", krxHolidays);
        
        // 일본 시장 (JPX) 휴일
        Set<LocalDate> jpxHolidays = new HashSet<>(Arrays.asList(
            LocalDate.of(2025, 1, 1),   // 신정
            LocalDate.of(2025, 1, 2),
            LocalDate.of(2025, 1, 3),
            LocalDate.of(2025, 1, 13),  // 성인의날
            LocalDate.of(2025, 2, 11),  // 건국기념일
            LocalDate.of(2025, 2, 23),  // 천황탄생일
            LocalDate.of(2025, 2, 24),  // 대체휴일
            LocalDate.of(2025, 3, 20),  // 춘분의날
            LocalDate.of(2025, 4, 29),  // 쇼와의날
            LocalDate.of(2025, 5, 3),   // 헌법기념일
            LocalDate.of(2025, 5, 4),   // 녹의날
            LocalDate.of(2025, 5, 5),   // 어린이날
            LocalDate.of(2025, 5, 6),   // 대체휴일
            LocalDate.of(2025, 9, 15),  // BCP 테스트
            LocalDate.of(2025, 9, 23),  // 추분의날
            LocalDate.of(2025, 11, 3),  // 문화의날
            LocalDate.of(2025, 11, 23), // 근로감사의날
            LocalDate.of(2025, 11, 24)  // 대체휴일
        ));
        MARKET_HOLIDAYS_2025.put("JPX", jpxHolidays);
        
        // 미국 시장 (CME) 휴일
        Set<LocalDate> cmeHolidays = new HashSet<>(Arrays.asList(
            LocalDate.of(2025, 1, 1),   // New Year's Day
            LocalDate.of(2025, 1, 20),  // Martin Luther King Jr. Day
            LocalDate.of(2025, 2, 17),  // Presidents Day
            LocalDate.of(2025, 4, 18),  // Good Friday
            LocalDate.of(2025, 5, 26),  // Memorial Day
            LocalDate.of(2025, 7, 4),   // Independence Day
            LocalDate.of(2025, 9, 1),   // Labor Day
            LocalDate.of(2025, 11, 27), // Thanksgiving
            LocalDate.of(2025, 12, 25)  // Christmas
        ));
        MARKET_HOLIDAYS_2025.put("CME", cmeHolidays);
        MARKET_HOLIDAYS_2025.put("US", cmeHolidays);
        
        // 유럽 시장 (Eurex) 휴일
        Set<LocalDate> eurexHolidays = new HashSet<>(Arrays.asList(
            LocalDate.of(2025, 1, 1),   // New Year's Day
            LocalDate.of(2025, 4, 18),  // Good Friday
            LocalDate.of(2025, 4, 21),  // Easter Monday
            LocalDate.of(2025, 5, 1),   // Labour Day
            LocalDate.of(2025, 12, 24), // Christmas Eve
            LocalDate.of(2025, 12, 25), // Christmas Day
            LocalDate.of(2025, 12, 26), // Boxing Day
            LocalDate.of(2025, 12, 31)  // New Year's Eve
        ));
        MARKET_HOLIDAYS_2025.put("EUREX", eurexHolidays);
        MARKET_HOLIDAYS_2025.put("EUROPE", eurexHolidays);
    }

    /**
     * 특정 시장이 휴일인지 확인
     */
    public boolean isMarketHoliday(String market, LocalDate date) {
        // 주말 확인
        if (date.getDayOfWeek() == DayOfWeek.SATURDAY || 
            date.getDayOfWeek() == DayOfWeek.SUNDAY) {
            return true;
        }
        
        // 시장별 휴일 확인
        Set<LocalDate> holidays = MARKET_HOLIDAYS_2025.get(market.toUpperCase());
        if (holidays != null) {
            return holidays.contains(date);
        }
        
        return false;
    }

    /**
     * 모든 주요 시장이 휴일인지 확인
     */
    public boolean isGlobalHoliday(LocalDate date) {
        return isMarketHoliday("KRX", date) &&
               isMarketHoliday("JPX", date) &&
               isMarketHoliday("CME", date) &&
               isMarketHoliday("EUREX", date);
    }

    /**
     * 특정 날짜에 열린 시장 목록 반환
     */
    public List<String> getOpenMarkets(LocalDate date) {
        List<String> openMarkets = new ArrayList<>();
        
        for (String market : MARKET_HOLIDAYS_2025.keySet()) {
            if (!isMarketHoliday(market, date)) {
                openMarkets.add(market);
            }
        }
        
        return openMarkets;
    }

    /**
     * 다음 거래일 계산
     */
    public LocalDate getNextTradingDay(String market, LocalDate date) {
        LocalDate nextDay = date.plusDays(1);
        
        while (isMarketHoliday(market, nextDay)) {
            nextDay = nextDay.plusDays(1);
        }
        
        return nextDay;
    }

    /**
     * 이전 거래일 계산
     */
    public LocalDate getPreviousTradingDay(String market, LocalDate date) {
        LocalDate prevDay = date.minusDays(1);
        
        while (isMarketHoliday(market, prevDay)) {
            prevDay = prevDay.minusDays(1);
        }
        
        return prevDay;
    }

    /**
     * 배치 작업 실행 가능 여부 확인
     */
    public boolean shouldRunBatch(String batchType, LocalDate date) {
        switch (batchType) {
            case "GLOBAL":
                // 글로벌 배치는 하나 이상의 시장이 열려있으면 실행
                return !getOpenMarkets(date).isEmpty();
                
            case "ASIA":
                return !isMarketHoliday("KRX", date) || 
                       !isMarketHoliday("JPX", date);
                
            case "EUROPE":
                return !isMarketHoliday("EUREX", date);
                
            case "US":
                return !isMarketHoliday("CME", date);
                
            default:
                return true;
        }
    }

    /**
     * 휴일 정보 로깅
     */
    public void logHolidayInfo(LocalDate date) {
        List<String> openMarkets = getOpenMarkets(date);
        
        if (openMarkets.isEmpty()) {
            log.info("All major markets are closed on {}", date);
        } else {
            log.info("Open markets on {}: {}", date, String.join(", ", openMarkets));
        }
    }
}