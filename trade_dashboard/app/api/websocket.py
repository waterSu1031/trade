from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import asyncio
import json
import logging
from app.services.ibkr_service import ibkr_service
from app.services.realtime_service import realtime_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all subscriptions
        for topic, connections in self.subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_to_topic(self, topic: str, message: str):
        if topic not in self.subscriptions:
            return
        
        disconnected = []
        for connection in self.subscriptions[topic]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to topic {topic}: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.subscriptions[topic]:
                self.subscriptions[topic].remove(conn)

    def subscribe(self, websocket: WebSocket, topic: str):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        
        if websocket not in self.subscriptions[topic]:
            self.subscriptions[topic].append(websocket)
            logger.info(f"WebSocket subscribed to {topic}")

    def unsubscribe(self, websocket: WebSocket, topic: str):
        if topic in self.subscriptions and websocket in self.subscriptions[topic]:
            self.subscriptions[topic].remove(websocket)
            logger.info(f"WebSocket unsubscribed from {topic}")

manager = ConnectionManager()

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    topic = message.get("topic")
                    if topic:
                        manager.subscribe(websocket, topic)
                        await manager.send_personal_message(
                            json.dumps({"type": "subscription_confirmed", "topic": topic}),
                            websocket
                        )
                
                elif message_type == "unsubscribe":
                    topic = message.get("topic")
                    if topic:
                        manager.unsubscribe(websocket, topic)
                        await manager.send_personal_message(
                            json.dumps({"type": "unsubscription_confirmed", "topic": topic}),
                            websocket
                        )
                
                elif message_type == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": message.get("timestamp")}),
                        websocket
                    )
                
                else:
                    await manager.send_personal_message(
                        json.dumps({"type": "error", "message": "Unknown message type"}),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON"}),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def start_market_data_stream():
    """Start streaming market data to subscribed clients"""
    while True:
        try:
            if ibkr_service.is_connected():
                # Get account summary
                account_data = await ibkr_service.get_account_summary()
                if account_data:
                    await manager.broadcast_to_topic(
                        "account_updates",
                        json.dumps({
                            "type": "account_update",
                            "data": account_data,
                            "timestamp": asyncio.get_event_loop().time()
                        })
                    )
                
                # Get current positions
                positions = await ibkr_service.get_positions()
                if positions:
                    position_data = [
                        {
                            "symbol": pos.contract.symbol,
                            "position": pos.position,
                            "avgCost": pos.avgCost,
                            "marketPrice": pos.marketPrice,
                            "marketValue": pos.marketValue,
                            "unrealizedPNL": pos.unrealizedPNL,
                            "realizedPNL": pos.realizedPNL,
                        }
                        for pos in positions
                        if pos.position != 0
                    ]
                    
                    await manager.broadcast_to_topic(
                        "position_updates",
                        json.dumps({
                            "type": "position_update",
                            "data": position_data,
                            "timestamp": asyncio.get_event_loop().time()
                        })
                    )
                
                # Get recent trades
                trades = await ibkr_service.get_trades()
                if trades:
                    trade_data = [
                        {
                            "orderId": trade.order.orderId,
                            "symbol": trade.contract.symbol,
                            "action": trade.order.action,
                            "quantity": trade.order.totalQuantity,
                            "status": trade.orderStatus.status,
                            "filled": trade.orderStatus.filled,
                            "avgFillPrice": trade.orderStatus.avgFillPrice,
                            "commission": getattr(trade.orderStatus, 'commission', 0.0)
                        }
                        for trade in trades[-10:]  # Last 10 trades
                    ]
                    
                    await manager.broadcast_to_topic(
                        "trade_updates",
                        json.dumps({
                            "type": "trade_update",
                            "data": trade_data,
                            "timestamp": asyncio.get_event_loop().time()
                        })
                    )
            
        except Exception as e:
            logger.error(f"Error in market data stream: {e}")
        
        await asyncio.sleep(5)  # Update every 5 seconds

# Start the background task when the module is imported
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(start_market_data_stream())
    
    # Start realtime service
    await realtime_service.start()
    
    # Register callbacks for real-time data
    async def handle_price_update(data):
        await manager.broadcast_to_topic("price_updates", json.dumps(data))
    
    async def handle_position_update(data):
        await manager.broadcast_to_topic("position_updates", json.dumps(data))
    
    async def handle_alert(data):
        await manager.broadcast_to_topic("alerts", json.dumps(data))
    
    realtime_service.subscribe_prices(handle_price_update)
    realtime_service.subscribe_positions(handle_position_update)
    realtime_service.subscribe_alerts(handle_alert)

@router.get("/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": len(manager.active_connections),
        "subscriptions": {
            topic: len(connections) 
            for topic, connections in manager.subscriptions.items()
        },
        "ibkr_connected": ibkr_service.is_connected()
    }