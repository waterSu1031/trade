"""
공통 데이터 모델 정의
모든 서비스에서 사용하는 표준화된 모델
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum

# Enums
class SecType(str, Enum):
    """증권 타입"""
    STK = "STK"      # Stock
    FUT = "FUT"      # Future
    OPT = "OPT"      # Option
    CASH = "CASH"    # Forex
    IND = "IND"      # Index
    CFD = "CFD"      # Contract for Difference
    BOND = "BOND"    # Bond
    FUND = "FUND"    # Mutual Fund
    CMDTY = "CMDTY"  # Commodity

class OrderAction(str, Enum):
    """주문 액션"""
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    """주문 타입"""
    MKT = "MKT"      # Market
    LMT = "LMT"      # Limit
    STP = "STP"      # Stop
    STP_LMT = "STP_LMT"  # Stop Limit

class OrderStatus(str, Enum):
    """주문 상태"""
    PENDING_SUBMIT = "PendingSubmit"
    PRE_SUBMITTED = "PreSubmitted"
    SUBMITTED = "Submitted"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    INACTIVE = "Inactive"

class RightType(str, Enum):
    """옵션 권리 타입"""
    C = "C"  # Call
    P = "P"  # Put

# Base Models
class ContractBase(BaseModel):
    """계약 기본 모델 (DB와 일치)"""
    con_id: int = Field(..., description="Contract ID")
    symbol: str = Field(..., description="Symbol")
    sec_type: SecType = Field(..., description="Security type")
    exchange: str = Field(..., description="Exchange")
    currency: str = Field(..., description="Currency")
    
    # Optional fields
    last_trade_date_or_contract_month: Optional[str] = None
    strike: Optional[Decimal] = None
    right_type: Optional[RightType] = None
    multiplier: Optional[str] = None
    primary_exchange: Optional[str] = None
    local_symbol: Optional[str] = None
    trading_class: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

class OrderBase(BaseModel):
    """주문 기본 모델"""
    order_id: str = Field(..., description="Order ID")
    symbol: str = Field(..., description="Symbol")
    action: OrderAction = Field(..., description="Buy/Sell")
    order_type: OrderType = Field(..., description="Order type")
    total_quantity: Decimal = Field(..., description="Total quantity")
    
    # Optional fields
    client_id: Optional[int] = None
    perm_id: Optional[int] = None
    parent_id: Optional[str] = None
    sec_type: Optional[SecType] = None
    exchange: Optional[str] = None
    lmt_price: Optional[Decimal] = None
    aux_price: Optional[Decimal] = None  # Stop price
    tif: Optional[str] = "DAY"  # Time in Force
    account: Optional[str] = None
    status: Optional[OrderStatus] = OrderStatus.PENDING_SUBMIT
    filled: Optional[Decimal] = Decimal("0")
    remaining: Optional[Decimal] = None
    avg_fill_price: Optional[Decimal] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

class PositionBase(BaseModel):
    """포지션 기본 모델"""
    symbol: str = Field(..., description="Symbol")
    quantity: Decimal = Field(..., description="Position quantity")
    avg_cost: Decimal = Field(..., description="Average cost")
    
    # Optional fields
    con_id: Optional[int] = None
    sec_type: Optional[SecType] = None
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"
    market_price: Optional[Decimal] = Decimal("0")
    market_value: Optional[Decimal] = Decimal("0")
    unrealized_pnl: Optional[Decimal] = Decimal("0")
    realized_pnl: Optional[Decimal] = Decimal("0")
    account: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

class TradeEventBase(BaseModel):
    """거래 이벤트 기본 모델"""
    exec_id: str = Field(..., description="Execution ID")
    order_id: str = Field(..., description="Order ID")
    time: datetime = Field(..., description="Execution time")
    symbol: str = Field(..., description="Symbol")
    side: str = Field(..., description="BOT/SLD")
    shares: Decimal = Field(..., description="Executed shares")
    price: Decimal = Field(..., description="Execution price")
    
    # Optional fields
    client_id: Optional[int] = None
    perm_id: Optional[int] = None
    acct_number: Optional[str] = None
    sec_type: Optional[SecType] = None
    exchange: Optional[str] = None
    position: Optional[Decimal] = None
    avg_cost: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

# Utility functions for model conversion
def to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """CamelCase를 snake_case로 변환"""
    import re
    
    def convert_key(key: str) -> str:
        # conId -> con_id 같은 특수 케이스 처리
        special_cases = {
            'conId': 'con_id',
            'orderId': 'order_id',
            'clientId': 'client_id',
            'permId': 'perm_id',
            'parentId': 'parent_id',
            'execId': 'exec_id',
            'acctNumber': 'acct_number',
            'avgFillPrice': 'avg_fill_price',
            'avgCost': 'avg_cost',
            'realizedPNL': 'realized_pnl',
            'secType': 'sec_type',
            'rightType': 'right_type',
            'primaryExchange': 'primary_exchange',
            'localSymbol': 'local_symbol',
            'tradingClass': 'trading_class',
            'lastTradeDateOrContractMonth': 'last_trade_date_or_contract_month',
            'totalQuantity': 'total_quantity',
            'lmtPrice': 'lmt_price',
            'auxPrice': 'aux_price',
            'orderType': 'order_type'
        }
        
        if key in special_cases:
            return special_cases[key]
        
        # 일반적인 camelCase 변환
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    return {convert_key(k): v for k, v in data.items()}

def to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """snake_case를 camelCase로 변환"""
    def convert_key(key: str) -> str:
        # 특수 케이스 처리
        special_cases = {
            'con_id': 'conId',
            'order_id': 'orderId',
            'client_id': 'clientId',
            'perm_id': 'permId',
            'parent_id': 'parentId',
            'exec_id': 'execId',
            'acct_number': 'acctNumber',
            'avg_fill_price': 'avgFillPrice',
            'avg_cost': 'avgCost',
            'realized_pnl': 'realizedPNL',
            'sec_type': 'secType',
            'right_type': 'rightType',
            'primary_exchange': 'primaryExchange',
            'local_symbol': 'localSymbol',
            'trading_class': 'tradingClass',
            'last_trade_date_or_contract_month': 'lastTradeDateOrContractMonth',
            'total_quantity': 'totalQuantity',
            'lmt_price': 'lmtPrice',
            'aux_price': 'auxPrice',
            'order_type': 'orderType'
        }
        
        if key in special_cases:
            return special_cases[key]
        
        # 일반적인 snake_case 변환
        components = key.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    return {convert_key(k): v for k, v in data.items()}