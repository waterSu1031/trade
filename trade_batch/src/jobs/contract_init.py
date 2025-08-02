import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


async def init_contract_data(db_manager, ibkr_manager, redis_manager):
    """
    계약 구조 초기화 작업
    Java의 setInitStructureJob에 해당
    """
    logger.info("Starting contract initialization job")
    
    try:
        # 1. CSV에서 심볼 로드
        symbols = await load_symbols_from_csv(db_manager)
        logger.info(f"Loaded {len(symbols)} symbols from CSV")
        
        # 2. 각 심볼에 대해 계약 상세 정보 수집
        for symbol in symbols:
            try:
                # IBKR에서 계약 상세 정보 가져오기
                contract_details = await fetch_contract_details(ibkr_manager, symbol)
                
                if contract_details:
                    # DB에 저장
                    await save_contract_details(db_manager, contract_details)
                    logger.info(f"Saved contract details for {symbol['symbol']}")
                    
                    # API 제한을 위한 대기
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"No contract details found for {symbol['symbol']}")
                    
            except Exception as e:
                logger.error(f"Error processing symbol {symbol['symbol']}: {e}")
                continue
        
        logger.info("Contract initialization job completed")
        return {"status": "success", "processed": len(symbols)}
        
    except Exception as e:
        logger.error(f"Contract initialization job failed: {e}")
        raise


async def load_symbols_from_csv(db_manager) -> List[Dict[str, Any]]:
    """CSV 파일에서 심볼 로드 (DB의 symbol_imports 테이블)"""
    query = """
        SELECT symbol, exchange, currency, sec_type 
        FROM symbol_imports 
        WHERE symbol IS NOT NULL
        ORDER BY symbol
    """
    
    return await db_manager.fetch_all(query)


async def fetch_contract_details(ibkr_manager, symbol_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """IBKR에서 계약 상세 정보 가져오기"""
    try:
        details_list = await ibkr_manager.get_contract_details(
            symbol=symbol_data['symbol'],
            exchange=symbol_data['exchange'],
            sec_type=symbol_data.get('sec_type', 'STK')
        )
        
        if details_list:
            # 첫 번째 계약 상세 정보 반환
            contract_detail = details_list[0]
            
            # symbol_data 정보 추가
            contract_detail['symbol'] = symbol_data['symbol']
            contract_detail['exchange'] = symbol_data['exchange']
            contract_detail['currency'] = symbol_data['currency']
            
            return contract_detail
            
    except Exception as e:
        logger.error(f"Error fetching contract details: {e}")
        return None


async def save_contract_details(db_manager, contract_details: Dict[str, Any]):
    """계약 상세 정보를 DB에 저장"""
    # contracts 테이블에 저장
    contract_query = """
        INSERT INTO contracts (
            con_id, symbol, sec_type, exchange, currency,
            primary_exch, local_symbol, trading_class,
            last_trade_date_or_contract_month, multiplier,
            strike, right_, description
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
        )
        ON CONFLICT (con_id) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            sec_type = EXCLUDED.sec_type,
            exchange = EXCLUDED.exchange,
            currency = EXCLUDED.currency,
            primary_exch = EXCLUDED.primary_exch,
            local_symbol = EXCLUDED.local_symbol,
            trading_class = EXCLUDED.trading_class,
            last_trade_date_or_contract_month = EXCLUDED.last_trade_date_or_contract_month,
            multiplier = EXCLUDED.multiplier,
            strike = EXCLUDED.strike,
            right_ = EXCLUDED.right_,
            description = EXCLUDED.description
    """
    
    contract = contract_details.get('contract', {})
    
    await db_manager.execute(
        contract_query,
        contract.get('conId', 0),
        contract.get('symbol'),
        contract.get('secType'),
        contract.get('exchange'),
        contract.get('currency'),
        contract.get('primaryExch'),
        contract.get('localSymbol'),
        contract.get('tradingClass'),
        contract.get('lastTradeDateOrContractMonth'),
        contract.get('multiplier'),
        contract.get('strike'),
        contract.get('right'),
        contract.get('description')
    )
    
    # contract_details 테이블에 저장
    if contract.get('conId'):
        details_query = """
            INSERT INTO contract_details (
                con_id, market_name, min_tick, price_magnifier,
                order_types, valid_exchanges, long_name,
                time_zone_id, trading_hours, liquid_hours,
                agg_group, market_rule_ids
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            )
            ON CONFLICT (con_id) DO UPDATE SET
                market_name = EXCLUDED.market_name,
                min_tick = EXCLUDED.min_tick,
                price_magnifier = EXCLUDED.price_magnifier,
                order_types = EXCLUDED.order_types,
                valid_exchanges = EXCLUDED.valid_exchanges,
                long_name = EXCLUDED.long_name,
                time_zone_id = EXCLUDED.time_zone_id,
                trading_hours = EXCLUDED.trading_hours,
                liquid_hours = EXCLUDED.liquid_hours,
                agg_group = EXCLUDED.agg_group,
                market_rule_ids = EXCLUDED.market_rule_ids
        """
        
        await db_manager.execute(
            details_query,
            contract.get('conId'),
            contract_details.get('marketName'),
            contract_details.get('minTick'),
            contract_details.get('priceMagnifier'),
            contract_details.get('orderTypes'),
            contract_details.get('validExchanges'),
            contract_details.get('longName'),
            contract_details.get('timeZoneId'),
            contract_details.get('tradingHours'),
            contract_details.get('liquidHours'),
            contract_details.get('aggGroup'),
            contract_details.get('marketRuleIds')
        )