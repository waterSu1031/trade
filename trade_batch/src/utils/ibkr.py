from ib_insync import IB, Contract, Stock, Future, Option, Forex, Index
from typing import Dict, List, Any, Optional
import logging
from .converters import ibkr_to_dict
import asyncio

logger = logging.getLogger(__name__)


class IBKRManager:
    """IBKR 연결 관리자 - Dict 기반"""
    
    def __init__(self):
        self.ib = IB()
        self._connected = False
    
    async def connect(self, host: str, port: int, client_id: int):
        """IBKR 게이트웨이 연결"""
        if self._connected:
            return
            
        try:
            await self.ib.connectAsync(host, port, clientId=client_id)
            self._connected = True
            logger.info(f"Connected to IBKR at {host}:{port} with client_id={client_id}")
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            raise
    
    async def disconnect(self):
        """연결 해제"""
        if self._connected:
            self.ib.disconnect()
            self._connected = False
            logger.info("Disconnected from IBKR")
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._connected
    
    async def get_contract_details(self, symbol: str, exchange: str, sec_type: str = "STK") -> List[Dict[str, Any]]:
        """계약 상세 정보를 Dict로 반환"""
        # Contract 객체 생성
        if sec_type == "STK":
            contract = Stock(symbol, exchange, 'USD')
        elif sec_type == "FUT":
            contract = Future(symbol, exchange=exchange)
        elif sec_type == "OPT":
            contract = Option(symbol, exchange=exchange)
        elif sec_type == "CASH":
            contract = Forex(symbol)
        elif sec_type == "IND":
            contract = Index(symbol, exchange)
        else:
            contract = Contract()
            contract.symbol = symbol
            contract.exchange = exchange
            contract.secType = sec_type
        
        # 상세 정보 요청
        details_list = await self.ib.reqContractDetailsAsync(contract)
        
        # Dict로 변환하여 반환
        return [ibkr_to_dict(details) for details in details_list]
    
    async def get_historical_data(self, symbol: str, exchange: str, duration: str = "1 D", 
                                 bar_size: str = "1 hour") -> List[Dict[str, Any]]:
        """과거 데이터를 Dict로 반환"""
        contract = Stock(symbol, exchange, 'USD')
        
        bars = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow='TRADES',
            useRTH=True
        )
        
        # BarData를 Dict로 변환
        result = []
        for bar in bars:
            result.append({
                'date': str(bar.date),
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': int(bar.volume),
                'average': float(bar.average),
                'barCount': int(bar.barCount)
            })
        
        return result
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """포지션을 Dict로 반환"""
        positions = await self.ib.reqPositionsAsync()
        
        result = []
        for pos in positions:
            result.append({
                'account': pos.account,
                'contract': ibkr_to_dict(pos.contract),
                'position': float(pos.position),
                'avgCost': float(pos.avgCost),
                'marketPrice': float(pos.marketPrice) if pos.marketPrice else 0,
                'marketValue': float(pos.marketValue) if pos.marketValue else 0,
                'unrealizedPNL': float(pos.unrealizedPNL) if pos.unrealizedPNL else 0,
                'realizedPNL': float(pos.realizedPNL) if pos.realizedPNL else 0
            })
        
        return result
    
    async def place_order(self, contract_dict: Dict[str, Any], order_dict: Dict[str, Any]) -> Dict[str, Any]:
        """주문 실행 - Dict 입력, Dict 출력"""
        # Dict를 Contract 객체로 변환
        contract = Contract()
        for key, value in contract_dict.items():
            setattr(contract, key, value)
        
        # Dict를 Order 객체로 변환
        from ib_insync import Order
        order = Order()
        for key, value in order_dict.items():
            setattr(order, key, value)
        
        # 주문 실행
        trade = self.ib.placeOrder(contract, order)
        
        # 주문 완료 대기
        await asyncio.sleep(1)
        
        # Trade 객체를 Dict로 변환
        return ibkr_to_dict(trade)