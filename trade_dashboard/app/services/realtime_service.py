"""
실시간 데이터 처리 서비스
"""
import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
import json


class RealtimeDataService:
    """실시간 시장 데이터 및 포지션 업데이트 서비스"""
    
    def __init__(self):
        self.price_subscribers = []
        self.position_subscribers = []
        self.alert_subscribers = []
        
        # 모의 데이터를 위한 가격 정보
        self.current_prices = {
            "AAPL": 195.50,
            "GOOGL": 155.20,
            "MSFT": 420.30,
            "TSLA": 245.60,
            "SPY": 485.50,
            "QQQ": 420.80,
            "ES": 5150.00,
            "NQ": 18250.00
        }
        
        # 포지션 정보
        self.positions = {
            "AAPL": {"qty": 100, "avg_price": 190.00, "symbol": "AAPL"},
            "GOOGL": {"qty": 50, "avg_price": 150.00, "symbol": "GOOGL"},
            "ES": {"qty": 2, "avg_price": 5100.00, "symbol": "ES"}
        }
        
        # 알림 큐
        self.alert_queue = deque(maxlen=100)
        
        # 실시간 업데이트 태스크
        self.update_task = None
        
    async def start(self):
        """실시간 데이터 업데이트 시작"""
        self.update_task = asyncio.create_task(self._update_loop())
        
    async def stop(self):
        """실시간 데이터 업데이트 중지"""
        if self.update_task:
            self.update_task.cancel()
            
    async def _update_loop(self):
        """실시간 데이터 업데이트 루프"""
        while True:
            try:
                # 1초마다 가격 업데이트
                await self._update_prices()
                await self._update_positions()
                await self._check_alerts()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Update loop error: {e}")
                await asyncio.sleep(5)
                
    async def _update_prices(self):
        """가격 데이터 업데이트 (시뮬레이션)"""
        for symbol in self.current_prices:
            # 랜덤 가격 변동 (-0.5% ~ +0.5%)
            change = random.uniform(-0.005, 0.005)
            self.current_prices[symbol] *= (1 + change)
            
        # 모든 구독자에게 브로드캐스트
        price_data = {
            "type": "price_update",
            "timestamp": datetime.now().isoformat(),
            "data": self.current_prices
        }
        
        for subscriber in self.price_subscribers:
            await subscriber(price_data)
            
    async def _update_positions(self):
        """포지션 손익 업데이트"""
        position_updates = []
        
        for symbol, position in self.positions.items():
            if symbol in self.current_prices:
                current_price = self.current_prices[symbol]
                avg_price = position["avg_price"]
                qty = position["qty"]
                
                # 손익 계산
                unrealized_pnl = (current_price - avg_price) * qty
                pnl_percent = ((current_price - avg_price) / avg_price) * 100
                
                position_update = {
                    "symbol": symbol,
                    "qty": qty,
                    "avg_price": avg_price,
                    "current_price": current_price,
                    "unrealized_pnl": unrealized_pnl,
                    "pnl_percent": pnl_percent,
                    "market_value": current_price * qty
                }
                position_updates.append(position_update)
        
        # 포지션 구독자에게 브로드캐스트
        if position_updates:
            position_data = {
                "type": "position_update",
                "timestamp": datetime.now().isoformat(),
                "data": position_updates
            }
            
            for subscriber in self.position_subscribers:
                await subscriber(position_data)
                
    async def _check_alerts(self):
        """알림 조건 체크 및 발송"""
        # 예시: 특정 조건 체크
        for symbol, price in self.current_prices.items():
            # 급격한 가격 변동 체크 (시뮬레이션)
            if random.random() < 0.01:  # 1% 확률로 알림 생성
                alert = {
                    "id": f"alert_{datetime.now().timestamp()}",
                    "type": "price_alert",
                    "severity": random.choice(["info", "warning", "critical"]),
                    "symbol": symbol,
                    "message": f"{symbol} 가격이 급격히 변동했습니다: ${price:.2f}",
                    "timestamp": datetime.now().isoformat()
                }
                
                self.alert_queue.append(alert)
                
                # 알림 구독자에게 브로드캐스트
                alert_data = {
                    "type": "alert",
                    "data": alert
                }
                
                for subscriber in self.alert_subscribers:
                    await subscriber(alert_data)
    
    def subscribe_prices(self, callback):
        """가격 업데이트 구독"""
        self.price_subscribers.append(callback)
        
    def unsubscribe_prices(self, callback):
        """가격 업데이트 구독 해제"""
        if callback in self.price_subscribers:
            self.price_subscribers.remove(callback)
            
    def subscribe_positions(self, callback):
        """포지션 업데이트 구독"""
        self.position_subscribers.append(callback)
        
    def unsubscribe_positions(self, callback):
        """포지션 업데이트 구독 해제"""
        if callback in self.position_subscribers:
            self.position_subscribers.remove(callback)
            
    def subscribe_alerts(self, callback):
        """알림 구독"""
        self.alert_subscribers.append(callback)
        
    def unsubscribe_alerts(self, callback):
        """알림 구독 해제"""
        if callback in self.alert_subscribers:
            self.alert_subscribers.remove(callback)
            
    def get_current_prices(self) -> Dict[str, float]:
        """현재 가격 조회"""
        return self.current_prices.copy()
        
    def get_positions(self) -> List[Dict[str, Any]]:
        """현재 포지션 조회"""
        positions = []
        for symbol, position in self.positions.items():
            if symbol in self.current_prices:
                current_price = self.current_prices[symbol]
                avg_price = position["avg_price"]
                qty = position["qty"]
                
                positions.append({
                    "symbol": symbol,
                    "qty": qty,
                    "avg_price": avg_price,
                    "current_price": current_price,
                    "unrealized_pnl": (current_price - avg_price) * qty,
                    "pnl_percent": ((current_price - avg_price) / avg_price) * 100,
                    "market_value": current_price * qty
                })
        return positions
        
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 알림 조회"""
        return list(self.alert_queue)[-limit:]
        
    def add_position(self, symbol: str, qty: int, avg_price: float):
        """포지션 추가"""
        self.positions[symbol] = {
            "qty": qty,
            "avg_price": avg_price,
            "symbol": symbol
        }
        
    def remove_position(self, symbol: str):
        """포지션 제거"""
        if symbol in self.positions:
            del self.positions[symbol]
            
    def update_position(self, symbol: str, qty: int, avg_price: float):
        """포지션 업데이트"""
        if symbol in self.positions:
            self.positions[symbol]["qty"] = qty
            self.positions[symbol]["avg_price"] = avg_price


# 싱글톤 인스턴스
realtime_service = RealtimeDataService()