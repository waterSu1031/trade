from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import logging
from datetime import datetime

from ..scheduler import scheduler_instance

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/scheduled-jobs")
async def get_scheduled_jobs() -> List[Dict[str, Any]]:
    """스케줄된 작업 목록 조회"""
    # 하드코딩된 작업 정보 (Java 버전과 동일)
    jobs = [
        {
            "jobName": "init_contract_data",
            "description": "계약 구조 초기화",
            "schedule": "매일 07:00",
            "cronExpression": "0 0 7 * * ?",
            "lastRun": None,
            "nextRun": None,
            "status": "READY"
        },
        {
            "jobName": "add_future_months",
            "description": "선물 월물 추가",
            "schedule": "매일 07:30",
            "cronExpression": "0 30 7 * * ?",
            "lastRun": None,
            "nextRun": None,
            "status": "READY"
        },
        {
            "jobName": "collect_time_data",
            "description": "시계열 데이터 수집",
            "schedule": "매일 18:00",
            "cronExpression": "0 0 18 * * ?",
            "lastRun": None,
            "nextRun": None,
            "status": "READY"
        },
        {
            "jobName": "cleanup_old_data",
            "description": "오래된 데이터 정리",
            "schedule": "매일 06:30",
            "cronExpression": "0 30 6 * * ?",
            "lastRun": None,
            "nextRun": None,
            "status": "READY"
        },
        {
            "jobName": "update_trading_hours",
            "description": "거래시간 업데이트",
            "schedule": "매주 일요일 05:00",
            "cronExpression": "0 0 5 * * SUN",
            "lastRun": None,
            "nextRun": None,
            "status": "READY"
        }
    ]
    
    # 실제 스케줄러에서 다음 실행 시간 가져오기
    scheduled_jobs = scheduler_instance.get_scheduled_jobs()
    job_map = {job['id'].replace('_', ''): job for job in scheduled_jobs}
    
    for job in jobs:
        job_id = job['jobName'].replace('_', '')
        if job_id in job_map:
            scheduled_job = job_map[job_id]
            job['nextRun'] = scheduled_job.get('next_run_time')
    
    return jobs


@router.post("/jobs/{job_name}/run")
async def run_job_manual(job_name: str) -> Dict[str, Any]:
    """수동으로 작업 실행"""
    try:
        logger.info(f"Manual job execution requested: {job_name}")
        
        # 비동기로 작업 실행
        result = await scheduler_instance.run_job(job_name)
        
        return {
            "status": "success",
            "message": f"{job_name} started successfully",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run job {job_name}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to execute job: {str(e)}"
        )


@router.get("/jobs/{job_name}/status")
async def get_job_status(job_name: str) -> Dict[str, Any]:
    """작업 상태 조회"""
    scheduled_jobs = scheduler_instance.get_scheduled_jobs()
    
    for job in scheduled_jobs:
        if job['id'] == job_name or job['id'].replace('_', '') == job_name.replace('_', ''):
            return {
                "jobName": job_name,
                "status": "SCHEDULED",
                "nextRunTime": job.get('next_run_time'),
                "trigger": job.get('trigger')
            }
    
    raise HTTPException(status_code=404, detail=f"Job {job_name} not found")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "trade_batch",
        "timestamp": datetime.now().isoformat()
    }