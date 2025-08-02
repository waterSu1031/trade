"""
시장 인식 연결 모니터링 서비스
- 시장별 거래 시간에 따른 연결 상태 모니터링
- 시장 개장/폐장에 따른 자동 연결 관리
- 시장별 연결 우선순위 관리
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time, timedelta
from enum import Enum
import asyncio

from tradelib import IBKRManager, RedisManager
from .trading_hour_cache import TradingHourCacheService
from .holiday_calendar import Market

logger = logging.getLogger(__name__)


class ConnectionPriority(Enum):
    """연결 우선순위"""
    CRITICAL = 1  # 핵심 시장 (항상 연결 유지)
    HIGH = 2      # 주요 시장
    NORMAL = 3    # 일반 시장
    LOW = 4       # 보조 시장


class MarketAwareConnectionMonitor:
    """시장 인식 연결 모니터링"""
    
    def __init__(
        self,
        ibkr_manager: IBKRManager,
        redis_manager: RedisManager,
        trading_hour_cache: TradingHourCacheService
    ):
        self.ibkr = ibkr_manager
        self.redis = redis_manager
        self.trading_hour_cache = trading_hour_cache
        
        # 시장별 우선순위 설정
        self.market_priorities = {
            "SMART": ConnectionPriority.CRITICAL,
            "NYSE": ConnectionPriority.CRITICAL,
            "NASDAQ": ConnectionPriority.CRITICAL,
            "CME": ConnectionPriority.HIGH,
            "EUREX": ConnectionPriority.HIGH,
            "HKFE": ConnectionPriority.NORMAL,
            "JPX": ConnectionPriority.NORMAL,
            "KRX": ConnectionPriority.NORMAL,
            "LSE": ConnectionPriority.LOW
        }
        
        # 모니터링 상태
        self.monitoring_active = False
        self.last_check = {}
        self.connection_attempts = {}
        self.market_status_cache = {}
        
        # 설정
        self.check_interval = 60  # 1분
        self.reconnect_delay = 300  # 5분
        self.max_reconnect_attempts = 3
    
    async def start_monitoring(self):
        """모니터링 시작"""
        logger.info("시장 인식 연결 모니터링 시작")
        self.monitoring_active = True
        
        # 초기 상태 확인
        await self.check_all_markets()
        
        # 주기적 모니터링 시작
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        logger.info("시장 인식 연결 모니터링 중지")
        self.monitoring_active = False
    
    async def _monitoring_loop(self):
        """모니터링 루프"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(self.check_interval)
                await self.check_all_markets()
            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
    
    async def check_all_markets(self) -> Dict[str, Any]:
        """모든 시장 상태 확인"""
        now = datetime.now()
        results = {
            "timestamp": now.isoformat(),
            "markets": {},
            "connection_status": self.ibkr.is_connected(),
            "recommendations": []
        }
        
        # 각 시장별 상태 확인
        for exchange, priority in self.market_priorities.items():
            market_status = await self.check_market_status(exchange, now)
            results["markets"][exchange] = market_status
            
            # 연결 권장사항 생성
            if market_status["is_open"] and priority in [ConnectionPriority.CRITICAL, ConnectionPriority.HIGH]:
                if not results["connection_status"]:
                    results["recommendations"].append({
                        "action": "CONNECT",
                        "reason": f"{exchange} market is open (Priority: {priority.name})"
                    })
        
        # 캐시에 저장
        await self.redis.set(
            "market_aware_connection:status",
            results,
            expire=300
        )
        
        # 필요시 자동 연결/해제
        await self._apply_recommendations(results["recommendations"])
        
        return results
    
    async def check_market_status(self, exchange: str, check_time: datetime) -> Dict[str, Any]:
        """특정 시장 상태 확인"""
        cache_key = f"{exchange}:{check_time.strftime('%Y-%m-%d:%H')}"
        
        # 캐시 확인
        if cache_key in self.market_status_cache:
            return self.market_status_cache[cache_key]
        
        # 거래 시간 확인
        is_open = await self.trading_hour_cache.is_market_open(exchange, check_time)
        
        # 다음 개장/폐장 시간 계산
        trading_hours = await self.trading_hour_cache.get_trading_hours(
            exchange, 
            check_time.date()
        )
        
        next_open = None
        next_close = None
        
        if trading_hours:
            current_time = check_time.time()
            
            for hours in trading_hours:
                if hours['open_time'] > current_time:
                    next_open = hours['open_time']
                    break
                    
                if hours['open_time'] <= current_time <= hours['close_time']:
                    next_close = hours['close_time']
                    break
        
        status = {
            "exchange": exchange,
            "is_open": is_open,
            "priority": self.market_priorities.get(exchange, ConnectionPriority.LOW).name,
            "next_open": next_open.isoformat() if next_open else None,
            "next_close": next_close.isoformat() if next_close else None,
            "last_check": check_time.isoformat()
        }
        
        # 캐시 저장 (1시간)
        self.market_status_cache[cache_key] = status
        
        return status
    
    async def _apply_recommendations(self, recommendations: List[Dict[str, Any]]):
        """권장사항 적용"""
        if not recommendations:
            return
        
        for rec in recommendations:
            if rec["action"] == "CONNECT" and not self.ibkr.is_connected():
                await self._attempt_connection(rec["reason"])
            elif rec["action"] == "DISCONNECT" and self.ibkr.is_connected():
                await self._disconnect(rec["reason"])
    
    async def _attempt_connection(self, reason: str):
        """연결 시도"""
        logger.info(f"연결 시도: {reason}")
        
        # 최근 연결 시도 확인
        last_attempt = self.connection_attempts.get("last_attempt")
        if last_attempt:
            time_since_last = (datetime.now() - last_attempt).total_seconds()
            if time_since_last < self.reconnect_delay:
                logger.debug(f"재연결 대기 중 ({self.reconnect_delay - time_since_last:.0f}초 남음)")
                return
        
        # 연결 시도
        try:
            success = await self.ibkr.reconnect()
            
            if success:
                logger.info("IBKR 연결 성공")
                self.connection_attempts["success_count"] = \
                    self.connection_attempts.get("success_count", 0) + 1
                self.connection_attempts["last_success"] = datetime.now()
                
                # 이벤트 발생
                await self.redis.publish(
                    "connection_events",
                    {
                        "event": "CONNECTED",
                        "timestamp": datetime.now().isoformat(),
                        "reason": reason
                    }
                )
            else:
                logger.warning("IBKR 연결 실패")
                self.connection_attempts["fail_count"] = \
                    self.connection_attempts.get("fail_count", 0) + 1
                
        except Exception as e:
            logger.error(f"연결 중 오류: {e}")
            self.connection_attempts["error_count"] = \
                self.connection_attempts.get("error_count", 0) + 1
        
        self.connection_attempts["last_attempt"] = datetime.now()
    
    async def _disconnect(self, reason: str):
        """연결 해제"""
        logger.info(f"연결 해제: {reason}")
        
        try:
            await self.ibkr.disconnect()
            
            # 이벤트 발생
            await self.redis.publish(
                "connection_events",
                {
                    "event": "DISCONNECTED",
                    "timestamp": datetime.now().isoformat(),
                    "reason": reason
                }
            )
        except Exception as e:
            logger.error(f"연결 해제 중 오류: {e}")
    
    async def get_market_schedule(self, date: datetime = None) -> Dict[str, Any]:
        """일일 시장 스케줄 조회"""
        if date is None:
            date = datetime.now()
        
        schedule = {
            "date": date.date().isoformat(),
            "markets": {}
        }
        
        for exchange in self.market_priorities.keys():
            trading_hours = await self.trading_hour_cache.get_trading_hours(
                exchange,
                date.date()
            )
            
            schedule["markets"][exchange] = {
                "priority": self.market_priorities[exchange].name,
                "sessions": []
            }
            
            for hours in trading_hours:
                if not hours['is_holiday']:
                    session = {
                        "open": hours['open_time'].isoformat(),
                        "close": hours['close_time'].isoformat()
                    }
                    
                    if hours['break_start'] and hours['break_end']:
                        session["break"] = {
                            "start": hours['break_start'].isoformat(),
                            "end": hours['break_end'].isoformat()
                        }
                    
                    schedule["markets"][exchange]["sessions"].append(session)
        
        return schedule
    
    async def should_connect(self) -> Dict[str, Any]:
        """연결 필요 여부 판단"""
        now = datetime.now()
        critical_markets_open = False
        high_priority_markets_open = False
        
        for exchange, priority in self.market_priorities.items():
            if await self.trading_hour_cache.is_market_open(exchange, now):
                if priority == ConnectionPriority.CRITICAL:
                    critical_markets_open = True
                elif priority == ConnectionPriority.HIGH:
                    high_priority_markets_open = True
        
        return {
            "should_connect": critical_markets_open or high_priority_markets_open,
            "critical_markets_open": critical_markets_open,
            "high_priority_markets_open": high_priority_markets_open,
            "current_connection": self.ibkr.is_connected()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return {
            "monitoring_active": self.monitoring_active,
            "connection_attempts": self.connection_attempts,
            "market_priorities": {
                k: v.name for k, v in self.market_priorities.items()
            },
            "cache_size": len(self.market_status_cache)
        }


# 전역 인스턴스
market_monitor_instance: Optional[MarketAwareConnectionMonitor] = None


async def initialize_market_aware_monitor(
    ibkr_manager: IBKRManager,
    redis_manager: RedisManager,
    trading_hour_cache: TradingHourCacheService
) -> MarketAwareConnectionMonitor:
    """시장 인식 모니터 초기화"""
    global market_monitor_instance
    
    if market_monitor_instance is None:
        market_monitor_instance = MarketAwareConnectionMonitor(
            ibkr_manager, redis_manager, trading_hour_cache
        )
        await market_monitor_instance.start_monitoring()
    
    return market_monitor_instance


async def get_market_aware_monitor() -> Optional[MarketAwareConnectionMonitor]:
    """시장 인식 모니터 인스턴스 반환"""
    return market_monitor_instance