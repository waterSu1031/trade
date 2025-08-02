import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def cleanup_old_data(db_manager, redis_manager):
    """
    오래된 데이터 정리 작업
    Java의 taskletJob에 해당하는 정리 작업
    """
    logger.info("Starting cleanup job")
    
    try:
        # 1. 오래된 시계열 데이터 정리
        await cleanup_time_series_data(db_manager)
        
        # 2. 오래된 거래시간 캐시 정리
        await cleanup_trading_hours_cache(db_manager)
        
        # 3. Redis 캐시 정리
        await cleanup_redis_cache(redis_manager)
        
        # 4. 임시 데이터 정리
        await cleanup_temp_data(db_manager)
        
        logger.info("Cleanup job completed successfully")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Cleanup job failed: {e}")
        raise


async def cleanup_time_series_data(db_manager):
    """오래된 시계열 데이터 정리 (6개월 이상)"""
    cutoff_date = datetime.now() - timedelta(days=180)
    
    regions = ['us', 'eu', 'cn']
    total_deleted = 0
    
    for region in regions:
        table_name = f"price_time_{region}"
        
        # 파티션이 있는 경우 파티션 단위로 삭제하는 것이 효율적
        # 여기서는 간단한 DELETE 쿼리 사용
        query = f"""
            DELETE FROM {table_name}
            WHERE utc < $1
        """
        
        result = await db_manager.execute(query, cutoff_date)
        # DELETE 결과에서 삭제된 행 수 추출
        deleted_count = int(result.split()[-1]) if result else 0
        total_deleted += deleted_count
        
        logger.info(f"Deleted {deleted_count} old records from {table_name}")
    
    logger.info(f"Total time series records deleted: {total_deleted}")


async def cleanup_trading_hours_cache(db_manager):
    """오래된 거래시간 캐시 정리 (3개월 이상)"""
    cutoff_date = datetime.now().date() - timedelta(days=90)
    
    query = """
        DELETE FROM trading_hours
        WHERE type = '' AND trade_date < $1
    """
    
    result = await db_manager.execute(query, cutoff_date)
    deleted_count = int(result.split()[-1]) if result else 0
    
    logger.info(f"Deleted {deleted_count} old trading hour records")


async def cleanup_redis_cache(redis_manager):
    """Redis 캐시 정리"""
    try:
        # 만료된 키는 Redis가 자동으로 정리하므로
        # 여기서는 특정 패턴의 키들만 정리
        
        # 예: 7일 이상 된 임시 데이터 삭제
        # pattern = "temp:*"
        # keys = await redis_manager._client.keys(pattern)
        # if keys:
        #     await redis_manager._client.delete(*keys)
        #     logger.info(f"Deleted {len(keys)} temporary Redis keys")
        
        logger.info("Redis cache cleanup completed")
        
    except Exception as e:
        logger.error(f"Error cleaning up Redis cache: {e}")


async def cleanup_temp_data(db_manager):
    """임시 테이블 및 데이터 정리"""
    # 예: 임시 테이블이 있다면 정리
    # 현재는 특별한 임시 데이터가 없으므로 pass
    pass


async def run_tasklet_job(db_manager, ibkr_manager, redis_manager):
    """
    Tasklet 작업 실행
    Java의 taskletJob에 해당
    """
    logger.info("[Tasklet] IBKR Futures 작업 실행 중...")
    
    # 여러 정리 작업 실행
    await cleanup_old_data(db_manager, redis_manager)
    
    # 추가적인 tasklet 작업이 있다면 여기에 구현
    # 예: 통계 계산, 리포트 생성 등
    
    return {"status": "finished"}