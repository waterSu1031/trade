from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PositionBase(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    market_price: Optional[float] = 0.0
    market_value: Optional[float] = 0.0
    unrealized_pnl: Optional[float] = 0.0
    realized_pnl: Optional[float] = 0.0
    currency: Optional[str] = "USD"
    exchange: Optional[str] = None

class PositionCreate(PositionBase):
    pass

class PositionUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None
    market_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    is_active: Optional[bool] = None

class PositionResponse(PositionBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True