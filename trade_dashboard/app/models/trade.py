from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TradeBase(BaseModel):
    symbol: str
    action: str
    quantity: float
    price: float
    commission: Optional[float] = 0.0
    realized_pnl: Optional[float] = 0.0
    status: str
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"

class TradeCreate(TradeBase):
    order_id: str
    execution_time: Optional[datetime] = None

class TradeUpdate(BaseModel):
    status: Optional[str] = None
    price: Optional[float] = None
    commission: Optional[float] = None
    realized_pnl: Optional[float] = None
    execution_time: Optional[datetime] = None

class TradeResponse(TradeBase):
    id: int
    order_id: str
    execution_time: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True