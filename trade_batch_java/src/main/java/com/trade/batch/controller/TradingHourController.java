package com.trade.batch.controller;

import com.trade.batch.service.TradingHourCacheService;
import com.trade.batch.service.TradingHourDataCollector;
import com.trade.batch.service.TradingHourService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/trading-hours")
@RequiredArgsConstructor
@Slf4j
public class TradingHourController {
    
    private final TradingHourService tradingHourService;
    private final TradingHourCacheService cacheService;
    private final TradingHourDataCollector dataCollector;
    
    /**
     * 특정 거래소의 거래시간 조회
     */
    @GetMapping("/{exchange}")
    public Map<String, Object> getTradingHours(
            @PathVariable String exchange,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        
        if (date == null) {
            date = LocalDate.now();
        }
        
        Map<String, Object> response = new HashMap<>();
        response.put("exchange", exchange);
        response.put("date", date);
        response.put("tradingHours", cacheService.getTradingHours(exchange, date));
        response.put("isTradingDay", cacheService.isTradingDay(exchange, date));
        
        return response;
    }
    
    /**
     * 현재 거래 가능 여부 확인
     */
    @GetMapping("/{exchange}/is-open")
    public Map<String, Object> isMarketOpen(@PathVariable String exchange) {
        LocalDateTime now = LocalDateTime.now();
        
        Map<String, Object> response = new HashMap<>();
        response.put("exchange", exchange);
        response.put("currentTime", now);
        response.put("isOpen", cacheService.isMarketOpen(exchange, now));
        
        return response;
    }
    
    /**
     * 거래시간 데이터 수집 (수동 실행)
     */
    @PostMapping("/collect")
    public Map<String, Object> collectTradingHours(
            @RequestParam(required = false) String exchange) {
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            if (exchange != null) {
                // 특정 거래소만 수집
                tradingHourService.forceUpdateTradingHours(exchange);
                response.put("status", "success");
                response.put("message", "Trading hours collection started for " + exchange);
            } else {
                // 모든 거래소 수집
                dataCollector.collectAllExchangeTradingHours();
                response.put("status", "success");
                response.put("message", "Trading hours collection started for all exchanges");
            }
        } catch (Exception e) {
            response.put("status", "error");
            response.put("message", e.getMessage());
        }
        
        return response;
    }
    
    /**
     * FIX 거래시간 초기화
     */
    @PostMapping("/initialize-fix")
    public Map<String, Object> initializeFixTradingHours() {
        Map<String, Object> response = new HashMap<>();
        
        try {
            tradingHourService.initializeFixTradingHours();
            response.put("status", "success");
            response.put("message", "FIX trading hours initialized");
        } catch (Exception e) {
            response.put("status", "error");
            response.put("message", e.getMessage());
        }
        
        return response;
    }
    
    /**
     * 수동 거래시간 입력
     */
    @PostMapping("/manual")
    public Map<String, Object> insertManualTradingHours() {
        Map<String, Object> response = new HashMap<>();
        
        try {
            dataCollector.insertManualTradingHours();
            response.put("status", "success");
            response.put("message", "Manual trading hours inserted");
        } catch (Exception e) {
            response.put("status", "error");
            response.put("message", e.getMessage());
        }
        
        return response;
    }
    
    /**
     * 캐시 무효화
     */
    @DeleteMapping("/cache/{exchange}")
    public Map<String, Object> invalidateCache(@PathVariable String exchange) {
        cacheService.invalidateCache(exchange);
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Cache invalidated for " + exchange);
        
        return response;
    }
    
    /**
     * 캐시 통계
     */
    @GetMapping("/cache/stats")
    public Map<String, Object> getCacheStats() {
        cacheService.logCacheStats();
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("message", "Cache stats logged");
        
        return response;
    }
    
    /**
     * 주간 거래시간 업데이트 (수동 실행)
     */
    @PostMapping("/update-weekly")
    public Map<String, Object> updateWeeklyTradingHours() {
        Map<String, Object> response = new HashMap<>();
        
        try {
            tradingHourService.updateWeeklyTradingHours();
            response.put("status", "success");
            response.put("message", "Weekly trading hours update started");
        } catch (Exception e) {
            response.put("status", "error");
            response.put("message", e.getMessage());
        }
        
        return response;
    }
}