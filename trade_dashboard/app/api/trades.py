from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from app.database.database import get_db
from app.database.models import Trade as DBTrade
from app.models.trade import TradeResponse, TradeCreate, TradeUpdate
from app.services.ibkr_service import ibkr_service

router = APIRouter()

@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    symbol: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get trades with optional filtering"""
    query = db.query(DBTrade)
    
    if symbol:
        query = query.filter(DBTrade.symbol == symbol)
    
    if start_date:
        query = query.filter(DBTrade.execution_time >= start_date)
    
    if end_date:
        query = query.filter(DBTrade.execution_time <= end_date)
    
    trades = query.order_by(DBTrade.execution_time.desc()).offset(skip).limit(limit).all()
    return trades

@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade by ID"""
    trade = db.query(DBTrade).filter(DBTrade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

@router.post("/", response_model=TradeResponse)
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    """Create a new trade record"""
    db_trade = DBTrade(**trade.dict())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: int, 
    trade_update: TradeUpdate, 
    db: Session = Depends(get_db)
):
    """Update a trade record"""
    db_trade = db.query(DBTrade).filter(DBTrade.id == trade_id).first()
    if not db_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    update_data = trade_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_trade, field, value)
    
    db.commit()
    db.refresh(db_trade)
    return db_trade

@router.get("/live/recent", response_model=List[dict])
async def get_recent_live_trades():
    """Get recent trades from IBKR"""
    try:
        trades = await ibkr_service.get_trades()
        return [
            {
                "orderId": trade.order.orderId,
                "symbol": trade.contract.symbol,
                "action": trade.order.action,
                "quantity": trade.order.totalQuantity,
                "status": trade.orderStatus.status,
                "filled": trade.orderStatus.filled,
                "avgFillPrice": trade.orderStatus.avgFillPrice,
                "commission": getattr(trade.orderStatus, 'commission', 0.0)
            }
            for trade in trades
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching live trades: {str(e)}")

@router.get("/summary/daily")
async def get_daily_trade_summary(
    trade_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get daily trade summary"""
    if not trade_date:
        trade_date = date.today()
    
    start_datetime = datetime.combine(trade_date, datetime.min.time())
    end_datetime = datetime.combine(trade_date, datetime.max.time())
    
    trades = db.query(DBTrade).filter(
        DBTrade.execution_time >= start_datetime,
        DBTrade.execution_time <= end_datetime,
        DBTrade.status == "FILLED"
    ).all()
    
    total_trades = len(trades)
    total_volume = sum(trade.quantity * trade.price for trade in trades)
    total_commission = sum(trade.commission for trade in trades)
    total_pnl = sum(trade.realized_pnl for trade in trades)
    
    buy_trades = [t for t in trades if t.action == "BUY"]
    sell_trades = [t for t in trades if t.action == "SELL"]
    
    return {
        "date": trade_date,
        "total_trades": total_trades,
        "buy_trades": len(buy_trades),
        "sell_trades": len(sell_trades),
        "total_volume": total_volume,
        "total_commission": total_commission,
        "realized_pnl": total_pnl,
        "net_pnl": total_pnl - total_commission
    }