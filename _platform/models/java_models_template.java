/**
 * Java 모델 템플릿 (Spring Boot용)
 * 공통 모델과 일치하도록 생성
 */

package com.trade.common.models;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDateTime;

// Enums
public enum SecType {
    STK, FUT, OPT, CASH, IND, CFD, BOND, FUND, CMDTY
}

public enum OrderAction {
    BUY, SELL
}

public enum OrderType {
    MKT, LMT, STP, STP_LMT
}

public enum OrderStatus {
    PendingSubmit, PreSubmitted, Submitted, Filled, Cancelled, Inactive
}

public enum RightType {
    C, P
}

// Models
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Contract {
    private Integer conId;
    private String symbol;
    private SecType secType;
    private String exchange;
    private String currency;
    
    // Optional fields
    private String lastTradeDateOrContractMonth;
    private BigDecimal strike;
    private RightType rightType;
    private String multiplier;
    private String primaryExchange;
    private String localSymbol;
    private String tradingClass;
    private String description;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Order {
    private String orderId;
    private String symbol;
    private OrderAction action;
    private OrderType orderType;
    private BigDecimal totalQuantity;
    
    // Optional fields
    private Integer clientId;
    private Long permId;
    private String parentId;
    private SecType secType;
    private String exchange;
    private BigDecimal lmtPrice;
    private BigDecimal auxPrice;
    private String tif = "DAY";
    private String account;
    private OrderStatus status = OrderStatus.PendingSubmit;
    private BigDecimal filled = BigDecimal.ZERO;
    private BigDecimal remaining;
    private BigDecimal avgFillPrice;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Position {
    private String symbol;
    private BigDecimal quantity;
    private BigDecimal avgCost;
    
    // Optional fields
    private Integer conId;
    private SecType secType;
    private String exchange;
    private String currency = "USD";
    private BigDecimal marketPrice = BigDecimal.ZERO;
    private BigDecimal marketValue = BigDecimal.ZERO;
    private BigDecimal unrealizedPnl = BigDecimal.ZERO;
    private BigDecimal realizedPnl = BigDecimal.ZERO;
    private String account;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TradeEvent {
    private String execId;
    private String orderId;
    private LocalDateTime time;
    private String symbol;
    private String side;
    private BigDecimal shares;
    private BigDecimal price;
    
    // Optional fields
    private Integer clientId;
    private Long permId;
    private String acctNumber;
    private SecType secType;
    private String exchange;
    private BigDecimal position;
    private BigDecimal avgCost;
    private BigDecimal realizedPnl;
    private BigDecimal commission;
}