# Test comment for monorepo structure verification - dashboard project
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import trades, positions, statistics, websocket, strategy, trading, dashboard, realtime
from app.config import settings
from app.database.database import engine, Base
from app.services.realtime_service import realtime_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await websocket.startup_event()
    yield
    # Shutdown
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
        "http://127.0.0.1:4173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["strategy"])
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(realtime.router, prefix="/api/realtime", tags=["realtime"])

# Create database tables (only if they don't exist)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database tables initialization: {e}")

@app.get("/")
async def root():
    return {"message": "Trade Dashboard API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}