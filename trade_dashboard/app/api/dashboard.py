"""
대시보드 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from enum import Enum

router = APIRouter()


class TimeRange(str, Enum):
    """시간 범위"""
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1m"
    MONTH_3 = "3m"
    MONTH_6 = "6m"
    YEAR_1 = "1y"
    ALL = "all"


class DashboardSummary(BaseModel):
    """대시보드 요약 정보"""
    total_equity: float
    daily_pnl: float
    daily_pnl_percent: float
    weekly_pnl: float
    weekly_pnl_percent: float
    monthly_pnl: float
    monthly_pnl_percent: float
    total_positions: int
    active_strategies: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    last_updated: datetime


class PerformanceMetrics(BaseModel):
    """성과 지표"""
    date: date
    equity: float
    daily_return: float
    cumulative_return: float
    drawdown: float
    volume: int
    trades: int


class TopPerformer(BaseModel):
    """상위 성과 종목/전략"""
    name: str
    type: str  # "stock" or "strategy"
    pnl: float
    pnl_percent: float
    trades: int


class MarketOverview(BaseModel):
    """시장 개요"""
    spy_price: float
    spy_change: float
    spy_change_percent: float
    vix_level: float
    vix_change: float
    market_sentiment: str  # "bullish", "neutral", "bearish"
    

class AlertInfo(BaseModel):
    """알림 정보"""
    id: str
    type: str  # "risk", "opportunity", "system"
    severity: str  # "info", "warning", "critical"
    message: str
    timestamp: datetime
    is_read: bool = False


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """대시보드 요약 정보 조회"""
    # TODO: 실제 데이터 계산
    return {
        "total_equity": 155000.0,
        "daily_pnl": 1250.50,
        "daily_pnl_percent": 0.82,
        "weekly_pnl": 3500.0,
        "weekly_pnl_percent": 2.31,
        "monthly_pnl": 8200.0,
        "monthly_pnl_percent": 5.59,
        "total_positions": 8,
        "active_strategies": 2,
        "win_rate": 68.5,
        "sharpe_ratio": 1.85,
        "max_drawdown": -4.2,
        "last_updated": datetime.now()
    }


@router.get("/performance", response_model=List[PerformanceMetrics])
async def get_performance_history(
    range: TimeRange = TimeRange.MONTH_1,
    resolution: str = "daily"  # "daily", "hourly", "weekly"
):
    """성과 이력 조회"""
    # TODO: 실제 성과 데이터 조회
    metrics = []
    
    # 샘플 데이터 생성
    base_equity = 150000
    days = 30 if range == TimeRange.MONTH_1 else 7
    
    for i in range(days):
        date_val = date.today() - timedelta(days=days-i-1)
        daily_return = (i % 3 - 1) * 0.5  # -0.5% to 1% daily returns
        equity = base_equity * (1 + daily_return / 100)
        
        metrics.append({
            "date": date_val,
            "equity": equity,
            "daily_return": daily_return,
            "cumulative_return": (equity - base_equity) / base_equity * 100,
            "drawdown": min(0, daily_return - 2),
            "volume": 50000 + i * 1000,
            "trades": 10 + i % 5
        })
        
        base_equity = equity
    
    return metrics


@router.get("/top-performers", response_model=List[TopPerformer])
async def get_top_performers(
    type: Optional[str] = None,  # "stock", "strategy", or None for all
    limit: int = Query(5, le=20)
):
    """상위 성과 종목/전략 조회"""
    # TODO: 실제 상위 성과자 조회
    performers = [
        {
            "name": "AAPL",
            "type": "stock",
            "pnl": 2500.0,
            "pnl_percent": 15.5,
            "trades": 25
        },
        {
            "name": "Example1Strategy",
            "type": "strategy",
            "pnl": 3200.0,
            "pnl_percent": 8.2,
            "trades": 150
        },
        {
            "name": "TSLA",
            "type": "stock",
            "pnl": -800.0,
            "pnl_percent": -5.2,
            "trades": 18
        }
    ]
    
    if type:
        performers = [p for p in performers if p["type"] == type]
    
    # Sort by PnL descending
    performers.sort(key=lambda x: x["pnl"], reverse=True)
    
    return performers[:limit]


@router.get("/market-overview", response_model=MarketOverview)
async def get_market_overview():
    """시장 개요 조회"""
    # TODO: 실제 시장 데이터 조회
    return {
        "spy_price": 445.25,
        "spy_change": 2.15,
        "spy_change_percent": 0.48,
        "vix_level": 15.3,
        "vix_change": -0.5,
        "market_sentiment": "bullish"
    }


@router.get("/alerts", response_model=List[AlertInfo])
async def get_alerts(
    unread_only: bool = False,
    limit: int = Query(10, le=50)
):
    """알림 목록 조회"""
    # TODO: 실제 알림 데이터 조회
    alerts = [
        {
            "id": "1",
            "type": "risk",
            "severity": "warning",
            "message": "포트폴리오 변동성이 설정된 임계값을 초과했습니다",
            "timestamp": datetime.now() - timedelta(hours=1),
            "is_read": False
        },
        {
            "id": "2",
            "type": "opportunity",
            "severity": "info",
            "message": "AAPL이 매수 신호를 생성했습니다",
            "timestamp": datetime.now() - timedelta(hours=2),
            "is_read": True
        },
        {
            "id": "3",
            "type": "system",
            "severity": "critical",
            "message": "IBKR 연결이 일시적으로 끊어졌습니다",
            "timestamp": datetime.now() - timedelta(hours=3),
            "is_read": False
        }
    ]
    
    if unread_only:
        alerts = [a for a in alerts if not a["is_read"]]
    
    return alerts[:limit]


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """알림을 읽음으로 표시"""
    # TODO: 실제 알림 상태 업데이트
    return {"message": f"Alert {alert_id} marked as read"}


@router.get("/activity-feed")
async def get_activity_feed(limit: int = Query(20, le=100)):
    """최근 활동 피드 조회"""
    # TODO: 실제 활동 데이터 조회
    activities = []
    
    for i in range(10):
        activities.append({
            "timestamp": datetime.now() - timedelta(minutes=i*15),
            "type": "trade",
            "description": f"{'매수' if i % 2 == 0 else '매도'} AAPL 100주 @ $150.{i}0",
            "strategy": "Example1Strategy"
        })
    
    return {"activities": activities[:limit], "count": len(activities)}


@router.get("/risk-metrics")
async def get_risk_metrics():
    """리스크 지표 조회"""
    # TODO: 실제 리스크 지표 계산
    return {
        "var_95": -2500.0,  # 95% VaR
        "var_99": -3500.0,  # 99% VaR
        "beta": 0.85,
        "correlation_spy": 0.72,
        "position_concentration": 0.25,  # 최대 포지션 비중
        "leverage": 1.2,
        "margin_usage": 0.45
    }