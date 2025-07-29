"""
실시간 데이터 REST API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.realtime_service import realtime_service

router = APIRouter()

class PositionUpdate(BaseModel):
    """포지션 업데이트 요청"""
    symbol: str
    qty: int
    avg_price: float

class AlertCreate(BaseModel):
    """알림 생성 요청"""
    type: str
    severity: str
    symbol: Optional[str] = None
    message: str

@router.get("/prices")
async def get_current_prices() -> Dict[str, float]:
    """현재 가격 조회"""
    return realtime_service.get_current_prices()

@router.get("/prices/{symbol}")
async def get_symbol_price(symbol: str) -> Dict[str, Any]:
    """특정 심볼 가격 조회"""
    prices = realtime_service.get_current_prices()
    if symbol not in prices:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    return {
        "symbol": symbol,
        "price": prices[symbol],
        "timestamp": None  # Would be set from actual market data
    }

@router.get("/positions")
async def get_positions() -> List[Dict[str, Any]]:
    """현재 포지션 목록 조회"""
    return realtime_service.get_positions()

@router.post("/positions")
async def add_position(position: PositionUpdate) -> Dict[str, str]:
    """포지션 추가"""
    realtime_service.add_position(
        symbol=position.symbol,
        qty=position.qty,
        avg_price=position.avg_price
    )
    return {"message": f"Position added for {position.symbol}"}

@router.put("/positions/{symbol}")
async def update_position(symbol: str, position: PositionUpdate) -> Dict[str, str]:
    """포지션 업데이트"""
    realtime_service.update_position(
        symbol=symbol,
        qty=position.qty,
        avg_price=position.avg_price
    )
    return {"message": f"Position updated for {symbol}"}

@router.delete("/positions/{symbol}")
async def remove_position(symbol: str) -> Dict[str, str]:
    """포지션 제거"""
    realtime_service.remove_position(symbol)
    return {"message": f"Position removed for {symbol}"}

@router.get("/alerts")
async def get_recent_alerts(limit: int = 10) -> List[Dict[str, Any]]:
    """최근 알림 조회"""
    return realtime_service.get_recent_alerts(limit)

@router.post("/alerts")
async def create_alert(alert: AlertCreate) -> Dict[str, str]:
    """수동 알림 생성"""
    from datetime import datetime
    
    alert_data = {
        "id": f"alert_{datetime.now().timestamp()}",
        "type": alert.type,
        "severity": alert.severity,
        "symbol": alert.symbol,
        "message": alert.message,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add to queue and broadcast
    realtime_service.alert_queue.append(alert_data)
    
    # Broadcast to alert subscribers
    alert_message = {
        "type": "alert",
        "data": alert_data
    }
    
    for subscriber in realtime_service.alert_subscribers:
        await subscriber(alert_message)
    
    return {"message": "Alert created successfully", "alert_id": alert_data["id"]}

@router.get("/status")
async def get_realtime_status() -> Dict[str, Any]:
    """실시간 서비스 상태 조회"""
    return {
        "running": realtime_service.update_task is not None and not realtime_service.update_task.done(),
        "price_subscribers": len(realtime_service.price_subscribers),
        "position_subscribers": len(realtime_service.position_subscribers),
        "alert_subscribers": len(realtime_service.alert_subscribers),
        "active_symbols": list(realtime_service.current_prices.keys()),
        "active_positions": len(realtime_service.positions),
        "alert_queue_size": len(realtime_service.alert_queue)
    }