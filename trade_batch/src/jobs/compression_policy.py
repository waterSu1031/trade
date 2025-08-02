"""
TimescaleDB 압축 정책 관리 작업
- 오래된 데이터 압축
- 청크 관리 및 최적화
- 압축 통계 리포트
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncpg

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class CompressionPolicyManager:
    """TimescaleDB 압축 정책 관리 클래스"""
    
    def __init__(self, db_manager: DatabaseManager, redis_manager: RedisManager):
        self.db = db_manager
        self.redis = redis_manager
        
        # 압축 정책 설정 (테이블별 압축 대상 기간)
        self.compression_policies = {
            'price_1min': {'compress_after_days': 7},
            'price_5min': {'compress_after_days': 30},
            'price_1hour': {'compress_after_days': 90},
            'price_1day': {'compress_after_days': 365},
            'trade_events': {'compress_after_days': 30},
            'orders': {'compress_after_days': 30}
        }
    
    async def identify_compression_candidates(self) -> List[Dict[str, Any]]:
        """압축 대상 청크 확인"""
        logger.info("압축 대상 청크 확인 시작")
        
        candidates = []
        
        try:
            # TimescaleDB가 설치되어 있는지 확인
            timescaledb_installed = await self._check_timescaledb()
            if not timescaledb_installed:
                logger.warning("TimescaleDB가 설치되어 있지 않습니다")
                return candidates
            
            # 각 하이퍼테이블의 압축되지 않은 청크 조회
            for table_name, policy in self.compression_policies.items():
                compress_before = datetime.now() - timedelta(days=policy['compress_after_days'])
                
                # 압축 대상 청크 조회
                chunks = await self.db.fetch("""
                    SELECT 
                        ch.hypertable_name,
                        ch.chunk_name,
                        ch.range_start,
                        ch.range_end,
                        pg_size_pretty(ch.total_bytes) as size,
                        ch.total_bytes,
                        EXTRACT(EPOCH FROM (NOW() - ch.range_start))/86400 as age_days
                    FROM timescaledb_information.chunks ch
                    WHERE ch.hypertable_name = $1
                    AND ch.is_compressed = false
                    AND ch.range_start < $2
                    ORDER BY ch.range_start
                """, table_name, compress_before)
                
                for chunk in chunks:
                    candidates.append({
                        'hypertable_name': chunk['hypertable_name'],
                        'chunk_name': chunk['chunk_name'],
                        'range_start': chunk['range_start'],
                        'range_end': chunk['range_end'],
                        'size': chunk['size'],
                        'total_bytes': chunk['total_bytes'],
                        'age_days': float(chunk['age_days'])
                    })
                    
        except asyncpg.UndefinedTableError:
            logger.warning("TimescaleDB 정보 스키마가 없습니다")
        except Exception as e:
            logger.error(f"압축 대상 확인 실패: {e}")
        
        logger.info(f"압축 대상 청크 수: {len(candidates)}")
        return candidates
    
    async def compress_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """청크 압축 실행"""
        logger.info(f"{len(chunks)}개 청크 압축 시작")
        
        results = {
            'compressed': 0,
            'failed': 0,
            'space_saved_mb': 0,
            'details': []
        }
        
        for chunk in chunks:
            try:
                chunk_name = chunk['chunk_name']
                size_before = chunk['total_bytes']
                
                # 압축 실행
                start_time = datetime.now()
                await self.db.execute(f"SELECT compress_chunk('{chunk_name}')")
                compression_time = (datetime.now() - start_time).total_seconds()
                
                # 압축 후 크기 확인
                size_after = await self._get_chunk_size(chunk_name)
                space_saved = (size_before - size_after) / 1024 / 1024  # MB
                compression_ratio = 1 - (size_after / size_before) if size_before > 0 else 0
                
                results['compressed'] += 1
                results['space_saved_mb'] += space_saved
                
                detail = {
                    'chunk_name': chunk_name,
                    'hypertable': chunk['hypertable_name'],
                    'size_before_mb': size_before / 1024 / 1024,
                    'size_after_mb': size_after / 1024 / 1024,
                    'space_saved_mb': space_saved,
                    'compression_ratio': compression_ratio,
                    'compression_time_sec': compression_time,
                    'status': 'success'
                }
                
                results['details'].append(detail)
                
                logger.info(
                    f"청크 압축 완료 - {chunk_name}: "
                    f"{size_before/1024/1024:.1f}MB → {size_after/1024/1024:.1f}MB "
                    f"({compression_ratio*100:.1f}% 압축)"
                )
                
            except Exception as e:
                logger.error(f"청크 압축 실패 - {chunk['chunk_name']}: {e}")
                results['failed'] += 1
                results['details'].append({
                    'chunk_name': chunk['chunk_name'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
    
    async def drop_old_chunks(self, retention_days: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """오래된 청크 삭제"""
        logger.info("오래된 청크 삭제 시작")
        
        results = {
            'dropped': 0,
            'space_freed_mb': 0,
            'details': []
        }
        
        # 기본 보관 기간 설정
        if retention_days is None:
            retention_days = {
                'price_1min': 30,
                'price_5min': 90,
                'price_1hour': 180,
                'price_1day': 730,  # 2년
                'trade_events': 365,
                'orders': 365
            }
        
        for table_name, days in retention_days.items():
            try:
                drop_before = datetime.now() - timedelta(days=days)
                
                # 삭제 대상 청크 조회
                old_chunks = await self.db.fetch("""
                    SELECT 
                        chunk_name,
                        total_bytes,
                        range_start,
                        range_end
                    FROM timescaledb_information.chunks
                    WHERE hypertable_name = $1
                    AND range_end < $2
                    ORDER BY range_end
                """, table_name, drop_before)
                
                for chunk in old_chunks:
                    # 백업 필요 여부 확인
                    if await self._should_backup_chunk(chunk):
                        await self._backup_chunk(chunk)
                    
                    # 청크 삭제
                    await self.db.execute(f"SELECT drop_chunks('{table_name}', older_than => $1)", drop_before)
                    
                    space_freed = chunk['total_bytes'] / 1024 / 1024
                    results['dropped'] += 1
                    results['space_freed_mb'] += space_freed
                    
                    logger.info(f"청크 삭제: {chunk['chunk_name']} ({space_freed:.1f} MB)")
                
                if old_chunks:
                    results['details'].append({
                        'table': table_name,
                        'chunks_dropped': len(old_chunks),
                        'retention_days': days
                    })
                    
            except Exception as e:
                logger.error(f"{table_name} 청크 삭제 실패: {e}")
                results['details'].append({
                    'table': table_name,
                    'error': str(e)
                })
        
        return results
    
    async def get_compression_statistics(self) -> Dict[str, Any]:
        """압축 통계 조회"""
        logger.info("압축 통계 조회 시작")
        
        stats = {
            'summary': {},
            'by_table': {},
            'recommendations': []
        }
        
        try:
            # 전체 압축 통계
            summary = await self.db.fetchrow("""
                SELECT 
                    COUNT(*) as total_chunks,
                    COUNT(CASE WHEN is_compressed THEN 1 END) as compressed_chunks,
                    SUM(total_bytes) as total_bytes,
                    SUM(CASE WHEN is_compressed THEN total_bytes ELSE 0 END) as compressed_bytes,
                    SUM(CASE WHEN NOT is_compressed THEN total_bytes ELSE 0 END) as uncompressed_bytes
                FROM timescaledb_information.chunks
            """)
            
            if summary:
                total_gb = summary['total_bytes'] / 1024 / 1024 / 1024
                compressed_gb = summary['compressed_bytes'] / 1024 / 1024 / 1024
                uncompressed_gb = summary['uncompressed_bytes'] / 1024 / 1024 / 1024
                
                stats['summary'] = {
                    'total_chunks': summary['total_chunks'],
                    'compressed_chunks': summary['compressed_chunks'],
                    'uncompressed_chunks': summary['total_chunks'] - summary['compressed_chunks'],
                    'compression_ratio': summary['compressed_chunks'] / summary['total_chunks'] * 100 if summary['total_chunks'] > 0 else 0,
                    'total_size_gb': round(total_gb, 2),
                    'compressed_size_gb': round(compressed_gb, 2),
                    'uncompressed_size_gb': round(uncompressed_gb, 2),
                    'potential_savings_gb': round(uncompressed_gb * 0.7, 2)  # 예상 압축률 70%
                }
            
            # 테이블별 압축 통계
            table_stats = await self.db.fetch("""
                SELECT 
                    hypertable_name,
                    COUNT(*) as total_chunks,
                    COUNT(CASE WHEN is_compressed THEN 1 END) as compressed_chunks,
                    SUM(total_bytes) / 1024.0 / 1024.0 / 1024.0 as size_gb,
                    MIN(range_start) as oldest_data,
                    MAX(range_end) as newest_data
                FROM timescaledb_information.chunks
                GROUP BY hypertable_name
                ORDER BY size_gb DESC
            """)
            
            for table in table_stats:
                stats['by_table'][table['hypertable_name']] = {
                    'total_chunks': table['total_chunks'],
                    'compressed_chunks': table['compressed_chunks'],
                    'uncompressed_chunks': table['total_chunks'] - table['compressed_chunks'],
                    'size_gb': round(float(table['size_gb']), 2),
                    'oldest_data': table['oldest_data'].isoformat() if table['oldest_data'] else None,
                    'newest_data': table['newest_data'].isoformat() if table['newest_data'] else None,
                    'compression_ratio': table['compressed_chunks'] / table['total_chunks'] * 100 if table['total_chunks'] > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"압축 통계 조회 실패: {e}")
        
        # 권장사항 생성
        stats['recommendations'] = self._generate_compression_recommendations(stats)
        
        return stats
    
    async def optimize_compression_policies(self) -> Dict[str, Any]:
        """압축 정책 최적화"""
        logger.info("압축 정책 최적화 시작")
        
        results = {
            'policies_updated': 0,
            'policies_created': 0,
            'details': []
        }
        
        for table_name, policy in self.compression_policies.items():
            try:
                # 현재 압축 정책 확인
                existing_policy = await self.db.fetchrow("""
                    SELECT 
                        hypertable_name,
                        compress_after
                    FROM timescaledb_information.compression_settings
                    WHERE hypertable_name = $1
                """, table_name)
                
                if existing_policy:
                    # 정책 업데이트 필요 여부 확인
                    current_days = self._interval_to_days(existing_policy['compress_after'])
                    if current_days != policy['compress_after_days']:
                        await self.db.execute("""
                            SELECT alter_job(
                                (SELECT job_id FROM timescaledb_information.jobs 
                                 WHERE hypertable_name = $1 AND proc_name = 'policy_compression'),
                                config => jsonb_build_object('compress_after', $2::interval)
                            )
                        """, table_name, f"{policy['compress_after_days']} days")
                        
                        results['policies_updated'] += 1
                        logger.info(f"{table_name} 압축 정책 업데이트: {policy['compress_after_days']}일")
                else:
                    # 새 압축 정책 생성
                    await self.db.execute("""
                        SELECT add_compression_policy($1, $2::interval)
                    """, table_name, f"{policy['compress_after_days']} days")
                    
                    results['policies_created'] += 1
                    logger.info(f"{table_name} 압축 정책 생성: {policy['compress_after_days']}일")
                
                results['details'].append({
                    'table': table_name,
                    'compress_after_days': policy['compress_after_days'],
                    'status': 'updated' if existing_policy else 'created'
                })
                
            except Exception as e:
                logger.error(f"{table_name} 압축 정책 최적화 실패: {e}")
                results['details'].append({
                    'table': table_name,
                    'error': str(e)
                })
        
        return results
    
    async def _check_timescaledb(self) -> bool:
        """TimescaleDB 설치 여부 확인"""
        try:
            result = await self.db.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
                )
            """)
            return result
        except Exception:
            return False
    
    async def _get_chunk_size(self, chunk_name: str) -> int:
        """청크 크기 조회 (bytes)"""
        result = await self.db.fetchval("""
            SELECT pg_total_relation_size($1)
        """, chunk_name)
        return int(result) if result else 0
    
    async def _should_backup_chunk(self, chunk: Dict[str, Any]) -> bool:
        """청크 백업 필요 여부 확인"""
        # 중요 데이터나 특정 기간의 데이터는 백업
        # 예: 1년 이상 된 데이터 중 압축되지 않은 것
        age_days = (datetime.now() - chunk['range_start']).days
        return age_days > 365
    
    async def _backup_chunk(self, chunk: Dict[str, Any]):
        """청크 백업 (구현 필요)"""
        logger.info(f"청크 백업: {chunk['chunk_name']}")
        # 실제 백업 로직 구현 필요
        # 예: S3, 다른 테이블로 복사 등
        pass
    
    def _interval_to_days(self, interval: str) -> int:
        """PostgreSQL interval을 일수로 변환"""
        # 간단한 파싱 (예: "7 days" -> 7)
        parts = interval.split()
        if len(parts) >= 2 and parts[1].startswith('day'):
            return int(parts[0])
        return 0
    
    def _generate_compression_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """압축 권장사항 생성"""
        recommendations = []
        
        # 전체 압축률이 낮은 경우
        compression_ratio = stats['summary'].get('compression_ratio', 0)
        if compression_ratio < 50:
            recommendations.append(
                f"전체 압축률이 {compression_ratio:.1f}%로 낮습니다. "
                "압축 정책을 더 적극적으로 적용하는 것을 권장합니다."
            )
        
        # 압축되지 않은 데이터가 많은 경우
        uncompressed_gb = stats['summary'].get('uncompressed_size_gb', 0)
        if uncompressed_gb > 100:
            recommendations.append(
                f"압축되지 않은 데이터가 {uncompressed_gb:.1f}GB입니다. "
                f"약 {uncompressed_gb * 0.7:.1f}GB의 공간을 절약할 수 있습니다."
            )
        
        # 테이블별 권장사항
        for table_name, table_stats in stats['by_table'].items():
            if table_stats['compression_ratio'] < 30:
                recommendations.append(
                    f"{table_name} 테이블의 압축률이 {table_stats['compression_ratio']:.1f}%로 낮습니다. "
                    "압축 정책 검토가 필요합니다."
                )
        
        return recommendations


async def manage_compression_policy(
    db_manager: DatabaseManager,
    ibkr_manager: Any,
    redis_manager: RedisManager
) -> Dict[str, Any]:
    """압축 정책 관리 작업 실행"""
    manager = CompressionPolicyManager(db_manager, redis_manager)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'operations': {}
    }
    
    # 1. 압축 대상 확인
    candidates = await manager.identify_compression_candidates()
    results['operations']['candidates'] = {
        'count': len(candidates),
        'total_size_mb': sum(c['total_bytes'] / 1024 / 1024 for c in candidates)
    }
    
    # 2. 청크 압축 실행
    if candidates:
        compression_results = await manager.compress_chunks(candidates[:10])  # 한번에 최대 10개
        results['operations']['compression'] = compression_results
    
    # 3. 오래된 청크 삭제
    drop_results = await manager.drop_old_chunks()
    results['operations']['cleanup'] = drop_results
    
    # 4. 압축 통계
    stats = await manager.get_compression_statistics()
    results['statistics'] = stats
    
    # 5. 압축 정책 최적화
    optimization = await manager.optimize_compression_policies()
    results['operations']['optimization'] = optimization
    
    # Redis에 결과 캐시
    await redis_manager.set(
        'compression:last_run',
        results,
        expire=86400  # 24시간
    )
    
    logger.info("압축 정책 관리 완료")
    
    return results