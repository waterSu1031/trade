from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class TradingStatistics(BaseModel):
    total_trades: int
    total_volume: float
    gross_pnl: float
    net_pnl: float
    commission: float
    win_trades: int
    loss_trades: int
    win_rate: float
    largest_win: float
    largest_loss: float
    avg_win: float
    avg_loss: float
    profit_factor: float

class DailyStatistics(TradingStatistics):
    session_date: datetime
    
class AccountSummary(BaseModel):
    account_id: str
    net_liquidation: float
    total_cash_value: float
    settled_cash: float
    buying_power: float
    equity_with_loan_value: float
    gross_position_value: float
    currency: str
    last_updated: datetime

class PerformanceMetrics(BaseModel):
    daily_pnl: Dict[str, float]
    monthly_pnl: Dict[str, float]
    yearly_pnl: Dict[str, float]
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_return: Optional[float] = None
    avg_daily_return: Optional[float] = None