"""
데이터 동기화 작업
- PostgreSQL에서 DuckDB로 데이터 동기화
- 분석용 데이터 준비
- 동기화 상태 모니터링
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import asyncpg
import duckdb
import pandas as pd
from pathlib import Path

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class DataSyncManager:
    """데이터 동기화 관리 클래스"""
    
    def __init__(self, db_manager: DatabaseManager, redis_manager: RedisManager):
        self.db = db_manager
        self.redis = redis_manager
        
        # DuckDB 설정
        self.duckdb_path = Path("data/analytics.duckdb")
        self.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 동기화 설정
        self.sync_config = {
            'trade_events': {
                'sync_interval': 'hourly',
                'retention_days': 90,
                'batch_size': 10000
            },
            'orders': {
                'sync_interval': 'hourly',
                'retention_days': 90,
                'batch_size': 10000
            },
            'price_1min': {
                'sync_interval': 'daily',
                'retention_days': 7,
                'batch_size': 50000
            },
            'price_5min': {
                'sync_interval': 'daily',
                'retention_days': 30,
                'batch_size': 50000
            },
            'price_1hour': {
                'sync_interval': 'daily',
                'retention_days': 90,
                'batch_size': 50000
            },
            'price_1day': {
                'sync_interval': 'daily',
                'retention_days': 365,
                'batch_size': 10000
            },
            'positions': {
                'sync_interval': 'hourly',
                'retention_days': None,  # 전체 동기화
                'batch_size': 1000
            }
        }
    
    async def sync_postgresql_to_duckdb(self) -> Dict[str, Any]:
        """PostgreSQL에서 DuckDB로 데이터 동기화"""
        logger.info("PostgreSQL → DuckDB 동기화 시작")
        
        results = {
            'synced_tables': 0,
            'total_rows': 0,
            'failed_tables': 0,
            'details': []
        }
        
        # DuckDB 연결
        with duckdb.connect(str(self.duckdb_path)) as duckdb_conn:
            # 각 테이블 동기화
            for table_name, config in self.sync_config.items():
                try:
                    sync_result = await self._sync_table(
                        duckdb_conn, 
                        table_name, 
                        config
                    )
                    
                    if sync_result['status'] == 'success':
                        results['synced_tables'] += 1
                        results['total_rows'] += sync_result['rows_synced']
                    else:
                        results['failed_tables'] += 1
                    
                    results['details'].append(sync_result)
                    
                except Exception as e:
                    logger.error(f"{table_name} 동기화 실패: {e}")
                    results['failed_tables'] += 1
                    results['details'].append({
                        'table': table_name,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # 동기화 메타데이터 업데이트
            self._update_sync_metadata(duckdb_conn, results)
        
        # Redis에 동기화 상태 저장
        await self.redis.set(
            'data_sync:last_run',
            {
                'timestamp': datetime.now().isoformat(),
                'results': results
            },
            expire=3600
        )
        
        logger.info(
            f"동기화 완료 - "
            f"성공: {results['synced_tables']}, "
            f"실패: {results['failed_tables']}, "
            f"총 행: {results['total_rows']}"
        )
        
        return results
    
    async def _sync_table(
        self, 
        duckdb_conn: duckdb.DuckDBPyConnection,
        table_name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """개별 테이블 동기화"""
        logger.info(f"{table_name} 테이블 동기화 시작")
        
        result = {
            'table': table_name,
            'status': 'pending',
            'rows_synced': 0,
            'sync_time_sec': 0,
            'last_sync_timestamp': None
        }
        
        start_time = datetime.now()
        
        try:
            # 마지막 동기화 시점 확인
            last_sync = await self._get_last_sync_timestamp(table_name)
            
            # 동기화할 데이터 범위 결정
            where_clause = ""
            params = []
            
            if last_sync:
                where_clause = "WHERE updated_at > $1"
                params.append(last_sync)
            elif config['retention_days']:
                where_clause = "WHERE time > $1"
                params.append(datetime.now() - timedelta(days=config['retention_days']))
            
            # 데이터 개수 확인
            count_query = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
            total_rows = await self.db.fetchval(count_query, *params)
            
            if total_rows == 0:
                logger.info(f"{table_name}: 동기화할 새 데이터 없음")
                result['status'] = 'success'
                result['sync_message'] = 'No new data to sync'
                return result
            
            logger.info(f"{table_name}: {total_rows}개 행 동기화 예정")
            
            # 배치 단위로 데이터 동기화
            batch_size = config['batch_size']
            offset = 0
            
            # DuckDB 테이블 생성 (없는 경우)
            await self._create_duckdb_table(duckdb_conn, table_name)
            
            while offset < total_rows:
                # PostgreSQL에서 데이터 조회
                query = f"""
                    SELECT * FROM {table_name} 
                    {where_clause}
                    ORDER BY time
                    LIMIT {batch_size} OFFSET {offset}
                """
                
                rows = await self.db.fetch(query, *params)
                
                if not rows:
                    break
                
                # DataFrame으로 변환
                df = pd.DataFrame([dict(row) for row in rows])
                
                # DuckDB에 삽입
                if offset == 0 and not last_sync:
                    # 첫 동기화인 경우 테이블 교체
                    duckdb_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    duckdb_conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
                else:
                    # 증분 동기화
                    duckdb_conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")
                
                offset += len(rows)
                result['rows_synced'] += len(rows)
                
                logger.debug(f"{table_name}: {offset}/{total_rows} 행 동기화 완료")
            
            # 인덱스 생성
            await self._create_duckdb_indexes(duckdb_conn, table_name)
            
            # 통계 업데이트
            duckdb_conn.execute(f"ANALYZE {table_name}")
            
            result['status'] = 'success'
            result['sync_time_sec'] = (datetime.now() - start_time).total_seconds()
            result['last_sync_timestamp'] = datetime.now().isoformat()
            
            # 동기화 타임스탬프 저장
            await self._save_sync_timestamp(table_name, datetime.now())
            
        except Exception as e:
            logger.error(f"{table_name} 동기화 중 오류: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            raise
        
        return result
    
    async def verify_sync_integrity(self) -> Dict[str, Any]:
        """동기화 데이터 정합성 검증"""
        logger.info("동기화 정합성 검증 시작")
        
        results = {
            'verified_tables': 0,
            'issues_found': 0,
            'details': []
        }
        
        with duckdb.connect(str(self.duckdb_path)) as duckdb_conn:
            for table_name in self.sync_config.keys():
                try:
                    # PostgreSQL 행 수
                    pg_count = await self.db.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                    
                    # DuckDB 행 수
                    duckdb_result = duckdb_conn.execute(
                        f"SELECT COUNT(*) as cnt FROM {table_name}"
                    ).fetchone()
                    duckdb_count = duckdb_result[0] if duckdb_result else 0
                    
                    # 차이 확인
                    diff = abs(pg_count - duckdb_count)
                    diff_pct = (diff / pg_count * 100) if pg_count > 0 else 0
                    
                    verification = {
                        'table': table_name,
                        'pg_count': pg_count,
                        'duckdb_count': duckdb_count,
                        'difference': diff,
                        'diff_percentage': diff_pct,
                        'status': 'ok' if diff_pct < 1 else 'mismatch'
                    }
                    
                    if verification['status'] == 'mismatch':
                        results['issues_found'] += 1
                        logger.warning(
                            f"{table_name} 행 수 불일치: "
                            f"PostgreSQL={pg_count}, DuckDB={duckdb_count}"
                        )
                    
                    results['verified_tables'] += 1
                    results['details'].append(verification)
                    
                except Exception as e:
                    logger.error(f"{table_name} 검증 실패: {e}")
                    results['details'].append({
                        'table': table_name,
                        'status': 'error',
                        'error': str(e)
                    })
        
        return results
    
    async def optimize_duckdb(self) -> Dict[str, Any]:
        """DuckDB 최적화"""
        logger.info("DuckDB 최적화 시작")
        
        results = {
            'vacuum_executed': False,
            'checkpoint_created': False,
            'size_before_mb': 0,
            'size_after_mb': 0,
            'tables_analyzed': []
        }
        
        # 파일 크기 (최적화 전)
        if self.duckdb_path.exists():
            results['size_before_mb'] = self.duckdb_path.stat().st_size / 1024 / 1024
        
        with duckdb.connect(str(self.duckdb_path)) as duckdb_conn:
            try:
                # VACUUM 실행
                duckdb_conn.execute("VACUUM")
                results['vacuum_executed'] = True
                logger.info("VACUUM 실행 완료")
                
                # CHECKPOINT 생성
                duckdb_conn.execute("CHECKPOINT")
                results['checkpoint_created'] = True
                logger.info("CHECKPOINT 생성 완료")
                
                # 각 테이블 ANALYZE
                for table_name in self.sync_config.keys():
                    try:
                        duckdb_conn.execute(f"ANALYZE {table_name}")
                        results['tables_analyzed'].append(table_name)
                    except Exception:
                        pass
                
                logger.info(f"ANALYZE 실행 완료: {len(results['tables_analyzed'])}개 테이블")
                
            except Exception as e:
                logger.error(f"DuckDB 최적화 실패: {e}")
        
        # 파일 크기 (최적화 후)
        if self.duckdb_path.exists():
            results['size_after_mb'] = self.duckdb_path.stat().st_size / 1024 / 1024
            results['space_saved_mb'] = results['size_before_mb'] - results['size_after_mb']
        
        return results
    
    async def generate_analytics_views(self) -> Dict[str, Any]:
        """분석용 뷰 생성"""
        logger.info("분석용 뷰 생성 시작")
        
        results = {
            'views_created': 0,
            'views_updated': 0,
            'failed': 0,
            'details': []
        }
        
        # 분석용 뷰 정의
        analytics_views = {
            'v_daily_trading_summary': """
                CREATE OR REPLACE VIEW v_daily_trading_summary AS
                SELECT 
                    DATE_TRUNC('day', time) as trading_date,
                    symbol,
                    COUNT(*) as trade_count,
                    SUM(executed_qty) as total_volume,
                    SUM(executed_qty * executed_price) as total_turnover,
                    SUM(realizedPNL) as total_pnl,
                    SUM(commission) as total_commission,
                    AVG(executed_price) as avg_price,
                    MIN(executed_price) as low_price,
                    MAX(executed_price) as high_price
                FROM trade_events
                GROUP BY DATE_TRUNC('day', time), symbol
            """,
            
            'v_position_history': """
                CREATE OR REPLACE VIEW v_position_history AS
                WITH position_changes AS (
                    SELECT 
                        symbol,
                        time,
                        SUM(CASE WHEN side = 'BUY' THEN executed_qty ELSE -executed_qty END) 
                            OVER (PARTITION BY symbol ORDER BY time) as running_position,
                        executed_price,
                        realizedPNL
                    FROM trade_events
                )
                SELECT * FROM position_changes
                WHERE ABS(running_position) > 0.0001
            """,
            
            'v_hourly_performance': """
                CREATE OR REPLACE VIEW v_hourly_performance AS
                SELECT 
                    DATE_TRUNC('hour', time) as hour,
                    COUNT(*) as trades,
                    SUM(realizedPNL) as hourly_pnl,
                    SUM(commission) as hourly_commission,
                    COUNT(DISTINCT symbol) as symbols_traded,
                    SUM(executed_qty * executed_price) as hourly_volume
                FROM trade_events
                GROUP BY DATE_TRUNC('hour', time)
            """,
            
            'v_symbol_performance': """
                CREATE OR REPLACE VIEW v_symbol_performance AS
                SELECT 
                    symbol,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN realizedPNL > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN realizedPNL < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(realizedPNL) as total_pnl,
                    AVG(realizedPNL) as avg_pnl_per_trade,
                    SUM(commission) as total_commission,
                    SUM(executed_qty) as total_volume,
                    MIN(time) as first_trade,
                    MAX(time) as last_trade
                FROM trade_events
                GROUP BY symbol
            """
        }
        
        with duckdb.connect(str(self.duckdb_path)) as duckdb_conn:
            for view_name, view_sql in analytics_views.items():
                try:
                    # 뷰 존재 여부 확인
                    existing = duckdb_conn.execute(
                        "SELECT COUNT(*) FROM duckdb_views() WHERE view_name = ?",
                        [view_name]
                    ).fetchone()[0]
                    
                    # 뷰 생성/업데이트
                    duckdb_conn.execute(view_sql)
                    
                    if existing:
                        results['views_updated'] += 1
                        status = 'updated'
                    else:
                        results['views_created'] += 1
                        status = 'created'
                    
                    results['details'].append({
                        'view': view_name,
                        'status': status
                    })
                    
                    logger.info(f"뷰 {status}: {view_name}")
                    
                except Exception as e:
                    logger.error(f"뷰 생성 실패 - {view_name}: {e}")
                    results['failed'] += 1
                    results['details'].append({
                        'view': view_name,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
    
    async def _get_last_sync_timestamp(self, table_name: str) -> Optional[datetime]:
        """마지막 동기화 시점 조회"""
        result = await self.redis.get(f'data_sync:last_timestamp:{table_name}')
        if result:
            return datetime.fromisoformat(result)
        return None
    
    async def _save_sync_timestamp(self, table_name: str, timestamp: datetime):
        """동기화 시점 저장"""
        await self.redis.set(
            f'data_sync:last_timestamp:{table_name}',
            timestamp.isoformat(),
            expire=86400 * 7  # 7일
        )
    
    async def _create_duckdb_table(self, duckdb_conn: duckdb.DuckDBPyConnection, table_name: str):
        """DuckDB 테이블 생성"""
        # 테이블 존재 여부 확인
        result = duckdb_conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name]
        ).fetchone()
        
        if result[0] > 0:
            return  # 이미 존재
        
        # PostgreSQL 스키마 기반으로 테이블 생성
        # 실제 구현에서는 스키마 매핑 필요
        logger.info(f"DuckDB 테이블 생성: {table_name}")
    
    async def _create_duckdb_indexes(self, duckdb_conn: duckdb.DuckDBPyConnection, table_name: str):
        """DuckDB 인덱스 생성"""
        # 주요 인덱스 생성
        index_definitions = {
            'trade_events': [
                "CREATE INDEX IF NOT EXISTS idx_te_symbol_time ON trade_events(symbol, time)",
                "CREATE INDEX IF NOT EXISTS idx_te_time ON trade_events(time)"
            ],
            'orders': [
                "CREATE INDEX IF NOT EXISTS idx_o_symbol_time ON orders(symbol, time)",
                "CREATE INDEX IF NOT EXISTS idx_o_status ON orders(status)"
            ],
            'price_1min': [
                "CREATE INDEX IF NOT EXISTS idx_p1m_symbol_time ON price_1min(symbol, timestamp)"
            ]
        }
        
        if table_name in index_definitions:
            for index_sql in index_definitions[table_name]:
                try:
                    duckdb_conn.execute(index_sql)
                except Exception:
                    pass  # 인덱스가 이미 존재하는 경우 무시
    
    def _update_sync_metadata(self, duckdb_conn: duckdb.DuckDBPyConnection, results: Dict[str, Any]):
        """동기화 메타데이터 업데이트"""
        # 메타데이터 테이블 생성
        duckdb_conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                sync_id INTEGER PRIMARY KEY,
                sync_timestamp TIMESTAMP,
                tables_synced INTEGER,
                total_rows BIGINT,
                sync_results JSON
            )
        """)
        
        # 메타데이터 삽입
        duckdb_conn.execute("""
            INSERT INTO sync_metadata (sync_timestamp, tables_synced, total_rows, sync_results)
            VALUES (?, ?, ?, ?)
        """, [
            datetime.now(),
            results['synced_tables'],
            results['total_rows'],
            str(results)
        ])


async def sync_data_to_analytics(
    db_manager: DatabaseManager,
    ibkr_manager: Any,
    redis_manager: RedisManager
) -> Dict[str, Any]:
    """데이터 동기화 작업 실행"""
    sync_manager = DataSyncManager(db_manager, redis_manager)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'operations': {}
    }
    
    # 1. PostgreSQL → DuckDB 동기화
    sync_results = await sync_manager.sync_postgresql_to_duckdb()
    results['operations']['sync'] = sync_results
    
    # 2. 동기화 정합성 검증
    verification = await sync_manager.verify_sync_integrity()
    results['operations']['verification'] = verification
    
    # 3. DuckDB 최적화
    optimization = await sync_manager.optimize_duckdb()
    results['operations']['optimization'] = optimization
    
    # 4. 분석용 뷰 생성/업데이트
    views = await sync_manager.generate_analytics_views()
    results['operations']['analytics_views'] = views
    
    # 요약
    results['summary'] = {
        'tables_synced': sync_results['synced_tables'],
        'total_rows_synced': sync_results['total_rows'],
        'integrity_issues': verification['issues_found'],
        'views_created': views['views_created'],
        'views_updated': views['views_updated']
    }
    
    logger.info(
        f"데이터 동기화 완료 - "
        f"테이블: {results['summary']['tables_synced']}, "
        f"행: {results['summary']['total_rows_synced']}"
    )
    
    return results