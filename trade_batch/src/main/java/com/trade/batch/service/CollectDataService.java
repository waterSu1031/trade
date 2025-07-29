package com.trade.batch.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ib.client.Bar;
import com.ib.client.Contract;
import com.ib.client.ContractDetails;
import com.trade.batch.ibkr.ClientIBKR;
import com.trade.batch.repository.CollectDataRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class CollectDataService {

    private final ClientIBKR clientIBKR;
    private final CommonService commonService;
    private final CollectDataRepository repository;
    private final ObjectMapper mapper = new ObjectMapper();


    public List<Map<String, Object>> loadSymbolFromAddCSV() {
        return repository.selectSymbolFromAddCSV();
//        return repository.selectSymbolFromFullCSV();
    }

    public Map<String, Object> fetchContractDetail(Map<String, Object> symbol) {
        int reqId = commonService.generateUniqueReqId();
        Contract contract = commonService.buildContract(symbol);
        try {
            CompletableFuture<ContractDetails> future = clientIBKR.requestContractDetailsAsync(reqId, contract);
            ContractDetails detail_cont = future.get(6, TimeUnit.SECONDS);
            return mapper.convertValue(detail_cont, new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            return Map.of();
        }
    }

    public void saveContractRel(Map<String, Object> contract_detail) {
        Contract contract_vo = (Contract) contract_detail.get("m_contract");
        Map<String, Object> contract = mapper.convertValue(contract_vo, new TypeReference<Map<String, Object>>() {});

        contract_detail = commonService.removeMPrefix(contract_detail);
        contract = commonService.removeMPrefix(contract);

        repository.insertExcXCon(contract);
        repository.upsertContract(contract);
        repository.upsertContractDetail(contract_detail);

        if("STK".equals(contract.get("sec_type")) ){
            repository.upsertContractDetailStock(contract_detail);
        }else if("FUT".equals(contract.get("sec_type"))){
            repository.upsertContractDetailFuture(contract_detail);
        }else if("OPT".equals(contract.get("sec_type"))){
            repository.upsertContractDetailOption(contract_detail);
        }else if("BOND".equals(contract.get("sec_type"))){
            repository.upsertContractDetailBond(contract_detail);
        }else if("FUND".equals(contract.get("sec_type"))){
            repository.upsertContractDetailFund(contract_detail);
        }else if("CASH".equals(contract.get("sec_type"))){
            repository.upsertContractDetailFX(contract_detail);
        }else if("IND".equals(contract.get("sec_type"))){
            repository.upsertContractDetailIndex(contract_detail);
        }

        contract.put("interval", "1m");
        repository.upsertConXData(contract);
    }

    // --------------------------------------------------------------------------------------

    public List<Map<String, Object>> loadTargetFutureContracts() {
        return repository.selectFutureMonthForNext();
    }

    public Map<String, Object> collectFutureMonth(Map<String, Object> contract) {
        LocalDate nowDate = LocalDate.now();
        String nextFutureMonth = nowDate.plusMonths(1).format(DateTimeFormatter.ofPattern("yyyyMM"));
        contract.put("sec_type", "FUT");
        contract.put("last_trade_date_or_contract_month", nextFutureMonth);

        Contract contract_vo = commonService.buildContract(contract);
        int reqId = commonService.generateUniqueReqId();

        Map<String, Object> next_contract = new HashMap<>();
        Map<String, Object> next_month = new HashMap<>();
        try {
            CompletableFuture<ContractDetails> future = clientIBKR.requestContractDetailsAsync(reqId, contract_vo);
            ContractDetails contact_detail_vo = future.get(6, TimeUnit.SECONDS);
            next_month = mapper.convertValue(contact_detail_vo.contract(), new TypeReference<Map<String, Object>>(){});
        } catch (Exception e) {
            return Map.of();
        }
        next_month = commonService.removeMPrefix(next_month);
        next_contract.put("con_id", contract.get("con_id"));
        next_contract.put("crt_month_con_id", next_month.get("conid"));
        next_contract.put("last_trade_date", next_month.get("lastTradeDate"));

        return next_contract;
    }

    public void saveFutureMonths(Map<String, Object> month) {
        repository.upsertNextFutureMonth(month);
    }

    // --------------------------------------------------------------------------------------

    public List<Map<String, Object>> loadContractForCollectTime() {
        List<Map<String, Object>> contracts = repository.selectContractForCollectTime();
        return contracts;
    }

    public List<Map<String, Object>> collectTimeData(Map<String, Object> contract) throws InterruptedException {
        DateTimeFormatter dtf = DateTimeFormatter.ofPattern("yyyyMMdd HH:mm:ss");
        String symbol = contract.get("symbol").toString();
        String exchange = contract.get("exchange").toString();
        String timeZone = commonService.exchangeTimezoneMap.get(exchange);

        String collectEndDT = LocalDate.now(ZoneId.of(timeZone)).atTime(0, 0, 0).format(dtf);
//        String collectEndDT = LocalDateTime.of(2024,12,31, 0, 0, 0).atZone(ZoneId.of(timeZone)).format(dtf);
        String collectSttDT = contract.get("end_date_loc").toString();

        int emptyCount = 0;     int fillCount = 0;     int reqId = 0;
        Contract contract_vo;
        CompletableFuture<List<Bar>> future;

        List<Map<String, Object>> times = new ArrayList<>();
        List<Map<String, Object>> time;
        while(true) {
            reqId = commonService.generateUniqueReqId();
            contract_vo = commonService.buildContract(contract);
            try {
                future = clientIBKR.requestHistoricalDataAsync(reqId, contract_vo, collectEndDT);
                List<Bar> bars = future.get(8, TimeUnit.SECONDS);

                if (bars != null && !bars.isEmpty()) {
                    time = mapper.convertValue(bars, new TypeReference<List<Map<String, Object>>>() {});

                    for(Map<String, Object> t : time){
                        t = commonService.removeMPrefix(t);
                        t.put("symbol", symbol);
                        t.put("exchange", exchange);
                        t.put("utc", t.get("time"));
                        t.put("loc", LocalDateTime.parse(t.get("time").toString(), dtf).atZone(ZoneId.of(timeZone)));
                    }

                    times.addAll(time);
                    fillCount++;
                    emptyCount = 0;
                } else {
                    emptyCount++;
                }
            }catch(Exception e){
                emptyCount++;
            }

            collectEndDT = commonService.minusDays(collectEndDT, 1);
            while(commonService.weekendDates.contains(collectEndDT.substring(0,8))){
                collectEndDT = commonService.minusDays(collectEndDT, 1);
            }
            if (fillCount == 6) {
                Thread.sleep(10_000);
                fillCount = 0;
            }
            if (emptyCount == 6) break;
            if (collectEndDT.substring(0,8).equals(collectSttDT.substring(0,8))) break;
        }

        return times;
    }

    public void saveTimeData(Map<String, Object> bar) {
        repository.insertTimeData(bar);
    }

    // --------------------------------------------------------------------------------------

    public List<Map<String, Object>> loadContractForConvertRange() {
        List<Map<String, Object>> contracts = repository.selectContractsForConvertRange();
        return contracts;
    }

    public List<Map<String, Object>> convertTimetoRange(Map<String, Object> contract) {
        List<Map<String, Object>> times = repository.selectTimeData(contract);
        System.out.println("시간데이터 >> 레인지데이터 변환");
        List<Map<String, Object>> ranges = null;
        return ranges;
    }

    public void saveRangeData(Map<String, Object> bar) {
        repository.insertRangeData(bar);
    }

}
