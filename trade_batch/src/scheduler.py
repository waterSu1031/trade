import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date
from typing import Dict, Any, List

from tradelib import DatabaseManager, IBKRManager, RedisManager
from .config import settings

# Jobs import
from .jobs.contract_init import init_contract_data
from .jobs.future_month import add_future_months
from .jobs.market_data import collect_time_data
from .jobs.trading_hours import update_weekly_trading_hours
from .jobs.cleanup import run_tasklet_job
from .jobs.data_integrity import run_data_integrity_check
from .jobs.partition_management import manage_partitions
from .jobs.daily_statistics import calculate_daily_statistics
from .jobs.compression_policy import manage_compression_policy
from .jobs.data_sync import sync_data_to_analytics

# Services import
from .services.connection_monitor import initialize_connection_monitor
from .services.holiday_calendar import initialize_holiday_calendar, Market
from .services.trading_hour_cache import initialize_trading_hour_cache
from .services.market_aware_connection_monitor import initialize_market_aware_monitor
from .services.redis_consumer import initialize_redis_consumer
from .services.backup_restore import initialize_backup_service
from .services.configuration_manager import initialize_configuration_manager
from .services.execution_statistics import initialize_execution_statistics

logger = logging.getLogger(__name__)


class BatchScheduler:
    """배치 작업 스케줄러"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_manager = DatabaseManager(settings.database_url)
        self.ibkr_manager = IBKRManager()
        self.redis_manager = RedisManager(settings.redis_url)
        self.holiday_calendar = None
        self.connection_monitor = None
        self.trading_hour_cache = None
        self.market_aware_monitor = None
        self.redis_consumer = None
        self.backup_service = None
        self.config_manager = None
        self.execution_stats = None
        
    async def initialize(self):
        """스케줄러 초기화"""
        # 연결 초기화
        await self.db_manager.connect()
        
        # IBKR 연결 (실패해도 계속 진행)
        try:
            await self.ibkr_manager.connect(
                settings.ibkr_host, 
                settings.ibkr_port, 
                settings.ibkr_client_id
            )
            logger.info("IBKR connection established")
        except Exception as e:
            logger.warning(f"IBKR connection failed: {e}. Continuing without IBKR.")
        
        await self.redis_manager.connect()
        
        # 서비스 초기화
        self.holiday_calendar = await initialize_holiday_calendar(
            self.db_manager, self.redis_manager
        )
        self.connection_monitor = await initialize_connection_monitor(
            self.ibkr_manager, self.redis_manager
        )
        self.trading_hour_cache = await initialize_trading_hour_cache(
            self.db_manager, self.redis_manager
        )
        self.market_aware_monitor = await initialize_market_aware_monitor(
            self.ibkr_manager, self.redis_manager, self.trading_hour_cache
        )
        self.redis_consumer = await initialize_redis_consumer(
            self.redis_manager, self.db_manager
        )
        self.backup_service = await initialize_backup_service(
            self.db_manager, self.redis_manager
        )
        self.config_manager = await initialize_configuration_manager(
            self.db_manager, self.redis_manager
        )
        self.execution_stats = await initialize_execution_statistics(
            self.db_manager, self.redis_manager
        )
        
        # 스케줄 설정
        self.setup_schedules()
        
        # 스케줄러 시작
        self.scheduler.start()
        logger.info("Batch scheduler initialized and started")
    
    def setup_schedules(self):
        """스케줄 설정"""
        # === 기존 스케줄 ===
        
        # 매일 7시 - 계약 구조 초기화 (휴일 확인)
        self.scheduler.add_job(
            self.run_job_with_holiday_check,
            CronTrigger(hour=7, minute=0),
            args=['init_contract_data', 'GLOBAL'],
            id='daily_contract_init',
            name='Daily Contract Initialization',
            replace_existing=True
        )
        
        # 매일 7시 30분 - 선물 월물 추가
        self.scheduler.add_job(
            self.run_job_with_holiday_check,
            CronTrigger(hour=7, minute=30),
            args=['add_future_months', 'GLOBAL'],
            id='daily_future_months',
            name='Daily Future Months Update',
            replace_existing=True
        )
        
        # 매일 18시 - 시계열 데이터 수집
        self.scheduler.add_job(
            self.run_job_with_holiday_check,
            CronTrigger(hour=18, minute=0),
            args=['collect_time_data', 'GLOBAL'],
            id='daily_time_data',
            name='Daily Time Data Collection',
            replace_existing=True
        )
        
        # 매일 6시 30분 - 정리 작업
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=6, minute=30),
            args=['cleanup_old_data'],
            id='daily_cleanup',
            name='Daily Cleanup Task',
            replace_existing=True
        )
        
        # 매주 일요일 5시 - 거래시간 업데이트
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(day_of_week='sun', hour=5, minute=0),
            args=['update_trading_hours'],
            id='weekly_trading_hours',
            name='Weekly Trading Hours Update',
            replace_existing=True
        )
        
        # === 새로운 스케줄 ===
        
        # 매일 2시 - 데이터 정합성 검증
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=2, minute=0),
            args=['data_integrity_check'],
            id='daily_data_integrity',
            name='Daily Data Integrity Check',
            replace_existing=True
        )
        
        # 매일 3시 - 파티션 관리
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=3, minute=0),
            args=['partition_management'],
            id='daily_partition_management',
            name='Daily Partition Management',
            replace_existing=True
        )
        
        # 매일 4시 - 일일 통계 계산
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=4, minute=0),
            args=['daily_statistics'],
            id='daily_statistics',
            name='Daily Statistics Calculation',
            replace_existing=True
        )
        
        # 매주 일요일 2시 - 압축 정책 실행
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(day_of_week='sun', hour=2, minute=0),
            args=['compression_policy'],
            id='weekly_compression',
            name='Weekly Compression Policy',
            replace_existing=True
        )
        
        # 매일 5시 - 데이터 동기화
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=5, minute=0),
            args=['data_sync'],
            id='daily_data_sync',
            name='Daily Data Sync to Analytics',
            replace_existing=True
        )
        
        # 매일 자정 - 거래시간 캐시 확인
        self.scheduler.add_job(
            self.check_trading_hours_cache,
            CronTrigger(hour=0, minute=0),
            id='daily_cache_check',
            name='Daily Trading Hours Cache Check',
            replace_existing=True
        )
        
        logger.info("All schedules configured")
    
    async def run_job(self, job_name: str) -> Dict[str, Any]:
        """작업 실행"""
        start_time = datetime.now()
        timestamp = start_time.strftime("%Y%m%d%H%M%S")
        logger.info(f"[{job_name}] 실행 시작 - {timestamp}")
        
        try:
            # job_name에 따라 적절한 함수 실행
            if job_name == 'init_contract_data':
                result = await init_contract_data(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'add_future_months':
                result = await add_future_months(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'collect_time_data':
                result = await collect_time_data(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'update_trading_hours':
                result = await update_weekly_trading_hours(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'cleanup_old_data':
                result = await run_tasklet_job(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'data_integrity_check':
                result = await run_data_integrity_check(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'partition_management':
                result = await manage_partitions(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'daily_statistics':
                result = await calculate_daily_statistics(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'compression_policy':
                result = await manage_compression_policy(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            elif job_name == 'data_sync':
                result = await sync_data_to_analytics(
                    self.db_manager, self.ibkr_manager, self.redis_manager
                )
            else:
                raise ValueError(f"Unknown job name: {job_name}")
            
            logger.info(f"[{job_name}] 실행 종료 - status: success")
            
            # 실행 통계 기록
            if self.execution_stats:
                await self.execution_stats.record_execution(
                    job_name=job_name,
                    start_time=start_time,
                    end_time=datetime.now(),
                    status='success',
                    result=result
                )
            
            return result
            
        except Exception as e:
            logger.error(f"[{job_name}] 실행 중 오류 발생: {e}", exc_info=True)
            
            # 실행 통계 기록
            if self.execution_stats:
                await self.execution_stats.record_execution(
                    job_name=job_name,
                    start_time=start_time,
                    end_time=datetime.now(),
                    status='failed',
                    error=str(e)
                )
            
            raise
    
    async def run_job_with_holiday_check(self, job_name: str, market: str = "GLOBAL") -> Dict[str, Any]:
        """휴일을 고려한 작업 실행"""
        # 휴일 확인
        today = date.today()
        if self.holiday_calendar and not await self.holiday_calendar.should_run_batch(market, today):
            logger.info(f"[{job_name}] 오늘은 {market} 시장 휴일입니다. 작업을 건너뜁니다.")
            return {'status': 'skipped', 'reason': 'market_holiday'}
        
        # 정상 실행
        return await self.run_job(job_name)
    
    async def check_trading_hours_cache(self):
        """거래시간 캐시 확인"""
        logger.debug("거래시간 캐시 상태 확인")
        
        if not self.holiday_calendar:
            return
        
        # 주요 거래소의 캐시 상태 확인
        markets = ['US', 'KR', 'JP', 'HK', 'EU']
        today = date.today()
        
        for market in markets:
            try:
                is_trading = await self.holiday_calendar.is_trading_day(
                    Market(market), 
                    today
                )
                if not is_trading:
                    logger.debug(f"{market} 시장은 오늘 휴장입니다")
            except Exception as e:
                logger.error(f"{market} 거래시간 확인 실패: {e}")
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """스케줄된 작업 목록 반환"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    async def shutdown(self):
        """스케줄러 종료"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
        
        if self.db_manager:
            await self.db_manager.disconnect()
        
        if self.ibkr_manager and self.ibkr_manager.is_connected():
            await self.ibkr_manager.disconnect()
        
        if self.redis_manager:
            await self.redis_manager.disconnect()
        
        logger.info("Batch scheduler shut down")


# 전역 스케줄러 인스턴스
scheduler_instance = BatchScheduler()


def setup_scheduler(scheduler: AsyncIOScheduler):
    """외부에서 스케줄러 설정을 위한 함수"""
    # main.py에서 사용
    pass