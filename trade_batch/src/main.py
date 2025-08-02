import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from .config import settings
from .scheduler import scheduler_instance
from .api.batch_controller import router as batch_router

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작
    logger.info("Starting Trade Batch Service...")
    
    try:
        # 스케줄러 초기화
        await scheduler_instance.initialize()
        logger.info("Trade Batch Service started successfully")
        
        yield
        
    finally:
        # 종료
        logger.info("Shutting down Trade Batch Service...")
        await scheduler_instance.shutdown()
        logger.info("Trade Batch Service shut down")


# FastAPI 앱 생성
app = FastAPI(
    title="Trade Batch Service",
    description="Python-based batch processing service for trading system",
    version="1.0.0",
    lifespan=lifespan
)

# 라우터 등록
app.include_router(batch_router, prefix="/api/batch", tags=["batch"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Trade Batch",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    # 개발 모드 실행
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8082,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )