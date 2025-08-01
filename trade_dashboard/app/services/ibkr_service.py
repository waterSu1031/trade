from ib_insync import IB, Stock, Contract, Trade, Position
from typing import List, Optional
import asyncio
import logging
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('trade_dashboard.ibkr_service')

class IBKRService:
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.host = settings.ib_host
        self.port = settings.ib_port
        self.client_id = settings.ib_client_id
        
    async def connect(self) -> bool:
        """Connect to IBKR Gateway or TWS"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                await self.ib.connectAsync(
                    host=self.host,
                    port=self.port,
                    clientId=self.client_id
                )
                self.connected = True
                logger.info(f"Connected to IBKR at {self.host}:{self.port}")
                return True
            except Exception as e:
                self.connected = False
                logger.error(f"IBKR connection attempt {attempt + 1}/{max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2.0)
                else:
                    logger.error("Max connection attempts reached")
                    return False
        return False
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    async def reconnect(self) -> bool:
        """Reconnect to IBKR"""
        await self.disconnect()
        await asyncio.sleep(1)
        return await self.connect()
    
    def is_connected(self) -> bool:
        """Check if connected to IBKR"""
        return self.connected and self.ib.isConnected()
    
    async def get_account_summary(self) -> dict:
        """Get account summary information"""
        if not self.is_connected():
            await self.connect()
        
        try:
            account_values = self.ib.accountSummary()
            summary = {}
            for av in account_values:
                summary[av.tag] = {
                    'value': av.value,
                    'currency': av.currency
                }
            return summary
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        if not self.is_connected():
            await self.connect()
        
        try:
            positions = self.ib.positions()
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_trades(self) -> List[Trade]:
        """Get current trades"""
        if not self.is_connected():
            await self.connect()
        
        try:
            trades = self.ib.trades()
            return trades
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return []
    
    async def get_portfolio(self) -> List:
        """Get portfolio items"""
        if not self.is_connected():
            await self.connect()
        
        try:
            portfolio = self.ib.portfolio()
            return portfolio
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return []
    
    async def place_order(self, contract: Contract, order) -> Trade:
        """Place an order"""
        if not self.is_connected():
            await self.connect()
        
        try:
            trade = self.ib.placeOrder(contract, order)
            return trade
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def get_market_data(self, contract: Contract) -> dict:
        """Get real-time market data for a contract"""
        if not self.is_connected():
            await self.connect()
        
        try:
            ticker = self.ib.reqMktData(contract)
            await self.ib.sleep(1)  # Wait for data
            
            return {
                'symbol': contract.symbol,
                'bid': ticker.bid,
                'ask': ticker.ask,
                'last': ticker.last,
                'volume': ticker.volume,
                'high': ticker.high,
                'low': ticker.low,
                'close': ticker.close
            }
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}

# Global instance
ibkr_service = IBKRService()