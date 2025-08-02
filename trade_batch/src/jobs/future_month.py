import logging
from typing import Dict, List, Any
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def add_future_months(db_manager, ibkr_manager, redis_manager):
    """
    선물 월물 추가 작업
    Java의 addFutureMonthJob에 해당
    """
    logger.info("Starting add future months job")
    
    try:
        # 1. 대상 선물 계약 로드
        target_contracts = await load_target_future_contracts(db_manager)
        logger.info(f"Loaded {len(target_contracts)} future contracts")
        
        # 2. 각 계약에 대해 월물 정보 수집
        processed_count = 0
        for contract in target_contracts:
            try:
                # IBKR에서 선물 월물 정보 수집
                future_months = await collect_future_months(ibkr_manager, contract)
                
                if future_months:
                    # DB에 저장
                    await save_future_months(db_manager, contract, future_months)
                    logger.info(f"Saved {len(future_months)} months for {contract['symbol']}")
                    processed_count += 1
                    
                    # API 제한을 위한 대기
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"No future months found for {contract['symbol']}")
                    
            except Exception as e:
                logger.error(f"Error processing contract {contract['symbol']}: {e}")
                continue
        
        logger.info(f"Add future months job completed. Processed: {processed_count}")
        return {"status": "success", "processed": processed_count}
        
    except Exception as e:
        logger.error(f"Add future months job failed: {e}")
        raise


async def load_target_future_contracts(db_manager) -> List[Dict[str, Any]]:
    """선물 월물 수집 대상 계약 로드"""
    query = """
        SELECT DISTINCT 
            c.con_id,
            c.symbol,
            c.exchange,
            c.currency,
            c.sec_type,
            c.trading_class
        FROM contracts c
        WHERE c.sec_type = 'FUT'
        AND c.symbol NOT LIKE '%!%'  -- 연속 계약 제외
        ORDER BY c.symbol
    """
    
    return await db_manager.fetch_all(query)


async def collect_future_months(ibkr_manager, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
    """IBKR에서 선물 월물 정보 수집"""
    try:
        # 연속 계약으로 모든 월물 조회
        continuous_symbol = f"{contract['symbol']}!"  # 연속 계약 심볼
        
        # 계약 상세 정보 요청
        details_list = await ibkr_manager.get_contract_details(
            symbol=continuous_symbol,
            exchange=contract['exchange'],
            sec_type='FUT'
        )
        
        future_months = []
        for details in details_list:
            contract_info = details.get('contract', {})
            
            # 월물 정보 추출
            month_data = {
                'con_id': contract_info.get('conId'),
                'symbol': contract_info.get('symbol'),
                'local_symbol': contract_info.get('localSymbol'),
                'last_trade_date': contract_info.get('lastTradeDateOrContractMonth'),
                'exchange': contract_info.get('exchange'),
                'currency': contract_info.get('currency'),
                'multiplier': contract_info.get('multiplier'),
                'trading_class': contract_info.get('tradingClass'),
                'market_name': details.get('marketName'),
                'long_name': details.get('longName'),
                'min_tick': details.get('minTick'),
                'underlying_con_id': details.get('underConId')
            }
            
            future_months.append(month_data)
        
        return future_months
        
    except Exception as e:
        logger.error(f"Error collecting future months: {e}")
        return []


async def save_future_months(db_manager, base_contract: Dict[str, Any], 
                           future_months: List[Dict[str, Any]]):
    """선물 월물 정보를 DB에 저장"""
    for month in future_months:
        # contracts 테이블에 월물 저장
        contract_query = """
            INSERT INTO contracts (
                con_id, symbol, sec_type, exchange, currency,
                local_symbol, trading_class, 
                last_trade_date_or_contract_month, multiplier,
                crt_month_con_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
            )
            ON CONFLICT (con_id) DO UPDATE SET
                symbol = EXCLUDED.symbol,
                local_symbol = EXCLUDED.local_symbol,
                last_trade_date_or_contract_month = EXCLUDED.last_trade_date_or_contract_month,
                multiplier = EXCLUDED.multiplier,
                crt_month_con_id = EXCLUDED.crt_month_con_id
        """
        
        await db_manager.execute(
            contract_query,
            month['con_id'],
            month['symbol'],
            'FUT',
            month['exchange'],
            month['currency'],
            month['local_symbol'],
            month['trading_class'],
            month['last_trade_date'],
            month['multiplier'],
            base_contract['con_id']  # 기본 계약 ID 참조
        )
        
        # contract_details_future 테이블에 추가 정보 저장
        if month.get('con_id'):
            details_query = """
                INSERT INTO contract_details_future (
                    con_id, contract_month, real_expiration_date,
                    under_conid, under_symbol, under_sec_type
                ) VALUES (
                    $1, $2, $3, $4, $5, $6
                )
                ON CONFLICT (con_id) DO UPDATE SET
                    contract_month = EXCLUDED.contract_month,
                    real_expiration_date = EXCLUDED.real_expiration_date,
                    under_conid = EXCLUDED.under_conid
            """
            
            # 월물 추출 (예: 202503)
            contract_month = month.get('last_trade_date', '')[:6] if month.get('last_trade_date') else ''
            
            await db_manager.execute(
                details_query,
                month['con_id'],
                contract_month,
                month['last_trade_date'],
                month.get('underlying_con_id'),
                base_contract['symbol'],
                'FUT'
            )