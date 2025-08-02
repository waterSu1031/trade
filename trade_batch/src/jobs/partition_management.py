"""
파티션 관리 작업
- 파티션 생성 및 삭제
- 파티션 유지보수
- 파티션 모니터링
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import asyncpg

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class PartitionManager:
    """데이터베이스 파티션 관리 클래스"""
    
    def __init__(self, db_manager: DatabaseManager, redis_manager: RedisManager):
        self.db = db_manager
        self.redis = redis_manager
        
        # 파티션 설정
        self.partition_config = {
            'price_1min': {'retention_days': 7, 'partition_interval': 'daily'},
            'price_5min': {'retention_days': 30, 'partition_interval': 'weekly'},
            'price_1hour': {'retention_days': 90, 'partition_interval': 'monthly'},
            'price_1day': {'retention_days': 365, 'partition_interval': 'yearly'},
            'trade_events': {'retention_days': 180, 'partition_interval': 'monthly'},
            'orders': {'retention_days': 180, 'partition_interval': 'monthly'}
        }
    
    async def create_future_partitions(self, days_ahead: int = 7) -> Dict[str, Any]:
        """미래 파티션 생성"""
        logger.info(f"{days_ahead}일 후까지의 파티션 생성 시작")
        
        results = {
            'created': 0,
            'failed': 0,
            'details': []
        }
        
        for table_name, config in self.partition_config.items():
            try:
                if config['partition_interval'] == 'daily':
                    created = await self._create_daily_partitions(table_name, days_ahead)
                elif config['partition_interval'] == 'weekly':
                    created = await self._create_weekly_partitions(table_name, days_ahead)
                elif config['partition_interval'] == 'monthly':
                    created = await self._create_monthly_partitions(table_name, days_ahead)
                elif config['partition_interval'] == 'yearly':
                    created = await self._create_yearly_partitions(table_name, days_ahead)
                
                results['created'] += created
                results['details'].append({
                    'table': table_name,
                    'created': created,
                    'interval': config['partition_interval']
                })
                
            except Exception as e:
                logger.error(f"{table_name} 파티션 생성 실패: {e}")
                results['failed'] += 1
                results['details'].append({
                    'table': table_name,
                    'error': str(e)
                })
        
        logger.info(f"파티션 생성 완료 - 생성: {results['created']}, 실패: {results['failed']}")
        return results
    
    async def drop_old_partitions(self) -> Dict[str, Any]:
        """오래된 파티션 삭제"""
        logger.info("오래된 파티션 삭제 시작")
        
        results = {
            'dropped': 0,
            'freed_space_mb': 0,
            'details': []
        }
        
        for table_name, config in self.partition_config.items():
            try:
                retention_date = datetime.now() - timedelta(days=config['retention_days'])
                
                # 삭제할 파티션 조회
                partitions = await self._get_old_partitions(table_name, retention_date)
                
                for partition in partitions:
                    # 파티션 크기 확인
                    size_mb = await self._get_partition_size(partition['partition_name'])
                    
                    # 파티션 삭제
                    await self.db.execute(f"DROP TABLE IF EXISTS {partition['partition_name']}")
                    
                    results['dropped'] += 1
                    results['freed_space_mb'] += size_mb
                    
                    logger.info(f"파티션 삭제: {partition['partition_name']} ({size_mb} MB)")
                    
                results['details'].append({
                    'table': table_name,
                    'dropped': len(partitions),
                    'retention_days': config['retention_days']
                })
                
            except Exception as e:
                logger.error(f"{table_name} 파티션 삭제 실패: {e}")
                results['details'].append({
                    'table': table_name,
                    'error': str(e)
                })
        
        logger.info(
            f"파티션 삭제 완료 - "
            f"삭제: {results['dropped']}, "
            f"확보 공간: {results['freed_space_mb']} MB"
        )
        
        return results
    
    async def analyze_partitions(self) -> Dict[str, Any]:
        """파티션 분석 및 최적화"""
        logger.info("파티션 분석 시작")
        
        results = {
            'analyzed': 0,
            'vacuum_executed': 0,
            'reindex_executed': 0,
            'details': []
        }
        
        for table_name in self.partition_config.keys():
            try:
                # 파티션 목록 조회
                partitions = await self._get_all_partitions(table_name)
                
                for partition in partitions:
                    partition_name = partition['partition_name']
                    
                    # ANALYZE 실행
                    await self.db.execute(f"ANALYZE {partition_name}")
                    results['analyzed'] += 1
                    
                    # 파티션 상태 확인
                    stats = await self._get_partition_stats(partition_name)
                    
                    # 필요한 경우 VACUUM 실행
                    if stats.get('dead_tuples_pct', 0) > 20:
                        await self.db.execute(f"VACUUM {partition_name}")
                        results['vacuum_executed'] += 1
                        logger.info(f"VACUUM 실행: {partition_name}")
                    
                    # 인덱스 팽창률이 높은 경우 REINDEX
                    if stats.get('index_bloat_pct', 0) > 30:
                        await self.db.execute(f"REINDEX TABLE {partition_name}")
                        results['reindex_executed'] += 1
                        logger.info(f"REINDEX 실행: {partition_name}")
                
                results['details'].append({
                    'table': table_name,
                    'partitions': len(partitions),
                    'analyzed': len(partitions)
                })
                
            except Exception as e:
                logger.error(f"{table_name} 파티션 분석 실패: {e}")
                results['details'].append({
                    'table': table_name,
                    'error': str(e)
                })
        
        logger.info(
            f"파티션 분석 완료 - "
            f"분석: {results['analyzed']}, "
            f"VACUUM: {results['vacuum_executed']}, "
            f"REINDEX: {results['reindex_executed']}"
        )
        
        return results
    
    async def monitor_partition_sizes(self) -> Dict[str, Any]:
        """파티션 크기 모니터링"""
        logger.info("파티션 크기 모니터링 시작")
        
        results = {
            'total_size_gb': 0,
            'largest_partitions': [],
            'table_sizes': {}
        }
        
        for table_name in self.partition_config.keys():
            try:
                partitions = await self._get_all_partitions(table_name)
                table_total_size = 0
                
                for partition in partitions:
                    size_mb = await self._get_partition_size(partition['partition_name'])
                    table_total_size += size_mb
                    
                    # 큰 파티션 추적 (1GB 이상)
                    if size_mb > 1024:
                        results['largest_partitions'].append({
                            'name': partition['partition_name'],
                            'size_gb': round(size_mb / 1024, 2),
                            'created': partition.get('created_at')
                        })
                
                results['table_sizes'][table_name] = {
                    'size_gb': round(table_total_size / 1024, 2),
                    'partition_count': len(partitions)
                }
                results['total_size_gb'] += table_total_size / 1024
                
            except Exception as e:
                logger.error(f"{table_name} 크기 모니터링 실패: {e}")
        
        # 크기순 정렬
        results['largest_partitions'].sort(key=lambda x: x['size_gb'], reverse=True)
        results['largest_partitions'] = results['largest_partitions'][:10]  # Top 10
        
        # Redis에 캐시
        await self.redis.set(
            'partition:size_monitoring',
            results,
            expire=3600  # 1시간
        )
        
        logger.info(f"파티션 모니터링 완료 - 총 크기: {results['total_size_gb']:.2f} GB")
        
        return results
    
    async def _create_daily_partitions(self, table_name: str, days_ahead: int) -> int:
        """일별 파티션 생성"""
        created = 0
        base_date = date.today()
        
        for i in range(days_ahead):
            partition_date = base_date + timedelta(days=i)
            partition_name = f"{table_name}_{partition_date.strftime('%Y%m%d')}"
            
            # 파티션 존재 확인
            exists = await self.db.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, partition_name)
            
            if not exists:
                start_date = partition_date
                end_date = partition_date + timedelta(days=1)
                
                await self.db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name} 
                    PARTITION OF {table_name}
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                """)
                
                created += 1
                logger.debug(f"파티션 생성: {partition_name}")
        
        return created
    
    async def _create_weekly_partitions(self, table_name: str, days_ahead: int) -> int:
        """주별 파티션 생성"""
        created = 0
        base_date = date.today()
        weeks_ahead = (days_ahead + 6) // 7
        
        for i in range(weeks_ahead):
            # 주의 시작일 (월요일)
            week_start = base_date - timedelta(days=base_date.weekday()) + timedelta(weeks=i)
            week_end = week_start + timedelta(days=7)
            partition_name = f"{table_name}_{week_start.strftime('%Y_w%U')}"
            
            exists = await self.db.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, partition_name)
            
            if not exists:
                await self.db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name} 
                    PARTITION OF {table_name}
                    FOR VALUES FROM ('{week_start}') TO ('{week_end}')
                """)
                
                created += 1
                logger.debug(f"파티션 생성: {partition_name}")
        
        return created
    
    async def _create_monthly_partitions(self, table_name: str, days_ahead: int) -> int:
        """월별 파티션 생성"""
        created = 0
        base_date = date.today()
        months_ahead = (days_ahead + 29) // 30
        
        for i in range(months_ahead):
            # 월의 시작일
            year = base_date.year
            month = base_date.month + i
            
            # 연도 넘김 처리
            while month > 12:
                month -= 12
                year += 1
            
            partition_date = date(year, month, 1)
            
            # 다음 달 첫날
            if month == 12:
                next_date = date(year + 1, 1, 1)
            else:
                next_date = date(year, month + 1, 1)
            
            partition_name = f"{table_name}_{partition_date.strftime('%Y%m')}"
            
            exists = await self.db.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, partition_name)
            
            if not exists:
                await self.db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name} 
                    PARTITION OF {table_name}
                    FOR VALUES FROM ('{partition_date}') TO ('{next_date}')
                """)
                
                created += 1
                logger.debug(f"파티션 생성: {partition_name}")
        
        return created
    
    async def _create_yearly_partitions(self, table_name: str, days_ahead: int) -> int:
        """연별 파티션 생성"""
        created = 0
        base_year = date.today().year
        years_ahead = (days_ahead + 364) // 365
        
        for i in range(years_ahead):
            year = base_year + i
            partition_name = f"{table_name}_{year}"
            
            exists = await self.db.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, partition_name)
            
            if not exists:
                start_date = date(year, 1, 1)
                end_date = date(year + 1, 1, 1)
                
                await self.db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name} 
                    PARTITION OF {table_name}
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                """)
                
                created += 1
                logger.debug(f"파티션 생성: {partition_name}")
        
        return created
    
    async def _get_old_partitions(self, table_name: str, retention_date: datetime) -> List[Dict]:
        """오래된 파티션 조회"""
        return await self.db.fetch("""
            SELECT 
                schemaname,
                tablename as partition_name,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE tablename LIKE $1 || '_%'
            AND tablename < $1 || '_' || $2
            ORDER BY tablename
        """, table_name, retention_date.strftime('%Y%m%d'))
    
    async def _get_all_partitions(self, table_name: str) -> List[Dict]:
        """모든 파티션 조회"""
        return await self.db.fetch("""
            SELECT 
                schemaname,
                tablename as partition_name
            FROM pg_tables
            WHERE tablename LIKE $1 || '_%'
            ORDER BY tablename
        """, table_name)
    
    async def _get_partition_size(self, partition_name: str) -> float:
        """파티션 크기 조회 (MB)"""
        result = await self.db.fetchval("""
            SELECT pg_total_relation_size($1) / 1024.0 / 1024.0
        """, partition_name)
        
        return float(result) if result else 0.0
    
    async def _get_partition_stats(self, partition_name: str) -> Dict[str, Any]:
        """파티션 통계 조회"""
        stats = await self.db.fetchrow("""
            SELECT 
                n_dead_tup::float / NULLIF(n_live_tup + n_dead_tup, 0) * 100 as dead_tuples_pct,
                pg_stat_user_tables.n_tup_ins,
                pg_stat_user_tables.n_tup_upd,
                pg_stat_user_tables.n_tup_del
            FROM pg_stat_user_tables
            WHERE relname = $1
        """, partition_name)
        
        # 인덱스 팽창률 확인
        index_bloat = await self.db.fetchval("""
            SELECT 
                CASE WHEN otta = 0 OR bs = 0 THEN 0.0
                ELSE (relpages::float / otta) * 100 - 100
                END as bloat_pct
            FROM (
                SELECT 
                    relpages,
                    bs,
                    CEIL((reltuples * ((datahdr + ma - 
                        CASE WHEN datahdr % ma = 0 THEN ma ELSE datahdr % ma END) + 
                        nullhdr + 4)) / bs) as otta
                FROM (
                    SELECT 
                        relname, 
                        relpages, 
                        reltuples, 
                        bs,
                        23 + CASE WHEN MAX(coalesce(s.stanullfrac,0)) > 0 THEN 2 ELSE 0 END +
                        SUM(CASE WHEN s.stanullfrac IS NULL THEN 0 ELSE 1 END) / 8 as nullhdr,
                        23 as datahdr, 
                        23 % 8 as ma
                    FROM pg_class c
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    LEFT JOIN pg_statistic s ON c.oid = s.starelid
                    CROSS JOIN (
                        SELECT current_setting('block_size')::numeric as bs
                    ) as bs
                    WHERE c.relname = $1
                    GROUP BY 1,2,3,4,6,7
                ) as subq
            ) as subq2
        """, partition_name)
        
        return {
            'dead_tuples_pct': stats['dead_tuples_pct'] if stats else 0,
            'index_bloat_pct': float(index_bloat) if index_bloat else 0,
            'inserts': stats['n_tup_ins'] if stats else 0,
            'updates': stats['n_tup_upd'] if stats else 0,
            'deletes': stats['n_tup_del'] if stats else 0
        }


async def manage_partitions(
    db_manager: DatabaseManager,
    ibkr_manager: Any,
    redis_manager: RedisManager
) -> Dict[str, Any]:
    """파티션 관리 작업 실행"""
    manager = PartitionManager(db_manager, redis_manager)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'operations': {}
    }
    
    # 1. 미래 파티션 생성 (7일)
    results['operations']['create_future'] = await manager.create_future_partitions(7)
    
    # 2. 오래된 파티션 삭제
    results['operations']['drop_old'] = await manager.drop_old_partitions()
    
    # 3. 파티션 분석 및 최적화
    results['operations']['analyze'] = await manager.analyze_partitions()
    
    # 4. 파티션 크기 모니터링
    results['operations']['monitoring'] = await manager.monitor_partition_sizes()
    
    # 요약
    summary = {
        'created_partitions': results['operations']['create_future']['created'],
        'dropped_partitions': results['operations']['drop_old']['dropped'],
        'freed_space_gb': results['operations']['drop_old']['freed_space_mb'] / 1024,
        'total_size_gb': results['operations']['monitoring']['total_size_gb']
    }
    
    results['summary'] = summary
    
    logger.info(
        f"파티션 관리 완료 - "
        f"생성: {summary['created_partitions']}, "
        f"삭제: {summary['dropped_partitions']}, "
        f"총 크기: {summary['total_size_gb']:.2f} GB"
    )
    
    return results