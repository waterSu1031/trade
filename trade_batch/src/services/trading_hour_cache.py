"""
거래시간 캐시 서비스
- 거래시간 정보 캐싱
- 거래일 여부 캐싱
- 시장 개장 상태 캐싱
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from cachetools import TTLCache
import asyncio

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class TradingHourCacheService:
    """거래시간 캐시 서비스"""
    
    def __init__(self, db_manager: DatabaseManager, redis_manager: RedisManager):
        self.db = db_manager
        self.redis = redis_manager
        
        # 메모리 캐시 (TTL 캐시)
        self.trading_hours_cache = TTLCache(maxsize=1000, ttl=3600)  # 1시간
        self.trading_day_cache = TTLCache(maxsize=500, ttl=86400)  # 24시간
        self.market_open_cache = TTLCache(maxsize=100, ttl=300)  # 5분
        
        # 캐시 통계
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    async def get_trading_hours(self, exchange: str, check_date: date) -> List[Dict[str, Any]]:
        """거래시간 조회 (캐시 적용)"""
        cache_key = f"{exchange}:{check_date.isoformat()}"
        
        # 메모리 캐시 확인
        if cache_key in self.trading_hours_cache:
            self.cache_stats['hits'] += 1
            return self.trading_hours_cache[cache_key]
        
        # Redis 캐시 확인
        redis_key = f"trading_hours:{cache_key}"
        cached_data = await self.redis.get(redis_key)
        
        if cached_data:
            self.cache_stats['hits'] += 1
            self.trading_hours_cache[cache_key] = cached_data
            return cached_data
        
        # DB에서 조회
        self.cache_stats['misses'] += 1
        logger.debug(f"Loading trading hours from DB for {cache_key}")
        
        trading_hours = await self.db.fetch("""
            SELECT 
                exchange,
                trading_date,
                open_time,
                close_time,
                break_start,
                break_end,
                time_zone,
                is_holiday,
                holiday_name
            FROM trading_hours
            WHERE exchange = $1 AND trading_date = $2
            AND is_active = true
            ORDER BY open_time
        """, exchange, check_date)
        
        result = [dict(row) for row in trading_hours]
        
        # 캐시 저장
        self.trading_hours_cache[cache_key] = result
        await self.redis.set(redis_key, result, expire=3600)
        
        return result
    
    async def is_trading_day(self, exchange: str, check_date: date) -> bool:
        """거래일 여부 확인 (캐시 적용)"""
        cache_key = f"{exchange}:{check_date.isoformat()}"
        
        # 메모리 캐시 확인
        if cache_key in self.trading_day_cache:
            self.cache_stats['hits'] += 1
            return self.trading_day_cache[cache_key]
        
        # Redis 캐시 확인
        redis_key = f"trading_day:{cache_key}"
        cached_data = await self.redis.get(redis_key)
        
        if cached_data is not None:
            self.cache_stats['hits'] += 1
            self.trading_day_cache[cache_key] = cached_data
            return cached_data
        
        # DB에서 확인
        self.cache_stats['misses'] += 1
        logger.debug(f"Checking trading day from DB for {cache_key}")
        
        result = await self.db.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM trading_hours
                WHERE exchange = $1 
                AND trading_date = $2
                AND is_holiday = false
                AND is_active = true
            )
        """, exchange, check_date)
        
        # 캐시 저장
        self.trading_day_cache[cache_key] = result
        await self.redis.set(redis_key, result, expire=86400)
        
        return result
    
    async def is_market_open(self, exchange: str, check_time: datetime) -> bool:
        """현재 시장 개장 여부 확인 (캐시 적용)"""
        # 5분 단위로 반올림
        rounded_time = check_time.replace(second=0, microsecond=0)
        minute = rounded_time.minute
        rounded_time = rounded_time.replace(minute=minute - (minute % 5))
        
        cache_key = f"{exchange}:{rounded_time.isoformat()}"
        
        # 메모리 캐시 확인
        if cache_key in self.market_open_cache:
            self.cache_stats['hits'] += 1
            return self.market_open_cache[cache_key]
        
        # DB에서 확인
        self.cache_stats['misses'] += 1
        logger.debug(f"Checking market open status for {cache_key}")
        
        # 거래시간 조회
        trading_hours = await self.get_trading_hours(exchange, check_time.date())
        
        is_open = False
        for hours in trading_hours:
            if hours['is_holiday']:
                continue
                
            # 시간대 변환 필요 (구현 단순화를 위해 생략)
            open_time = hours['open_time']
            close_time = hours['close_time']
            
            # 현재 시간이 거래시간 내인지 확인
            current_time = check_time.time()
            if open_time <= current_time <= close_time:
                # 휴식시간 확인
                if hours['break_start'] and hours['break_end']:
                    if not (hours['break_start'] <= current_time <= hours['break_end']):
                        is_open = True
                        break
                else:
                    is_open = True
                    break
        
        # 캐시 저장
        self.market_open_cache[cache_key] = is_open
        
        return is_open
    
    async def invalidate_cache(self, exchange: str):
        """특정 거래소 캐시 무효화"""
        logger.info(f"Invalidating cache for exchange: {exchange}")
        
        # 메모리 캐시에서 제거
        keys_to_remove = []
        
        for key in self.trading_hours_cache.keys():
            if key.startswith(f"{exchange}:"):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.trading_hours_cache[key]
        
        keys_to_remove = []
        for key in self.trading_day_cache.keys():
            if key.startswith(f"{exchange}:"):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.trading_day_cache[key]
        
        keys_to_remove = []
        for key in self.market_open_cache.keys():
            if key.startswith(f"{exchange}:"):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.market_open_cache[key]
        
        # Redis 캐시에서 제거
        await self.redis.delete_pattern(f"trading_hours:{exchange}:*")
        await self.redis.delete_pattern(f"trading_day:{exchange}:*")
    
    async def clear_all_cache(self):
        """전체 캐시 초기화"""
        logger.info("Clearing all trading hours cache")
        
        # 메모리 캐시 초기화
        self.trading_hours_cache.clear()
        self.trading_day_cache.clear()
        self.market_open_cache.clear()
        
        # Redis 캐시 초기화
        await self.redis.delete_pattern("trading_hours:*")
        await self.redis.delete_pattern("trading_day:*")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': f"{hit_rate * 100:.2f}%",
            'trading_hours_size': len(self.trading_hours_cache),
            'trading_day_size': len(self.trading_day_cache),
            'market_open_size': len(self.market_open_cache)
        }
    
    async def warmup_cache(self):
        """캐시 예열 (주요 거래소의 향후 7일 데이터)"""
        logger.info("Warming up trading hours cache...")
        
        today = date.today()
        major_exchanges = ["CME", "EUREX", "HKFE", "JPX", "KSE", "SMART", "NYSE", "NASDAQ"]
        
        tasks = []
        for exchange in major_exchanges:
            for i in range(7):
                check_date = today + timedelta(days=i)
                tasks.append(self.get_trading_hours(exchange, check_date))
                tasks.append(self.is_trading_day(exchange, check_date))
        
        # 병렬 실행
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Cache warmup completed")
    
    async def cleanup_old_cache(self, days_to_keep: int = 90):
        """오래된 캐시 데이터 정리"""
        logger.info(f"Cleaning up cache data older than {days_to_keep} days")
        
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        # DB에서 오래된 데이터 삭제
        deleted = await self.db.execute("""
            DELETE FROM trading_hours
            WHERE trading_date < $1
        """, cutoff_date)
        
        logger.info(f"Deleted {deleted} old trading hour records")
        
        # Redis 캐시 정리는 TTL로 자동 처리됨


# 전역 캐시 서비스 인스턴스
cache_service_instance: Optional[TradingHourCacheService] = None


async def initialize_trading_hour_cache(
    db_manager: DatabaseManager,
    redis_manager: RedisManager
) -> TradingHourCacheService:
    """거래시간 캐시 서비스 초기화"""
    global cache_service_instance
    
    if cache_service_instance is None:
        cache_service_instance = TradingHourCacheService(db_manager, redis_manager)
        await cache_service_instance.warmup_cache()
    
    return cache_service_instance


async def get_trading_hour_cache() -> Optional[TradingHourCacheService]:
    """거래시간 캐시 서비스 인스턴스 반환"""
    return cache_service_instance