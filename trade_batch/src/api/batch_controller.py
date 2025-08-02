from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, date

from ..scheduler import scheduler_instance
from ..services.connection_monitor import get_connection_monitor
from ..services.holiday_calendar import get_holiday_calendar

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/scheduled-jobs")
async def get_scheduled_jobs() -> List[Dict[str, Any]]:
    """스케줄된 작업 목록 조회"""
    # 모든 작업 정보 (기존 + 새로운 작업들)
    jobs = [
        {
            "jobName": "init_contract_data",
            "description": "계약 구조 초기화",
            "schedule": "매일 07:00",
            "cronExpression": "0 0 7 * * ?",
            "category": "basic"
        },
        {
            "jobName": "add_future_months",
            "description": "선물 월물 추가",
            "schedule": "매일 07:30",
            "cronExpression": "0 30 7 * * ?",
            "category": "basic"
        },
        {
            "jobName": "collect_time_data",
            "description": "시계열 데이터 수집",
            "schedule": "매일 18:00",
            "cronExpression": "0 0 18 * * ?",
            "category": "basic"
        },
        {
            "jobName": "cleanup_old_data",
            "description": "오래된 데이터 정리",
            "schedule": "매일 06:30",
            "cronExpression": "0 30 6 * * ?",
            "category": "basic"
        },
        {
            "jobName": "update_trading_hours",
            "description": "거래시간 업데이트",
            "schedule": "매주 일요일 05:00",
            "cronExpression": "0 0 5 * * SUN",
            "category": "basic"
        },
        {
            "jobName": "data_integrity_check",
            "description": "데이터 정합성 검증",
            "schedule": "매일 02:00",
            "cronExpression": "0 0 2 * * ?",
            "category": "advanced"
        },
        {
            "jobName": "partition_management",
            "description": "파티션 관리",
            "schedule": "매일 03:00",
            "cronExpression": "0 0 3 * * ?",
            "category": "advanced"
        },
        {
            "jobName": "daily_statistics",
            "description": "일일 통계 계산",
            "schedule": "매일 04:00",
            "cronExpression": "0 0 4 * * ?",
            "category": "advanced"
        },
        {
            "jobName": "compression_policy",
            "description": "압축 정책 실행",
            "schedule": "매주 일요일 02:00",
            "cronExpression": "0 0 2 * * SUN",
            "category": "advanced"
        },
        {
            "jobName": "data_sync",
            "description": "데이터 동기화",
            "schedule": "매일 05:00",
            "cronExpression": "0 0 5 * * ?",
            "category": "advanced"
        }
    ]
    
    # 실제 스케줄러에서 다음 실행 시간 가져오기
    scheduled_jobs = scheduler_instance.get_scheduled_jobs()
    job_map = {job['id']: job for job in scheduled_jobs}
    
    for job in jobs:
        job_id = f"daily_{job['jobName']}" if 'daily' in job['schedule'] else f"weekly_{job['jobName']}"
        if job_id in job_map:
            scheduled_job = job_map[job_id]
            job['nextRun'] = scheduled_job.get('next_run_time')
            job['status'] = 'SCHEDULED'
        else:
            job['nextRun'] = None
            job['status'] = 'NOT_SCHEDULED'
    
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
    # 스케줄된 작업 정보
    scheduled_jobs = scheduler_instance.get_scheduled_jobs()
    
    for job in scheduled_jobs:
        if job_name in job['id']:
            job_status = {
                "jobName": job_name,
                "status": "SCHEDULED",
                "nextRunTime": job.get('next_run_time'),
                "trigger": job.get('trigger')
            }
            break
    else:
        job_status = {
            "jobName": job_name,
            "status": "NOT_FOUND"
        }
    
    # Redis에서 최근 실행 결과 조회
    redis = scheduler_instance.redis_manager
    
    # 작업별 상태 키
    status_keys = {
        'data_integrity_check': 'data_integrity:last_check',
        'partition_management': 'partition:size_monitoring',
        'daily_statistics': f'daily_report:{(date.today() - timedelta(days=1)).isoformat()}',
        'compression_policy': 'compression:last_run',
        'data_sync': 'data_sync:last_run'
    }
    
    if job_name in status_keys:
        try:
            last_run_data = await redis.get(status_keys[job_name])
            if last_run_data:
                job_status['lastRunResult'] = last_run_data
        except Exception as e:
            logger.error(f"Failed to get last run data: {e}")
    
    return job_status


@router.get("/connection/status")
async def get_connection_status() -> Dict[str, Any]:
    """IBKR 연결 상태 조회"""
    try:
        monitor = await get_connection_monitor()
        if monitor:
            status = await monitor.check_connection()
            stats = await monitor.get_connection_statistics()
            
            return {
                "status": "success",
                "connection": status,
                "statistics": stats
            }
        
        return {
            "status": "error",
            "message": "Connection monitor not initialized"
        }
        
    except Exception as e:
        logger.error(f"연결 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connection/reconnect")
async def force_reconnect() -> Dict[str, Any]:
    """IBKR 강제 재연결"""
    try:
        monitor = await get_connection_monitor()
        if monitor:
            success = await monitor.attempt_reconnection()
            
            return {
                "status": "success" if success else "failed",
                "reconnected": success,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "error",
            "message": "Connection monitor not initialized"
        }
        
    except Exception as e:
        logger.error(f"재연결 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holidays")
async def get_holidays(
    market: Optional[str] = Query(None, description="Market code (US, KR, JP, HK, EU)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """휴일 정보 조회"""
    try:
        calendar = await get_holiday_calendar()
        if not calendar:
            return {
                "status": "error",
                "message": "Holiday calendar not initialized"
            }
        
        # 날짜 파싱
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start = date.today()
        
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end = start
        
        # 시장 필터링
        if market:
            # 특정 시장의 휴일만
            holidays = []
            current = start
            while current <= end:
                is_holiday = not await calendar.is_trading_day(
                    calendar.Market(market), current
                )
                if is_holiday:
                    holidays.append({
                        "date": current.isoformat(),
                        "market": market,
                        "is_holiday": True
                    })
                current = current.replace(day=current.day + 1)
        else:
            # 모든 시장의 휴일 정보
            holidays = []
            current = start
            while current <= end:
                info = await calendar.get_holiday_info(current)
                holidays.append(info)
                current = current.replace(day=current.day + 1)
        
        return {
            "status": "success",
            "holidays": holidays,
            "total": len(holidays)
        }
        
    except Exception as e:
        logger.error(f"휴일 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/daily")
async def get_daily_statistics(
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """일일 통계 조회"""
    try:
        redis = scheduler_instance.redis_manager
        
        # 날짜 결정
        if target_date:
            report_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            report_date = date.today() - timedelta(days=1)  # 어제
        
        # Redis에서 리포트 조회
        report = await redis.get(f'daily_report:{report_date.isoformat()}')
        
        if report:
            return {
                "status": "success",
                "report": report
            }
        
        return {
            "status": "not_found",
            "message": f"No report found for {report_date}"
        }
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/overview")
async def get_monitoring_overview() -> Dict[str, Any]:
    """전체 모니터링 현황"""
    try:
        redis = scheduler_instance.redis_manager
        
        # 각종 상태 수집
        overview = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "recent_executions": {}
        }
        
        # IBKR 연결 상태
        try:
            monitor = await get_connection_monitor()
            if monitor:
                overview["services"]["ibkr_connection"] = monitor.get_status_info()
        except Exception as e:
            logger.error(f"Failed to get connection monitor: {e}")
        
        # 스케줄러 상태
        jobs = scheduler_instance.get_scheduled_jobs()
        overview["services"]["scheduler"] = {
            "active_jobs": len(jobs),
            "next_job": min((job['next_run_time'] for job in jobs if job.get('next_run_time')), default=None)
        }
        
        # 최근 작업 실행 결과
        result_keys = {
            'data_integrity': 'data_integrity:last_check',
            'compression': 'compression:last_run',
            'data_sync': 'data_sync:last_run',
            'partition_monitoring': 'partition:size_monitoring'
        }
        
        for name, key in result_keys.items():
            try:
                result = await redis.get(key)
                if result and isinstance(result, dict):
                    overview["recent_executions"][name] = {
                        'timestamp': result.get('timestamp'),
                        'status': 'success' if result else 'no_data'
                    }
            except Exception as e:
                logger.error(f"Failed to get {name} result: {e}")
        
        return overview
        
    except Exception as e:
        logger.error(f"모니터링 현황 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """헬스 체크"""
    health_status = {
        "status": "healthy",
        "service": "trade_batch",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # 데이터베이스 연결 확인
    try:
        await scheduler_instance.db_manager.fetch("SELECT 1")
        health_status["components"]["database"] = "healthy"
    except Exception:
        health_status["components"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Redis 연결 확인
    try:
        await scheduler_instance.redis_manager.ping()
        health_status["components"]["redis"] = "healthy"
    except Exception:
        health_status["components"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # IBKR 연결 확인
    try:
        is_connected = scheduler_instance.ibkr_manager.is_connected()
        health_status["components"]["ibkr"] = "healthy" if is_connected else "disconnected"
    except Exception:
        health_status["components"]["ibkr"] = "error"
    
    # 스케줄러 상태
    try:
        jobs = scheduler_instance.get_scheduled_jobs()
        health_status["components"]["scheduler"] = {
            "status": "healthy",
            "active_jobs": len(jobs)
        }
    except Exception:
        health_status["components"]["scheduler"] = {"status": "error"}
    
    return health_status


@router.get("/statistics/execution/{job_name}")
async def get_job_execution_statistics(
    job_name: str,
    period_days: int = Query(7, description="Period in days")
) -> Dict[str, Any]:
    """작업별 실행 통계 조회"""
    try:
        stats_service = await get_execution_statistics()
        if not stats_service:
            return {
                "status": "error",
                "message": "Statistics service not initialized"
            }
        
        stats = await stats_service.get_job_statistics(job_name, period_days)
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/performance-report")
async def get_performance_report(
    report_date: Optional[str] = Query(None, description="Report date (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """성능 리포트 조회"""
    try:
        stats_service = await get_execution_statistics()
        if not stats_service:
            return {
                "status": "error",
                "message": "Statistics service not initialized"
            }
        
        if report_date:
            date_obj = datetime.strptime(report_date, "%Y-%m-%d").date()
        else:
            date_obj = None
        
        report = await stats_service.generate_performance_report(date_obj)
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"성능 리포트 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_configuration(
    path: Optional[str] = Query(None, description="Configuration path (e.g., 'scheduler.check_interval')")
) -> Dict[str, Any]:
    """현재 설정 조회"""
    try:
        config_manager = await get_configuration_manager()
        if not config_manager:
            return {
                "status": "error",
                "message": "Configuration manager not initialized"
            }
        
        config = await config_manager.get_config(path)
        return {
            "status": "success",
            "config": config,
            "version": config_manager.config_version
        }
        
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_configuration(
    updates: Dict[str, Any],
    validate: bool = Query(True, description="Validate before applying")
) -> Dict[str, Any]:
    """설정 업데이트"""
    try:
        config_manager = await get_configuration_manager()
        if not config_manager:
            return {
                "status": "error",
                "message": "Configuration manager not initialized"
            }
        
        result = await config_manager.update_config(updates, validate)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"설정 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup")
async def create_backup(
    backup_type: str = Query("daily", description="Backup type (daily/weekly/monthly)"),
    tables: Optional[List[str]] = Query(None, description="Specific tables to backup")
) -> Dict[str, Any]:
    """백업 생성"""
    try:
        backup_service = await get_backup_service()
        if not backup_service:
            return {
                "status": "error",
                "message": "Backup service not initialized"
            }
        
        result = await backup_service.create_backup(backup_type, tables)
        return {
            "status": "success",
            "backup": result
        }
        
    except Exception as e:
        logger.error(f"백업 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup")
async def list_backups() -> Dict[str, Any]:
    """백업 목록 조회"""
    try:
        backup_service = await get_backup_service()
        if not backup_service:
            return {
                "status": "error",
                "message": "Backup service not initialized"
            }
        
        backups = await backup_service.list_backups()
        stats = backup_service.get_backup_statistics()
        
        return {
            "status": "success",
            "backups": backups,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"백업 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trading-hours/cache-stats")
async def get_trading_hours_cache_stats() -> Dict[str, Any]:
    """거래시간 캐시 통계"""
    try:
        cache_service = await get_trading_hour_cache()
        if not cache_service:
            return {
                "status": "error",
                "message": "Trading hour cache not initialized"
            }
        
        stats = cache_service.get_cache_stats()
        return {
            "status": "success",
            "cache_stats": stats
        }
        
    except Exception as e:
        logger.error(f"캐시 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 추가 imports 필요
from datetime import timedelta