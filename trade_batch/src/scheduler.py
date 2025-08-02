import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Dict, Any, List

from .utils.db import DatabaseManager
from .utils.ibkr import IBKRManager
from .utils.redis import RedisManager
from .config import settings

# Jobs import
from .jobs.contract_init import init_contract_data
from .jobs.future_month import add_future_months
from .jobs.market_data import collect_time_data
from .jobs.trading_hours import update_weekly_trading_hours
from .jobs.cleanup import run_tasklet_job

logger = logging.getLogger(__name__)


class BatchScheduler:
    """배치 작업 스케줄러"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_manager = DatabaseManager(settings.database_url)
        self.ibkr_manager = IBKRManager()
        self.redis_manager = RedisManager(settings.redis_url)
        
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
        
        # 스케줄 설정
        self.setup_schedules()
        
        # 스케줄러 시작
        self.scheduler.start()
        logger.info("Batch scheduler initialized and started")
    
    def setup_schedules(self):
        """스케줄 설정"""
        # 매일 7시 - 계약 구조 초기화
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=7, minute=0),
            args=['init_contract_data'],
            id='daily_contract_init',
            name='Daily Contract Initialization',
            replace_existing=True
        )
        
        # 매일 7시 30분 - 선물 월물 추가
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=7, minute=30),
            args=['add_future_months'],
            id='daily_future_months',
            name='Daily Future Months Update',
            replace_existing=True
        )
        
        # 매일 18시 - 시계열 데이터 수집
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=18, minute=0),
            args=['collect_time_data'],
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
        
        logger.info("All schedules configured")
    
    async def run_job(self, job_name: str) -> Dict[str, Any]:
        """작업 실행"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
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
            else:
                raise ValueError(f"Unknown job name: {job_name}")
            
            logger.info(f"[{job_name}] 실행 종료 - status: success")
            return result
            
        except Exception as e:
            logger.error(f"[{job_name}] 실행 중 오류 발생: {e}", exc_info=True)
            raise
    
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