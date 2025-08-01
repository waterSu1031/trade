package com.trade.batch.service;

import com.ib.client.Contract;
import com.trade.batch.repository.CollectDataRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;


//@Component
@Service
public class CommonService {

    private final AtomicInteger reqIdGen = new AtomicInteger(10000);
    private final CollectDataRepository repository;
    Set<String> weekendDates = new HashSet<>();
    Map<String, String> exchangeTimezoneMap = new HashMap<>();

    public CommonService(CollectDataRepository repository) {
        this.repository = repository;
        loadWeekendCache(2022, 2025);
    }
    
    @jakarta.annotation.PostConstruct
    public void init() {
        try {
            loadExchangeTimezoneCache();
        } catch (Exception e) {
            // Log error but don't fail startup
            System.err.println("Failed to load exchange timezone cache: " + e.getMessage());
        }
    }

    public int generateUniqueReqId() {
        return reqIdGen.getAndIncrement();
    }

    // 휴일 캐쉬저장.

    public Contract buildContract(Map<String, Object> contract) {
        Contract contract_vo = new Contract();

        String symbol = String.valueOf(contract.get("symbol"));
        String sec_type = String.valueOf(contract.get("sec_type")).toUpperCase();
        String exchange = String.valueOf(contract.get("exchange"));
        String currency = String.valueOf(contract.get("currency"));

        String lastTradeDateOrContractMonth =
                contract.containsKey("lasttradedateorcontractmonth")
                ? String.valueOf(contract.get("lasttradedateorcontractmonth"))
                : null;

        contract_vo.symbol(symbol);
        contract_vo.secType(sec_type);
        contract_vo.exchange(exchange);
        contract_vo.currency(currency);

        if ("FUT".equals(sec_type)) {
            contract_vo.lastTradeDateOrContractMonth(lastTradeDateOrContractMonth);
        }
        return contract_vo;
    }

    public boolean isWithin7Days(String dateStr1, String dateStr2) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");
        LocalDate d1 = LocalDate.parse(dateStr1, formatter);
        LocalDate d2 = LocalDate.parse(dateStr2, formatter);
        long diff = Math.abs(ChronoUnit.DAYS.between(d1, d2));
        return diff <= 7;
    }

    // 오늘 날짜로 장 종료시간 세팅
    public String getTodaySessionCloseTime(int hour, int min) {
        LocalDate today = LocalDate.now();
        LocalDateTime dt = today.atTime(hour, min, 0);
        return dt.format(DateTimeFormatter.ofPattern("yyyyMMdd HH:mm:ss"));
    }

    // endDateTime 문자열에서 하루 전(거래일)로 이동
    public String minusDays(String endDateTimeStr, int days) {
        LocalDateTime dt = LocalDateTime.parse(endDateTimeStr, DateTimeFormatter.ofPattern("yyyyMMdd HH:mm:ss"));
        LocalDateTime prev = dt.minusDays(days);
        return prev.format(DateTimeFormatter.ofPattern("yyyyMMdd HH:mm:ss"));
    }

    public Map<String, Object> removeMPrefix(Map<String, Object> input) {
        Map<String, Object> result = new HashMap<>();
        input.forEach((key, value) -> {
            String newKey = key.startsWith("m_") ? key.substring(2) : key;
            if (value instanceof Map) {
                result.put(newKey, removeMPrefix((Map<String, Object>) value));
            } else if (value instanceof List) {
                List<?> list = (List<?>) value;
                List<Object> newList = new ArrayList<>();
                for (Object obj : list) {
                    newList.add(obj instanceof Map ? removeMPrefix((Map<String, Object>) obj) : obj);
                }
                result.put(newKey, newList);
            } else {
                result.put(newKey, value);
            }
        });
        return result;
    }

    public void loadWeekendCache(int stt_year, int end_year) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");
        LocalDate day = LocalDate.of(stt_year, 1, 1);
        LocalDate last = LocalDate.of(end_year, 12, 31);

        while (!day.isAfter(last)) {
            DayOfWeek dow = day.getDayOfWeek();
            if (dow == DayOfWeek.SATURDAY || dow == DayOfWeek.SUNDAY) {
                weekendDates.add(day.format(formatter));  // String("yyyyMMdd") 형태로 저장
            }
            day = day.plusDays(1);
        }
    }

    public void loadExchangeTimezoneCache() {
        List<Map<String, Object>> rows = repository.selectExchangeTimeZone();
        for (Map<String, Object> row : rows) {
            String exchange = (String) row.get("exchange");
            String timezone = (String) row.get("timezone");
            exchangeTimezoneMap.put(exchange, timezone);
        }
    }

}