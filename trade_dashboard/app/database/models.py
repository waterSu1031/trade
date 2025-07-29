from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database.database import Base

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    status = Column(String, nullable=False)  # FILLED, PENDING, CANCELLED
    exchange = Column(String)
    currency = Column(String, default="USD")
    execution_time = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    market_price = Column(Float, default=0.0)
    market_value = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    exchange = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TradingSession(Base):
    __tablename__ = "trading_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_date = Column(DateTime, nullable=False)
    total_trades = Column(Integer, default=0)
    total_volume = Column(Float, default=0.0)
    gross_pnl = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    win_trades = Column(Integer, default=0)
    loss_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    largest_win = Column(Float, default=0.0)
    largest_loss = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, unique=True, index=True, nullable=False)
    net_liquidation = Column(Float, default=0.0)
    total_cash_value = Column(Float, default=0.0)
    settled_cash = Column(Float, default=0.0)
    accrued_cash = Column(Float, default=0.0)
    buying_power = Column(Float, default=0.0)
    equity_with_loan_value = Column(Float, default=0.0)
    previous_day_equity_with_loan_value = Column(Float, default=0.0)
    gross_position_value = Column(Float, default=0.0)
    reg_t_equity = Column(Float, default=0.0)
    reg_t_margin = Column(Float, default=0.0)
    sma = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())