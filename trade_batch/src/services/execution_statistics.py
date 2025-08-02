"""
상세 실행 통계 추적 서비스
- 작업 실행 통계
- 성능 모니터링
- 통계 리포트 생성
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from collections import defaultdict
import statistics

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class ExecutionStatistics:
    """실행 통계 추적 서비스"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        redis_manager: RedisManager
    ):
        self.db = db_manager
        self.redis = redis_manager
        
        # 실시간 통계 저장소
        self.current_stats = defaultdict(lambda: {
            'count': 0,
            'success': 0,
            'failed': 0,
            'durations': [],
            'errors': []
        })
        
        # 성능 임계값
        self.performance_thresholds = {
            'init_contract_data': 300,      # 5분
            'add_future_months': 180,       # 3분
            'collect_time_data': 600,       # 10분
            'data_integrity_check': 1800,   # 30분
            'partition_management': 600,    # 10분
            'daily_statistics': 900,        # 15분
            'compression_policy': 3600,     # 1시간
            'data_sync': 1800              # 30분
        }
    
    async def record_execution(
        self,
        job_name: str,
        start_time: datetime,
        end_time: datetime,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """작업 실행 기록"""
        duration = (end_time - start_time).total_seconds()
        
        # 실시간 통계 업데이트
        stats = self.current_stats[job_name]
        stats['count'] += 1
        stats['durations'].append(duration)
        
        if status == 'success':
            stats['success'] += 1
        else:
            stats['failed'] += 1
            if error:
                stats['errors'].append({
                    'timestamp': end_time.isoformat(),
                    'error': error[:200]  # 최대 200자
                })
        
        # DB에 저장
        await self.db.execute("""
            INSERT INTO job_execution_history (
                job_name, start_time, end_time, duration_seconds,
                status, result_summary, error_message
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, job_name, start_time, end_time, duration,
            status, json.dumps(result) if result else None, error)
        
        # Redis에 최근 실행 정보 저장
        execution_info = {
            'job_name': job_name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': duration,
            'status': status
        }
        
        await self.redis.lpush(
            f"execution:recent:{job_name}",
            execution_info
        )
        
        # 리스트 크기 제한 (최근 100개)
        await self.redis.ltrim(f"execution:recent:{job_name}", 0, 99)
        
        # 성능 알림 확인
        await self._check_performance_alert(job_name, duration)
    
    async def _check_performance_alert(self, job_name: str, duration: float):
        """성능 알림 확인"""
        threshold = self.performance_thresholds.get(job_name)
        
        if threshold and duration > threshold:
            alert = {
                'job_name': job_name,
                'duration': duration,
                'threshold': threshold,
                'exceeded_by': duration - threshold,
                'timestamp': datetime.now().isoformat()
            }
            
            # 알림 발송
            await self.redis.publish('alert_events', {
                'alert_type': 'PERFORMANCE_THRESHOLD_EXCEEDED',
                'severity': 'WARNING',
                'details': alert
            })
            
            logger.warning(
                f"성능 임계값 초과: {job_name} - "
                f"{duration:.1f}초 (임계값: {threshold}초)"
            )
    
    async def get_job_statistics(
        self,
        job_name: str,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """작업별 통계 조회"""
        start_date = datetime.now() - timedelta(days=period_days)
        
        # DB에서 실행 기록 조회
        rows = await self.db.fetch("""
            SELECT 
                COUNT(*) as total_runs,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                AVG(duration_seconds) as avg_duration,
                MIN(duration_seconds) as min_duration,
                MAX(duration_seconds) as max_duration,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_seconds) as median_duration,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds) as p95_duration
            FROM job_execution_history
            WHERE job_name = $1 AND start_time >= $2
        """, job_name, start_date)
        
        if not rows:
            return {'job_name': job_name, 'no_data': True}
        
        stats = dict(rows[0])
        
        # 성공률 계산
        if stats['total_runs'] > 0:
            stats['success_rate'] = (stats['success_count'] / stats['total_runs']) * 100
        else:
            stats['success_rate'] = 0
        
        # 일별 통계
        daily_stats = await self.db.fetch("""
            SELECT 
                DATE(start_time) as date,
                COUNT(*) as runs,
                AVG(duration_seconds) as avg_duration,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count
            FROM job_execution_history
            WHERE job_name = $1 AND start_time >= $2
            GROUP BY DATE(start_time)
            ORDER BY date
        """, job_name, start_date)
        
        stats['daily_stats'] = [dict(row) for row in daily_stats]
        
        # 최근 오류
        recent_errors = await self.db.fetch("""
            SELECT start_time, error_message
            FROM job_execution_history
            WHERE job_name = $1 AND status = 'failed' AND start_time >= $2
            ORDER BY start_time DESC
            LIMIT 5
        """, job_name, start_date)
        
        stats['recent_errors'] = [dict(row) for row in recent_errors]
        
        return stats
    
    async def get_overall_statistics(
        self,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """전체 통계 조회"""
        start_date = datetime.now() - timedelta(days=period_days)
        
        # 전체 요약
        summary = await self.db.fetchrow("""
            SELECT 
                COUNT(*) as total_executions,
                COUNT(DISTINCT job_name) as unique_jobs,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as total_success,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as total_failed,
                AVG(duration_seconds) as avg_duration,
                SUM(duration_seconds) as total_duration
            FROM job_execution_history
            WHERE start_time >= $1
        """, start_date)
        
        overall_stats = dict(summary) if summary else {}
        
        # 작업별 요약
        job_summary = await self.db.fetch("""
            SELECT 
                job_name,
                COUNT(*) as runs,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                AVG(duration_seconds) as avg_duration
            FROM job_execution_history
            WHERE start_time >= $1
            GROUP BY job_name
            ORDER BY runs DESC
        """, start_date)
        
        overall_stats['jobs'] = [dict(row) for row in job_summary]
        
        # 시간대별 실행 패턴
        hourly_pattern = await self.db.fetch("""
            SELECT 
                EXTRACT(HOUR FROM start_time) as hour,
                COUNT(*) as executions,
                AVG(duration_seconds) as avg_duration
            FROM job_execution_history
            WHERE start_time >= $1
            GROUP BY EXTRACT(HOUR FROM start_time)
            ORDER BY hour
        """, start_date)
        
        overall_stats['hourly_pattern'] = [dict(row) for row in hourly_pattern]
        
        # 성공률 계산
        if overall_stats.get('total_executions', 0) > 0:
            overall_stats['overall_success_rate'] = (
                overall_stats['total_success'] / overall_stats['total_executions']
            ) * 100
        else:
            overall_stats['overall_success_rate'] = 0
        
        return overall_stats
    
    async def generate_performance_report(
        self,
        report_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """성능 리포트 생성"""
        if not report_date:
            report_date = date.today() - timedelta(days=1)
        
        report = {
            'report_date': report_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'jobs': {}
        }
        
        # 각 작업별 성능 분석
        jobs = await self.db.fetch("""
            SELECT DISTINCT job_name
            FROM job_execution_history
            WHERE DATE(start_time) = $1
        """, report_date)
        
        for job_row in jobs:
            job_name = job_row['job_name']
            
            # 해당 날짜의 실행 데이터
            executions = await self.db.fetch("""
                SELECT 
                    start_time,
                    end_time,
                    duration_seconds,
                    status
                FROM job_execution_history
                WHERE job_name = $1 AND DATE(start_time) = $2
                ORDER BY start_time
            """, job_name, report_date)
            
            if not executions:
                continue
            
            durations = [row['duration_seconds'] for row in executions]
            success_count = sum(1 for row in executions if row['status'] == 'success')
            
            job_stats = {
                'total_runs': len(executions),
                'success_count': success_count,
                'failed_count': len(executions) - success_count,
                'success_rate': (success_count / len(executions)) * 100,
                'performance': {
                    'avg_duration': statistics.mean(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'median_duration': statistics.median(durations),
                    'std_deviation': statistics.stdev(durations) if len(durations) > 1 else 0
                },
                'threshold': self.performance_thresholds.get(job_name),
                'threshold_violations': sum(
                    1 for d in durations 
                    if self.performance_thresholds.get(job_name) and 
                    d > self.performance_thresholds[job_name]
                )
            }
            
            # 성능 등급 판정
            if job_stats['success_rate'] >= 95 and job_stats['threshold_violations'] == 0:
                job_stats['grade'] = 'EXCELLENT'
            elif job_stats['success_rate'] >= 90 and job_stats['threshold_violations'] <= 1:
                job_stats['grade'] = 'GOOD'
            elif job_stats['success_rate'] >= 80:
                job_stats['grade'] = 'FAIR'
            else:
                job_stats['grade'] = 'POOR'
            
            report['jobs'][job_name] = job_stats
        
        # 전체 요약
        all_success = sum(j['success_count'] for j in report['jobs'].values())
        all_total = sum(j['total_runs'] for j in report['jobs'].values())
        
        report['summary'] = {
            'total_jobs': len(report['jobs']),
            'total_executions': all_total,
            'overall_success_rate': (all_success / all_total * 100) if all_total > 0 else 0,
            'excellent_jobs': sum(1 for j in report['jobs'].values() if j['grade'] == 'EXCELLENT'),
            'poor_jobs': sum(1 for j in report['jobs'].values() if j['grade'] == 'POOR')
        }
        
        # Redis에 리포트 저장
        await self.redis.set(
            f"performance_report:{report_date.isoformat()}",
            report,
            expire=86400 * 30  # 30일
        )
        
        return report
    
    async def get_trend_analysis(
        self,
        job_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """추세 분석"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # 일별 데이터
        daily_data = await self.db.fetch("""
            SELECT 
                DATE(start_time) as date,
                COUNT(*) as runs,
                AVG(duration_seconds) as avg_duration,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
                MAX(duration_seconds) as max_duration
            FROM job_execution_history
            WHERE job_name = $1 AND DATE(start_time) BETWEEN $2 AND $3
            GROUP BY DATE(start_time)
            ORDER BY date
        """, job_name, start_date, end_date)
        
        if not daily_data:
            return {'job_name': job_name, 'no_data': True}
        
        # 추세 계산
        dates = [row['date'] for row in daily_data]
        durations = [row['avg_duration'] for row in daily_data]
        success_rates = [
            (row['success_count'] / row['runs'] * 100) if row['runs'] > 0 else 0
            for row in daily_data
        ]
        
        # 간단한 선형 추세 (증가/감소)
        duration_trend = 'stable'
        if len(durations) >= 7:
            first_week_avg = statistics.mean(durations[:7])
            last_week_avg = statistics.mean(durations[-7:])
            
            change_percent = ((last_week_avg - first_week_avg) / first_week_avg) * 100
            
            if change_percent > 10:
                duration_trend = 'increasing'
            elif change_percent < -10:
                duration_trend = 'decreasing'
        
        return {
            'job_name': job_name,
            'period': f"{start_date} to {end_date}",
            'daily_data': [dict(row) for row in daily_data],
            'trends': {
                'duration_trend': duration_trend,
                'avg_duration_change': change_percent if 'change_percent' in locals() else 0,
                'current_avg_duration': durations[-1] if durations else 0,
                'current_success_rate': success_rates[-1] if success_rates else 0
            },
            'statistics': {
                'total_runs': sum(row['runs'] for row in daily_data),
                'avg_daily_runs': statistics.mean([row['runs'] for row in daily_data]),
                'overall_avg_duration': statistics.mean(durations),
                'overall_success_rate': statistics.mean(success_rates)
            }
        }
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """실시간 통계 반환"""
        stats = {}
        
        for job_name, job_stats in self.current_stats.items():
            success_rate = 0
            if job_stats['count'] > 0:
                success_rate = (job_stats['success'] / job_stats['count']) * 100
            
            avg_duration = 0
            if job_stats['durations']:
                avg_duration = statistics.mean(job_stats['durations'])
            
            stats[job_name] = {
                'total_runs': job_stats['count'],
                'success_count': job_stats['success'],
                'failed_count': job_stats['failed'],
                'success_rate': success_rate,
                'avg_duration': avg_duration,
                'recent_errors': job_stats['errors'][-5:]  # 최근 5개
            }
        
        return stats
    
    async def cleanup_old_statistics(self, retention_days: int = 90):
        """오래된 통계 정리"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        deleted = await self.db.execute("""
            DELETE FROM job_execution_history
            WHERE start_time < $1
        """, cutoff_date)
        
        logger.info(f"오래된 실행 기록 {deleted}개 삭제됨")
        
        return {'deleted_records': deleted}


# 전역 통계 인스턴스
statistics_instance: Optional[ExecutionStatistics] = None


async def initialize_execution_statistics(
    db_manager: DatabaseManager,
    redis_manager: RedisManager
) -> ExecutionStatistics:
    """실행 통계 서비스 초기화"""
    global statistics_instance
    
    if statistics_instance is None:
        statistics_instance = ExecutionStatistics(db_manager, redis_manager)
    
    return statistics_instance


async def get_execution_statistics() -> Optional[ExecutionStatistics]:
    """실행 통계 인스턴스 반환"""
    return statistics_instance


# JSON import 추가
import json