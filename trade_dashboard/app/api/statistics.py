from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.database.database import get_db
from app.database.models import Trade as DBTrade, Position as DBPosition, TradingSession
from app.models.statistics import TradingStatistics, DailyStatistics, AccountSummary, PerformanceMetrics
from app.services.ibkr_service import ibkr_service

router = APIRouter()

@router.get("/daily", response_model=List[DailyStatistics])
async def get_daily_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get daily trading statistics"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    daily_stats = []
    current_date = start_date
    
    while current_date <= end_date:
        start_datetime = datetime.combine(current_date, datetime.min.time())
        end_datetime = datetime.combine(current_date, datetime.max.time())
        
        trades = db.query(DBTrade).filter(
            and_(
                DBTrade.execution_time >= start_datetime,
                DBTrade.execution_time <= end_datetime,
                DBTrade.status == "FILLED"
            )
        ).all()
        
        stats = calculate_trading_statistics(trades)
        daily_stat = DailyStatistics(
            session_date=start_datetime,
            **stats.dict()
        )
        daily_stats.append(daily_stat)
        
        current_date += timedelta(days=1)
    
    return daily_stats

@router.get("/overall", response_model=TradingStatistics)
async def get_overall_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get overall trading statistics"""
    query = db.query(DBTrade).filter(DBTrade.status == "FILLED")
    
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(DBTrade.execution_time >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(DBTrade.execution_time <= end_datetime)
    
    trades = query.all()
    return calculate_trading_statistics(trades)

@router.get("/account", response_model=AccountSummary)
async def get_account_summary():
    """Get current account summary from IBKR"""
    try:
        account_data = await ibkr_service.get_account_summary()
        
        return AccountSummary(
            account_id="LIVE_ACCOUNT",
            net_liquidation=float(account_data.get("NetLiquidation", {}).get("value", 0)),
            total_cash_value=float(account_data.get("TotalCashValue", {}).get("value", 0)),
            settled_cash=float(account_data.get("SettledCash", {}).get("value", 0)),
            buying_power=float(account_data.get("BuyingPower", {}).get("value", 0)),
            equity_with_loan_value=float(account_data.get("EquityWithLoanValue", {}).get("value", 0)),
            gross_position_value=float(account_data.get("GrossPositionValue", {}).get("value", 0)),
            currency=account_data.get("Currency", {}).get("value", "USD"),
            last_updated=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account summary: {str(e)}")

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get performance metrics"""
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    if not end_date:
        end_date = date.today()
    
    # Get daily P&L
    daily_pnl = {}
    monthly_pnl = {}
    yearly_pnl = {}
    
    current_date = start_date
    while current_date <= end_date:
        start_datetime = datetime.combine(current_date, datetime.min.time())
        end_datetime = datetime.combine(current_date, datetime.max.time())
        
        daily_trades = db.query(DBTrade).filter(
            and_(
                DBTrade.execution_time >= start_datetime,
                DBTrade.execution_time <= end_datetime,
                DBTrade.status == "FILLED"
            )
        ).all()
        
        daily_net_pnl = sum(trade.realized_pnl - trade.commission for trade in daily_trades)
        daily_pnl[current_date.isoformat()] = daily_net_pnl
        
        # Monthly aggregation
        month_key = current_date.strftime("%Y-%m")
        if month_key not in monthly_pnl:
            monthly_pnl[month_key] = 0
        monthly_pnl[month_key] += daily_net_pnl
        
        # Yearly aggregation
        year_key = str(current_date.year)
        if year_key not in yearly_pnl:
            yearly_pnl[year_key] = 0
        yearly_pnl[year_key] += daily_net_pnl
        
        current_date += timedelta(days=1)
    
    # Calculate additional metrics
    daily_returns = list(daily_pnl.values())
    total_return = sum(daily_returns)
    avg_daily_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0
    
    # Simple Sharpe ratio calculation (assuming risk-free rate = 0)
    if daily_returns:
        std_dev = (sum((x - avg_daily_return) ** 2 for x in daily_returns) / len(daily_returns)) ** 0.5
        sharpe_ratio = avg_daily_return / std_dev if std_dev > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Max drawdown calculation
    cumulative_returns = []
    running_total = 0
    for ret in daily_returns:
        running_total += ret
        cumulative_returns.append(running_total)
    
    if cumulative_returns:
        peak = cumulative_returns[0]
        max_drawdown = 0
        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak != 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
    else:
        max_drawdown = 0
    
    return PerformanceMetrics(
        daily_pnl=daily_pnl,
        monthly_pnl=monthly_pnl,
        yearly_pnl=yearly_pnl,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        total_return=total_return,
        avg_daily_return=avg_daily_return
    )

@router.get("/symbols/{symbol}")
async def get_symbol_statistics(
    symbol: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get statistics for a specific symbol"""
    query = db.query(DBTrade).filter(
        and_(
            DBTrade.symbol == symbol,
            DBTrade.status == "FILLED"
        )
    )
    
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(DBTrade.execution_time >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(DBTrade.execution_time <= end_datetime)
    
    trades = query.all()
    stats = calculate_trading_statistics(trades)
    
    # Get current position for this symbol
    current_position = db.query(DBPosition).filter(
        and_(
            DBPosition.symbol == symbol,
            DBPosition.is_active == True
        )
    ).first()
    
    return {
        "symbol": symbol,
        "statistics": stats,
        "current_position": {
            "quantity": current_position.quantity if current_position else 0,
            "market_value": current_position.market_value if current_position else 0,
            "unrealized_pnl": current_position.unrealized_pnl if current_position else 0
        } if current_position else None
    }

def calculate_trading_statistics(trades: List[DBTrade]) -> TradingStatistics:
    """Calculate trading statistics from a list of trades"""
    if not trades:
        return TradingStatistics(
            total_trades=0,
            total_volume=0,
            gross_pnl=0,
            net_pnl=0,
            commission=0,
            win_trades=0,
            loss_trades=0,
            win_rate=0,
            largest_win=0,
            largest_loss=0,
            avg_win=0,
            avg_loss=0,
            profit_factor=0
        )
    
    total_trades = len(trades)
    total_volume = sum(trade.quantity * trade.price for trade in trades)
    gross_pnl = sum(trade.realized_pnl for trade in trades)
    commission = sum(trade.commission for trade in trades)
    net_pnl = gross_pnl - commission
    
    winning_trades = [trade for trade in trades if trade.realized_pnl > 0]
    losing_trades = [trade for trade in trades if trade.realized_pnl < 0]
    
    win_trades = len(winning_trades)
    loss_trades = len(losing_trades)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    
    if winning_trades:
        largest_win = max(trade.realized_pnl for trade in winning_trades)
        avg_win = sum(trade.realized_pnl for trade in winning_trades) / len(winning_trades)
    else:
        largest_win = 0
        avg_win = 0
    
    if losing_trades:
        largest_loss = min(trade.realized_pnl for trade in losing_trades)
        avg_loss = sum(trade.realized_pnl for trade in losing_trades) / len(losing_trades)
    else:
        largest_loss = 0
        avg_loss = 0
    
    # Profit factor: ratio of gross profit to gross loss
    gross_profit = sum(trade.realized_pnl for trade in winning_trades)
    gross_loss = abs(sum(trade.realized_pnl for trade in losing_trades))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    return TradingStatistics(
        total_trades=total_trades,
        total_volume=total_volume,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        commission=commission,
        win_trades=win_trades,
        loss_trades=loss_trades,
        win_rate=win_rate,
        largest_win=largest_win,
        largest_loss=largest_loss,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor
    )