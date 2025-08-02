from typing import Any, Dict, List
from datetime import datetime, date
from decimal import Decimal


def ibkr_to_dict(obj: Any) -> Any:
    """IBKR 객체를 Dict로 재귀적으로 변환"""
    if obj is None:
        return None
    
    # 기본 타입은 그대로 반환
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # datetime/date 처리
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    
    # Decimal 처리
    if isinstance(obj, Decimal):
        return float(obj)
    
    # 리스트 처리
    if isinstance(obj, (list, tuple)):
        return [ibkr_to_dict(item) for item in obj]
    
    # Dict는 재귀 처리
    if isinstance(obj, dict):
        return {key: ibkr_to_dict(value) for key, value in obj.items()}
    
    # 객체 처리
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            # private 속성 제외
            if not key.startswith('_'):
                result[key] = ibkr_to_dict(value)
        return result
    
    # 기타 - 문자열로 변환
    return str(obj)


def dict_to_contract(contract_dict: Dict[str, Any]):
    """Dict를 IBKR Contract 객체로 변환"""
    from ib_insync import Contract
    
    contract = Contract()
    for key, value in contract_dict.items():
        if hasattr(contract, key):
            setattr(contract, key, value)
    
    return contract


def dict_to_order(order_dict: Dict[str, Any]):
    """Dict를 IBKR Order 객체로 변환"""
    from ib_insync import Order
    
    order = Order()
    for key, value in order_dict.items():
        if hasattr(order, key):
            setattr(order, key, value)
    
    return order