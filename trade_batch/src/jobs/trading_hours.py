import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta, date
import json

logger = logging.getLogger(__name__)


async def update_weekly_trading_hours(db_manager, ibkr_manager, redis_manager):
    """
    주간 거래시간 업데이트
    Java의 updateWeeklyTradingHours에 해당
    """
    logger.info("=== Weekly Trading Hours Update Started ===")
    
    try:
        # 거래소별 대표 심볼
        exchange_symbols = {
            "CME": "ES",      # E-mini S&P 500
            "EUREX": "FDAX",  # DAX Future
            "KSE": "101S6",   # KOSPI200
            "HKFE": "HSI",    # Hang Seng
            "SGX": "NK225M",  # Nikkei 225 Mini
            "JPX": "NK225",   # Nikkei 225
            "CBOT": "ZC",     # Corn
            "NYMEX": "CL",    # Crude Oil
            "COMEX": "GC",    # Gold
            "ICEEU": "BRN",   # Brent Oil
            "NSE": "NIFTY50", # Nifty 50
            "OSE": "NK225",   # Osaka Nikkei 225
        }
        
        today = date.today()
        end_date = today + timedelta(days=7)
        
        for exchange, symbol in exchange_symbols.items():
            try:
                logger.info(f"Updating trading hours for {exchange} ({symbol})")
                await update_trading_hours_for_exchange(
                    db_manager, ibkr_manager, exchange, symbol, today, end_date
                )
                
                # API 제한을 위한 대기
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to update trading hours for {exchange}: {e}")
        
        # 오래된 캐시 정리 (3개월 이상)
        await cleanup_old_cache(db_manager)
        
        logger.info("=== Weekly Trading Hours Update Completed Successfully ===")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Failed to update weekly trading hours: {e}")
        raise


async def update_trading_hours_for_exchange(db_manager, ibkr_manager, exchange: str, 
                                          symbol: str, start_date: date, end_date: date):
    """특정 거래소의 거래시간 업데이트"""
    try:
        # IBKR에서 계약 상세 정보 조회
        details_list = await ibkr_manager.get_contract_details(
            symbol=symbol,
            exchange=exchange,
            sec_type="FUT"
        )
        
        if not details_list:
            logger.warning(f"No contract details found for {exchange}:{symbol}")
            return
        
        details = details_list[0]
        trading_hours_str = details.get('tradingHours', '')
        
        if trading_hours_str:
            # 거래시간 파싱 및 저장
            await parse_trading_hours(db_manager, exchange, trading_hours_str)
        else:
            logger.warning(f"No trading hours data received for {exchange}")
            
    except Exception as e:
        logger.error(f"Error updating trading hours for {exchange}: {e}")


async def parse_trading_hours(db_manager, exchange: str, trading_hours_str: str):
    """
    IBKR 거래시간 문자열 파싱
    형식: "20251103:1700-20251104:1600;20251104:1700-20251105:1600"
    """
    # 거래소별 시간대
    timezones = {
        "CME": "America/Chicago",
        "CBOT": "America/Chicago",
        "NYMEX": "America/New_York",
        "COMEX": "America/New_York",
        "EUREX": "Europe/Berlin",
        "ICEEU": "Europe/London",
        "KSE": "Asia/Seoul",
        "JPX": "Asia/Tokyo",
        "OSE": "Asia/Tokyo",
        "SGX": "Asia/Singapore",
        "HKFE": "Asia/Hong_Kong",
        "NSE": "Asia/Kolkata"
    }
    
    timezone = timezones.get(exchange, "UTC")
    sessions = trading_hours_str.split(";")
    
    # 점심시간이 있는 거래소 확인
    has_lunch_break = await check_lunch_break(db_manager, exchange)
    
    for i, session_data in enumerate(sessions):
        try:
            # CLOSED 체크
            if "CLOSED" in session_data:
                date_str = session_data.split(":")[0]
                trade_date = datetime.strptime(date_str, "%Y%m%d").date()
                day_of_week = trade_date.strftime("%a").upper()[:3]
                
                await save_holiday(db_manager, exchange, trade_date, day_of_week, 
                                 timezone, session_data)
                continue
            
            # 시간 파싱
            parts = session_data.split("-")
            if len(parts) != 2:
                continue
            
            start_str, end_str = parts
            
            # 시작 시간
            start_parts = start_str.split(":")
            start_date = datetime.strptime(start_parts[0], "%Y%m%d").date()
            start_time = datetime.strptime(start_parts[1], "%H%M").time()
            
            # 종료 시간
            end_parts = end_str.split(":")
            end_date = datetime.strptime(end_parts[0], "%Y%m%d").date()
            end_time = datetime.strptime(end_parts[1], "%H%M").time()
            
            # 현지 시간
            start_loc = datetime.combine(start_date, start_time)
            end_loc = datetime.combine(end_date, end_time)
            
            # UTC 변환 (간단한 변환, 실제로는 pytz 사용 권장)
            # TODO: pytz를 사용한 정확한 시간대 변환 구현
            start_utc = start_loc  # 임시
            end_utc = end_loc      # 임시
            
            # 요일
            day_of_week = start_date.strftime("%a").upper()[:3]
            
            # 세션 구분
            session_type = determine_session(exchange, sessions, i, has_lunch_break)
            
            # 저장
            await save_trading_hours(
                db_manager, exchange, "", session_type, start_date, day_of_week,
                start_utc, end_utc, start_loc, end_loc,
                timezone, False, session_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing session data '{session_data}' for {exchange}: {e}")


async def check_lunch_break(db_manager, exchange: str) -> bool:
    """특정 거래소가 점심시간이 있는지 확인"""
    query = """
        SELECT COUNT(*) FROM trading_hours
        WHERE exchange = $1 AND type = 'FIX' AND session IN ('MORNING', 'AFTERNOON')
    """
    
    count = await db_manager.fetch_value(query, exchange)
    return count > 0 if count else False


def determine_session(exchange: str, all_sessions: List[str], current_index: int, 
                     has_lunch_break: bool) -> str:
    """세션 타입 결정"""
    if not has_lunch_break or len(all_sessions) == 1:
        return "REGULAR"
    
    # 점심시간이 있는 거래소의 경우
    if current_index == 0:
        return "MORNING"
    elif current_index == 1:
        return "AFTERNOON"
    else:
        return "REGULAR"


async def save_trading_hours(db_manager, exchange: str, type_: str, session: str,
                           trade_date: date, day_of_week: str,
                           start_utc: datetime, end_utc: datetime,
                           start_loc: datetime, end_loc: datetime,
                           timezone: str, is_holiday: bool, raw_data: str):
    """거래시간 저장"""
    query = """
        INSERT INTO trading_hours (
            exchange, type, session, trade_date, day_of_week,
            start_time_utc, end_time_utc, start_time_loc, end_time_loc,
            timezone, is_holiday, raw_data
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
        )
        ON CONFLICT (exchange, type, session, trade_date) 
        DO UPDATE SET
            day_of_week = EXCLUDED.day_of_week,
            start_time_utc = EXCLUDED.start_time_utc,
            end_time_utc = EXCLUDED.end_time_utc,
            start_time_loc = EXCLUDED.start_time_loc,
            end_time_loc = EXCLUDED.end_time_loc,
            is_holiday = EXCLUDED.is_holiday,
            raw_data = EXCLUDED.raw_data,
            created_at = CURRENT_TIMESTAMP
    """
    
    await db_manager.execute(
        query,
        exchange, type_, session, trade_date, day_of_week,
        start_utc, end_utc, start_loc, end_loc,
        timezone, is_holiday, raw_data
    )


async def save_holiday(db_manager, exchange: str, trade_date: date, 
                      day_of_week: str, timezone: str, raw_data: str):
    """휴일 정보 저장"""
    query = """
        INSERT INTO trading_hours (
            exchange, type, session, trade_date, day_of_week,
            timezone, is_holiday, raw_data
        ) VALUES (
            $1, '', 'CLOSED', $2, $3, $4, true, $5
        )
        ON CONFLICT (exchange, type, session, trade_date) 
        DO UPDATE SET
            day_of_week = EXCLUDED.day_of_week,
            is_holiday = EXCLUDED.is_holiday,
            raw_data = EXCLUDED.raw_data,
            created_at = CURRENT_TIMESTAMP
    """
    
    await db_manager.execute(query, exchange, trade_date, day_of_week, timezone, raw_data)


async def cleanup_old_cache(db_manager):
    """오래된 데이터 정리 (3개월 이상)"""
    cutoff_date = date.today() - timedelta(days=90)
    
    query = """
        DELETE FROM trading_hours
        WHERE type = '' AND trade_date < $1
    """
    
    deleted = await db_manager.execute(query, cutoff_date)
    logger.info(f"Deleted old trading hour records before {cutoff_date}")