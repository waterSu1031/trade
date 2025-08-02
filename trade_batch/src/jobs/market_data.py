import logging
from typing import Dict, List, Any
import asyncio
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


async def collect_time_data(db_manager, ibkr_manager, redis_manager):
    """
    시계열 데이터 수집 작업
    Java의 collectTimeDataStep에 해당
    """
    logger.info("Starting collect time data job")
    
    try:
        # 1. 시계열 데이터 수집 대상 계약 로드
        contracts = await load_contracts_for_time_data(db_manager)
        logger.info(f"Loaded {len(contracts)} contracts for time data collection")
        
        # 2. 각 계약에 대해 시계열 데이터 수집
        processed_count = 0
        for contract in contracts:
            try:
                # IBKR에서 과거 데이터 수집
                time_data = await collect_historical_data(ibkr_manager, contract)
                
                if time_data:
                    # DB에 저장
                    await save_time_data(db_manager, contract, time_data)
                    logger.info(f"Saved {len(time_data)} bars for {contract['symbol']}")
                    processed_count += 1
                    
                    # Redis에 최신 데이터 캐시
                    await cache_latest_data(redis_manager, contract, time_data)
                    
                    # API 제한을 위한 대기
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"No time data found for {contract['symbol']}")
                    
            except Exception as e:
                logger.error(f"Error processing contract {contract['symbol']}: {e}")
                continue
        
        logger.info(f"Collect time data job completed. Processed: {processed_count}")
        return {"status": "success", "processed": processed_count}
        
    except Exception as e:
        logger.error(f"Collect time data job failed: {e}")
        raise


async def load_contracts_for_time_data(db_manager) -> List[Dict[str, Any]]:
    """시계열 데이터 수집 대상 계약 로드"""
    query = """
        SELECT 
            c.con_id,
            c.symbol,
            c.exchange,
            c.currency,
            c.sec_type,
            c.local_symbol,
            es.symbol as exchange_symbol
        FROM contracts c
        JOIN exchange_symbols es ON es.exchange = c.exchange
        WHERE c.con_id IS NOT NULL
        AND c.exchange IN ('CME', 'EUREX', 'HKFE', 'KSE', 'JPX', 'SGX')
        ORDER BY c.exchange, c.symbol
        LIMIT 50  -- 배치 크기 제한
    """
    
    return await db_manager.fetch_all(query)


async def collect_historical_data(ibkr_manager, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
    """IBKR에서 과거 데이터 수집"""
    try:
        # 1시간 봉 데이터를 1일치 수집
        bars = await ibkr_manager.get_historical_data(
            symbol=contract['symbol'],
            exchange=contract['exchange'],
            duration="1 D",
            bar_size="1 hour"
        )
        
        # 계약 정보 추가
        for bar in bars:
            bar['con_id'] = contract['con_id']
            bar['symbol'] = contract['symbol']
            bar['exchange'] = contract['exchange']
        
        return bars
        
    except Exception as e:
        logger.error(f"Error collecting historical data: {e}")
        return []


async def save_time_data(db_manager, contract: Dict[str, Any], time_data: List[Dict[str, Any]]):
    """시계열 데이터를 DB에 저장"""
    # 지역별 테이블 결정
    region_map = {
        'CME': 'us', 'CBOT': 'us', 'NYMEX': 'us', 'COMEX': 'us',
        'EUREX': 'eu', 'ICEEU': 'eu',
        'HKFE': 'cn', 'SGX': 'cn', 'JPX': 'cn', 'KSE': 'cn'
    }
    
    region = region_map.get(contract['exchange'], 'us')
    table_name = f"price_time_{region}"
    
    # 배치 삽입을 위한 데이터 준비
    insert_data = []
    for bar in time_data:
        # 시간 변환
        bar_datetime = datetime.fromisoformat(bar['date'].replace('Z', '+00:00'))
        
        insert_data.append((
            contract['con_id'],
            contract['symbol'],
            contract['exchange'],
            bar_datetime,  # UTC
            bar_datetime,  # LOC (나중에 timezone 변환 필요)
            bar['open'],
            bar['high'],
            bar['low'],
            bar['close'],
            bar['volume'],
            bar['barCount'],
            bar['average']
        ))
    
    # 배치 삽입
    query = f"""
        INSERT INTO {table_name} (
            con_id, symbol, exchange, utc, loc,
            open, high, low, close, volume, count, vwap
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (con_id, symbol, utc) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            count = EXCLUDED.count,
            vwap = EXCLUDED.vwap
    """
    
    await db_manager.execute_many(query, insert_data)


async def cache_latest_data(redis_manager, contract: Dict[str, Any], time_data: List[Dict[str, Any]]):
    """최신 데이터를 Redis에 캐시"""
    if not time_data:
        return
    
    # 가장 최근 데이터
    latest_bar = time_data[-1]
    
    # 캐시 키: market_data:{exchange}:{symbol}
    cache_key = f"market_data:{contract['exchange']}:{contract['symbol']}"
    
    # 1시간 동안 캐시
    await redis_manager.set(cache_key, latest_bar, expire=3600)
    
    # 심볼 리스트 업데이트
    await redis_manager.hset(
        "active_symbols",
        f"{contract['exchange']}:{contract['symbol']}",
        json.dumps({
            "con_id": contract['con_id'],
            "last_update": datetime.now().isoformat()
        })
    )