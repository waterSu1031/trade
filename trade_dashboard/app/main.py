# Test comment for monorepo structure verification - dashboard project
import sys
sys.path.append('/home/freeksj/Workspace_Rule/trade')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import trades, positions, statistics, websocket, strategy, trading, dashboard, realtime
from app.config import settings
from app.database.database import engine, Base
from app.services.realtime_service import realtime_service
# Setup basic logging
import logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('trade_dashboard')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Trade Dashboard service started")
    try:
        await websocket.startup_event()
        logger.info("WebSocket service started successfully")
    except Exception as e:
        logger.error(f"WebSocket startup failed: {e}")
    yield
    # Shutdown
    logger.info("Trade Dashboard service stopped")
    await realtime_service.stop()

app = FastAPI(
    title="Trade Dashboard API",
    description="Trading dashboard backend for IBKR integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Svelte frontend development
        "http://localhost:4173",  # Svelte frontend preview
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["strategy"])
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(realtime.router, prefix="/api/realtime", tags=["realtime"])

@app.get("/")
async def root():
    return {"message": "Trade Dashboard API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trade_dashboard"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)