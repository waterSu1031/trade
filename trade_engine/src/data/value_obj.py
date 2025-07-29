from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from ib_insync import Stock, Future, Forex


class ConditionVO(BaseModel):
    symbol_list: List[str]
    stt_dt: Optional[str] = None
    end_dt: Optional[str] = None
    interval: Optional[str] = None
    strategy: Optional[str] = None
    trade_mode: Optional[str] = "back"
    real_mode: Optional[str] = "paper"


class ContractVO(BaseModel):
    # ───── 공통 필드 ─────
    con_id: int
    symbol: str
    sec_type: Literal['STK', 'CONTFUT', 'FUT', 'CASH']
    exchange: Optional[str] = Field(default=None, description="거래소")
    currency: str = Field(default="USD", description="통화")

    # ───── 선물(FUTURE) 전용 필드 ─────
    local_symbol: Optional[str] = Field(default=None, description="지역 종목")
    last_trade_date: Optional[str] = Field(default=None, description="마지막 거래일(예: 20240920)")
    multiplier: Optional[str] = Field(default=None, description="계약 승수 (예: 50)")

    # # ───── 옵션(OPTION) 전용 필드 ─────
    # strike: Optional[float] = Field(default=None, description="옵션 행사가")
    # right: Optional[Literal['C', 'P']] = Field(default=None, description="콜/풋 (C=콜, P=풋)")
    #
    # # ───── 채권(BOND) 전용 필드 ─────
    # maturity: Optional[str] = Field(default=None, description="만기일 (채권 전용)")
    # coupon: Optional[float] = Field(default=None, description="이자율")
    # cusip: Optional[str] = Field(default=None, description="미국 채권 식별번호")
    # issuer_id: Optional[str] = Field(default=None, description="발행기관 ID")

    @classmethod
    def from_rows(cls, rows: List[dict]) -> List["ContractVO"]:
        return [cls(**row) for row in rows]

    def create_contract(self):
        # 주식/외환 등
        if self.sec_type == "STK":
            return Stock(
                symbol=self.symbol,
                exchange=self.exchange or "SMART",
                currency=self.currency
            )
        if self.sec_type == "CONTFUT":
            return Future(
                symbol=self.symbol,
                exchange=self.exchange or "CME",
                secType="CONTFUT",
                currency=self.currency,
                localSymbol=self.local_symbol
            )
        elif self.sec_type == "FUT":
            return Future(
                symbol=self.symbol,
                exchange=self.exchange or "CME",
                secType="FUT",
                currency=self.currency,
                localSymbol=self.local_symbol,
                lastTradeDateOrContractMonth=self.last_trade_date,
                multiplier=self.multiplier
            )
        elif self.sec_type == "CASH":
            return Forex(
                symbol=self.symbol,
                exchange=self.exchange or "IDEALPRO",
                currency=self.currency
            )

        else:
            raise ValueError(f"Unsupported sec_type: {self.sec_type}")


class OrderVO(ContractVO):
    # ───── 주문 공통 필드 ─────
    order_id: Optional[str] = None
    action: Literal['BUY', 'SELL']
    position_side: Literal['OPEN', 'CLOSE']
    order_type: Literal['MKT', 'LMT', 'STP', 'STP LMT']
    quantity: float
    tif: Literal['DAY', 'GTC'] = "DAY"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    # ───── 전략 및 메타 정보 ─────
    strategy: Optional[str] = None
    signal_id: Optional[str] = None
    timestamp: Optional[str] = None
    user_tag: Optional[str] = None

    @classmethod
    def from_rows(cls, rows: List[dict]) -> List["OrderVO"]:
        return [cls(**row) for row in rows]
