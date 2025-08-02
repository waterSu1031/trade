package com.trade.batch.service;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.trade.batch.repository.TradingHourRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
@Slf4j
@RequiredArgsConstructor
public class TradingHourCacheService {
    
    private final TradingHourRepository repository;
    private final TradingHourService tradingHourService;
    
    // 거래시간 캐시 (키: exchange:date)
    private final Cache<String, List<Map<String, Object>>> tradingHoursCache = 
        Caffeine.newBuilder()
            .expireAfterWrite(1, TimeUnit.HOURS)
            .maximumSize(1000)
            .recordStats()
            .build();
    
    // 거래 가능 여부 캐시 (키: exchange:date)
    private final Cache<String, Boolean> tradingDayCache = 
        Caffeine.newBuilder()
            .expireAfterWrite(24, TimeUnit.HOURS)
            .maximumSize(500)
            .recordStats()
            .build();
    
    // 현재 거래 가능 여부 캐시 (키: exchange:datetime, 5분 캐시)
    private final Cache<String, Boolean> marketOpenCache = 
        Caffeine.newBuilder()
            .expireAfterWrite(5, TimeUnit.MINUTES)
            .maximumSize(100)
            .recordStats()
            .build();
    
    /**
     * 거래시간 조회 (캐시 적용)
     */
    public List<Map<String, Object>> getTradingHours(String exchange, LocalDate date) {
        String key = exchange + ":" + date;
        
        return tradingHoursCache.get(key, k -> {
            log.debug("Loading trading hours from DB for {}", key);
            return repository.getActiveTradingHours(exchange, date);
        });
    }
    
    /**
     * 거래 가능 여부 확인 (캐시 적용)
     */
    public boolean isTradingDay(String exchange, LocalDate date) {
        String key = exchange + ":" + date;
        
        return tradingDayCache.get(key, k -> {
            log.debug("Checking trading day from DB for {}", key);
            return repository.isTradingDay(exchange, date);
        });
    }
    
    /**
     * 현재 거래 가능 여부 확인 (캐시 적용)
     */
    public boolean isMarketOpen(String exchange, LocalDateTime now) {
        // 분 단위로 캐시 키 생성 (5분 단위로 캐시)
        LocalDateTime roundedTime = now.withSecond(0).withNano(0);
        int minute = roundedTime.getMinute();
        roundedTime = roundedTime.withMinute(minute - (minute % 5));
        
        String key = exchange + ":" + roundedTime;
        
        return marketOpenCache.get(key, k -> {
            log.debug("Checking market open status for {}", key);
            return tradingHourService.isMarketOpen(exchange, now);
        });
    }
    
    /**
     * 캐시 무효화
     */
    public void invalidateCache(String exchange) {
        log.info("Invalidating cache for exchange: {}", exchange);
        
        // 해당 거래소의 모든 캐시 항목 삭제
        tradingHoursCache.asMap().entrySet().removeIf(
            entry -> entry.getKey().startsWith(exchange + ":")
        );
        tradingDayCache.asMap().entrySet().removeIf(
            entry -> entry.getKey().startsWith(exchange + ":")
        );
        marketOpenCache.asMap().entrySet().removeIf(
            entry -> entry.getKey().startsWith(exchange + ":")
        );
    }
    
    /**
     * 전체 캐시 초기화
     */
    public void clearAllCache() {
        log.info("Clearing all trading hours cache");
        tradingHoursCache.invalidateAll();
        tradingDayCache.invalidateAll();
        marketOpenCache.invalidateAll();
    }
    
    /**
     * 캐시 통계 출력
     */
    public void logCacheStats() {
        log.info("Trading Hours Cache Stats: {}", tradingHoursCache.stats());
        log.info("Trading Day Cache Stats: {}", tradingDayCache.stats());
        log.info("Market Open Cache Stats: {}", marketOpenCache.stats());
    }
    
    /**
     * 캐시 예열 (주요 거래소의 향후 7일 데이터)
     */
    public void warmupCache() {
        log.info("Warming up trading hours cache...");
        
        LocalDate today = LocalDate.now();
        List<String> majorExchanges = List.of("CME", "EUREX", "HKFE", "JPX", "KSE");
        
        for (String exchange : majorExchanges) {
            for (int i = 0; i < 7; i++) {
                LocalDate date = today.plusDays(i);
                getTradingHours(exchange, date);
                isTradingDay(exchange, date);
            }
        }
        
        log.info("Cache warmup completed");
    }
}