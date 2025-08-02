"""
시장 휴일 캘린더 서비스
- 시장별 휴일 관리
- 거래일 확인
- 휴일 인식 스케줄링
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, date, timedelta
from enum import Enum

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class Market(Enum):
    """시장 구분"""
    US = "US"           # 미국 시장
    KR = "KR"           # 한국 시장
    JP = "JP"           # 일본 시장
    HK = "HK"           # 홍콩 시장
    EU = "EU"           # 유럽 시장
    UK = "UK"           # 영국 시장
    GLOBAL = "GLOBAL"   # 전체


class HolidayCalendar:
    """시장 휴일 캘린더 클래스"""
    
    def __init__(self, db_manager: DatabaseManager, redis_manager: RedisManager):
        self.db = db_manager
        self.redis = redis_manager
        
        # 시장별 거래소 심볼 매핑
        self.exchange_symbols = {
            Market.US: ["SMART", "NYSE", "NASDAQ", "ARCA"],
            Market.KR: ["KRX", "KOSPI", "KOSDAQ"],
            Market.JP: ["TSE", "OSE"],
            Market.HK: ["HKEX"],
            Market.EU: ["EUREX", "LSE"],
            Market.UK: ["LSE"]
        }
        
        # 고정 휴일 정의 (월-일)
        self.fixed_holidays = {
            Market.US: [
                (1, 1),    # New Year's Day
                (7, 4),    # Independence Day
                (12, 25),  # Christmas
            ],
            Market.KR: [
                (1, 1),    # 신정
                (3, 1),    # 삼일절
                (5, 5),    # 어린이날
                (6, 6),    # 현충일
                (8, 15),   # 광복절
                (10, 3),   # 개천절
                (10, 9),   # 한글날
                (12, 25),  # 크리스마스
            ],
            Market.JP: [
                (1, 1),    # 元日
                (2, 11),   # 建国記念の日
                (2, 23),   # 天皇誕生日
                (4, 29),   # 昭和の日
                (5, 3),    # 憲法記念日
                (5, 4),    # みどりの日
                (5, 5),    # こどもの日
                (11, 3),   # 文化の日
                (11, 23),  # 勤労感謝の日
            ]
        }
        
        # 가변 휴일 (실제 구현시 외부 API 연동 필요)
        self.variable_holidays = {}
        
    async def is_trading_day(self, market: Market, check_date: date) -> bool:
        """거래일 여부 확인"""
        # 주말 확인
        if check_date.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 캐시 확인
        cache_key = f"holiday:{market.value}:{check_date.isoformat()}"
        cached = await self.redis.get(cache_key)
        if cached is not None:
            return not cached  # 휴일이면 거래일 아님
        
        # 휴일 확인
        is_holiday = await self._is_holiday(market, check_date)
        
        # 캐시 저장
        await self.redis.set(cache_key, is_holiday, expire=86400 * 30)  # 30일
        
        return not is_holiday
    
    async def get_next_trading_day(self, market: Market, from_date: date) -> date:
        """다음 거래일 조회"""
        next_date = from_date + timedelta(days=1)
        max_days = 10  # 최대 10일까지 확인
        
        for _ in range(max_days):
            if await self.is_trading_day(market, next_date):
                return next_date
            next_date += timedelta(days=1)
        
        # 10일 이내에 거래일이 없으면 예외
        raise ValueError(f"{from_date}로부터 {max_days}일 이내에 거래일이 없습니다")
    
    async def get_previous_trading_day(self, market: Market, from_date: date) -> date:
        """이전 거래일 조회"""
        prev_date = from_date - timedelta(days=1)
        max_days = 10
        
        for _ in range(max_days):
            if await self.is_trading_day(market, prev_date):
                return prev_date
            prev_date -= timedelta(days=1)
        
        raise ValueError(f"{from_date}로부터 {max_days}일 이전에 거래일이 없습니다")
    
    async def get_trading_days(
        self, 
        market: Market, 
        start_date: date, 
        end_date: date
    ) -> List[date]:
        """기간 내 거래일 목록 조회"""
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if await self.is_trading_day(market, current_date):
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        return trading_days
    
    async def get_holiday_info(self, check_date: date) -> Dict[str, Any]:
        """날짜의 휴일 정보 조회"""
        holiday_info = {
            'date': check_date.isoformat(),
            'is_weekend': check_date.weekday() >= 5,
            'markets_closed': [],
            'markets_open': [],
            'holiday_names': {}
        }
        
        for market in Market:
            if market == Market.GLOBAL:
                continue
                
            is_holiday = await self._is_holiday(market, check_date)
            
            if is_holiday:
                holiday_info['markets_closed'].append(market.value)
                
                # 휴일명 조회
                holiday_name = await self._get_holiday_name(market, check_date)
                if holiday_name:
                    holiday_info['holiday_names'][market.value] = holiday_name
            else:
                holiday_info['markets_open'].append(market.value)
        
        return holiday_info
    
    async def should_run_batch(self, market_type: str, check_date: date) -> bool:
        """배치 실행 여부 결정"""
        if market_type == "GLOBAL":
            # 전체 시장 기준 - 하나라도 열려있으면 실행
            for market in [Market.US, Market.KR, Market.JP, Market.HK, Market.EU]:
                if await self.is_trading_day(market, check_date):
                    return True
            return False
        else:
            # 특정 시장 기준
            try:
                market = Market(market_type)
                return await self.is_trading_day(market, check_date)
            except ValueError:
                logger.warning(f"알 수 없는 시장 타입: {market_type}")
                return True  # 기본적으로 실행
    
    async def update_holiday_calendar(self, year: int) -> Dict[str, Any]:
        """휴일 캘린더 업데이트"""
        logger.info(f"{year}년 휴일 캘린더 업데이트 시작")
        
        results = {
            'year': year,
            'markets_updated': [],
            'holidays_added': 0,
            'errors': []
        }
        
        for market in Market:
            if market == Market.GLOBAL:
                continue
                
            try:
                # 데이터베이스에서 기존 휴일 조회
                existing_holidays = await self._get_stored_holidays(market, year)
                
                # 고정 휴일 추가
                new_holidays = await self._add_fixed_holidays(market, year, existing_holidays)
                results['holidays_added'] += new_holidays
                
                # 가변 휴일 추가 (실제 구현시 외부 API 연동)
                # variable_holidays = await self._fetch_variable_holidays(market, year)
                
                results['markets_updated'].append(market.value)
                
            except Exception as e:
                logger.error(f"{market.value} 휴일 업데이트 실패: {e}")
                results['errors'].append({
                    'market': market.value,
                    'error': str(e)
                })
        
        # 캐시 초기화
        await self._clear_holiday_cache(year)
        
        logger.info(f"{year}년 휴일 캘린더 업데이트 완료")
        
        return results
    
    async def _is_holiday(self, market: Market, check_date: date) -> bool:
        """휴일 여부 확인 (내부)"""
        # 데이터베이스에서 확인
        result = await self.db.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM market_holidays
                WHERE market = $1 AND holiday_date = $2
            )
        """, market.value, check_date)
        
        if result:
            return True
        
        # 고정 휴일 확인
        if market in self.fixed_holidays:
            month_day = (check_date.month, check_date.day)
            if month_day in self.fixed_holidays[market]:
                return True
        
        return False
    
    async def _get_holiday_name(self, market: Market, check_date: date) -> Optional[str]:
        """휴일명 조회"""
        result = await self.db.fetchval("""
            SELECT holiday_name
            FROM market_holidays
            WHERE market = $1 AND holiday_date = $2
        """, market.value, check_date)
        
        return result
    
    async def _get_stored_holidays(self, market: Market, year: int) -> Set[date]:
        """저장된 휴일 조회"""
        rows = await self.db.fetch("""
            SELECT holiday_date
            FROM market_holidays
            WHERE market = $1 AND EXTRACT(YEAR FROM holiday_date) = $2
        """, market.value, year)
        
        return {row['holiday_date'] for row in rows}
    
    async def _add_fixed_holidays(
        self, 
        market: Market, 
        year: int, 
        existing_holidays: Set[date]
    ) -> int:
        """고정 휴일 추가"""
        added = 0
        
        if market not in self.fixed_holidays:
            return added
        
        for month, day in self.fixed_holidays[market]:
            try:
                holiday_date = date(year, month, day)
                
                # 이미 존재하는지 확인
                if holiday_date in existing_holidays:
                    continue
                
                # 휴일명 결정
                holiday_name = self._get_fixed_holiday_name(market, month, day)
                
                # 데이터베이스에 추가
                await self.db.execute("""
                    INSERT INTO market_holidays (market, holiday_date, holiday_name, is_fixed)
                    VALUES ($1, $2, $3, true)
                    ON CONFLICT (market, holiday_date) DO NOTHING
                """, market.value, holiday_date, holiday_name)
                
                added += 1
                
            except ValueError:
                # 유효하지 않은 날짜 (예: 2월 30일)
                pass
        
        return added
    
    def _get_fixed_holiday_name(self, market: Market, month: int, day: int) -> str:
        """고정 휴일명 반환"""
        holiday_names = {
            Market.US: {
                (1, 1): "New Year's Day",
                (7, 4): "Independence Day",
                (12, 25): "Christmas Day"
            },
            Market.KR: {
                (1, 1): "신정",
                (3, 1): "삼일절",
                (5, 5): "어린이날",
                (6, 6): "현충일",
                (8, 15): "광복절",
                (10, 3): "개천절",
                (10, 9): "한글날",
                (12, 25): "크리스마스"
            },
            Market.JP: {
                (1, 1): "元日",
                (2, 11): "建国記念の日",
                (2, 23): "天皇誕生日",
                (4, 29): "昭和の日",
                (5, 3): "憲法記念日",
                (5, 4): "みどりの日",
                (5, 5): "こどもの日",
                (11, 3): "文化の日",
                (11, 23): "勤労感謝の日"
            }
        }
        
        if market in holiday_names and (month, day) in holiday_names[market]:
            return holiday_names[market][(month, day)]
        
        return f"{market.value} Holiday"
    
    async def _clear_holiday_cache(self, year: int):
        """휴일 캐시 초기화"""
        # 해당 연도의 모든 캐시 삭제
        pattern = f"holiday:*:{year}-*"
        await self.redis.delete_pattern(pattern)
    
    def log_holiday_info(self, check_date: date):
        """휴일 정보 로깅"""
        asyncio.create_task(self._log_holiday_info_async(check_date))
    
    async def _log_holiday_info_async(self, check_date: date):
        """휴일 정보 비동기 로깅"""
        info = await self.get_holiday_info(check_date)
        
        if info['markets_closed']:
            logger.info(
                f"{check_date} 휴장 시장: {', '.join(info['markets_closed'])}"
            )
            
            for market, holiday_name in info['holiday_names'].items():
                logger.info(f"  - {market}: {holiday_name}")


# 전역 캘린더 인스턴스
calendar_instance: Optional[HolidayCalendar] = None


async def initialize_holiday_calendar(
    db_manager: DatabaseManager,
    redis_manager: RedisManager
) -> HolidayCalendar:
    """휴일 캘린더 초기화"""
    global calendar_instance
    
    if calendar_instance is None:
        calendar_instance = HolidayCalendar(db_manager, redis_manager)
        
        # 현재 연도와 다음 연도 휴일 업데이트
        current_year = datetime.now().year
        await calendar_instance.update_holiday_calendar(current_year)
        await calendar_instance.update_holiday_calendar(current_year + 1)
    
    return calendar_instance


async def get_holiday_calendar() -> Optional[HolidayCalendar]:
    """휴일 캘린더 인스턴스 반환"""
    return calendar_instance