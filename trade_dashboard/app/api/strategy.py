"""
전략 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

router = APIRouter()


class StrategyInfo(BaseModel):
    """전략 정보 모델"""
    name: str
    description: str
    version: str
    is_active: bool
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class StrategyParameter(BaseModel):
    """전략 파라미터 모델"""
    name: str
    value: Any
    type: str
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    

class StrategyPerformance(BaseModel):
    """전략 성과 모델"""
    strategy_name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_profit: float
    avg_loss: float
    last_updated: datetime


@router.get("/", response_model=List[StrategyInfo])
async def get_strategies():
    """사용 가능한 모든 전략 목록 조회"""
    # TODO: 실제 전략 목록을 trade_engine에서 가져오기
    strategies = [
        {
            "name": "Example1Strategy",
            "description": "예제 전략 1 - 이동평균 크로스오버",
            "version": "1.0.0",
            "is_active": True,
            "parameters": {
                "fast_period": 10,
                "slow_period": 20,
                "stop_loss": 0.02,
                "take_profit": 0.05
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "name": "Example2Strategy", 
            "description": "예제 전략 2 - RSI 기반 전략",
            "version": "1.0.0",
            "is_active": False,
            "parameters": {
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    return strategies


@router.get("/{strategy_name}", response_model=StrategyInfo)
async def get_strategy(strategy_name: str):
    """특정 전략 상세 정보 조회"""
    # TODO: 실제 전략 정보 조회
    if strategy_name not in ["Example1Strategy", "Example2Strategy"]:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")
    
    return {
        "name": strategy_name,
        "description": f"{strategy_name} 설명",
        "version": "1.0.0",
        "is_active": True,
        "parameters": {},
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


@router.get("/{strategy_name}/performance", response_model=StrategyPerformance)
async def get_strategy_performance(strategy_name: str, period: str = "1d"):
    """전략 성과 조회"""
    # TODO: 실제 성과 데이터 조회
    return {
        "strategy_name": strategy_name,
        "total_return": 15.5,
        "sharpe_ratio": 1.8,
        "max_drawdown": -5.2,
        "win_rate": 65.0,
        "profit_factor": 2.1,
        "total_trades": 100,
        "winning_trades": 65,
        "losing_trades": 35,
        "avg_profit": 120.5,
        "avg_loss": -57.3,
        "last_updated": datetime.now()
    }


@router.post("/{strategy_name}/activate")
async def activate_strategy(strategy_name: str):
    """전략 활성화"""
    # TODO: trade_engine에 전략 활성화 요청
    return {"message": f"Strategy {strategy_name} activated successfully"}


@router.post("/{strategy_name}/deactivate")
async def deactivate_strategy(strategy_name: str):
    """전략 비활성화"""
    # TODO: trade_engine에 전략 비활성화 요청
    return {"message": f"Strategy {strategy_name} deactivated successfully"}


@router.put("/{strategy_name}/parameters")
async def update_strategy_parameters(
    strategy_name: str,
    parameters: Dict[str, Any]
):
    """전략 파라미터 업데이트"""
    # TODO: 파라미터 유효성 검사 및 업데이트
    return {
        "message": f"Strategy {strategy_name} parameters updated",
        "parameters": parameters
    }


@router.get("/{strategy_name}/signals")
async def get_strategy_signals(
    strategy_name: str,
    limit: int = 100
):
    """전략 신호 이력 조회"""
    # TODO: 실제 신호 데이터 조회
    signals = []
    return {"strategy": strategy_name, "signals": signals, "count": len(signals)}