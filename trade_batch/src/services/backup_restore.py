"""
백업 및 복원 서비스
- 데이터베이스 백업
- 포인트 인 타임 복구
- 백업 관리 및 정리
"""

import logging
import os
import gzip
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import subprocess

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class BackupRestoreService:
    """백업 및 복원 서비스"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        redis_manager: RedisManager,
        backup_dir: str = "/data/backups"
    ):
        self.db = db_manager
        self.redis = redis_manager
        self.backup_dir = Path(backup_dir)
        
        # 백업 디렉토리 생성
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 백업 설정
        self.retention_days = {
            'daily': 7,      # 일일 백업 7일 보관
            'weekly': 30,    # 주간 백업 30일 보관
            'monthly': 365   # 월간 백업 1년 보관
        }
        
        # 백업할 테이블 목록
        self.backup_tables = [
            'trades',
            'positions',
            'orders',
            'contracts',
            'market_data_1min',
            'market_data_5min',
            'market_data_1hour',
            'market_data_1day',
            'trade_events',
            'trading_hours',
            'market_holidays'
        ]
    
    async def create_backup(
        self,
        backup_type: str = 'daily',
        tables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """백업 생성"""
        start_time = datetime.now()
        logger.info(f"{backup_type} 백업 시작")
        
        # 백업 메타데이터
        backup_info = {
            'type': backup_type,
            'timestamp': start_time.isoformat(),
            'tables': tables or self.backup_tables,
            'status': 'in_progress',
            'files': []
        }
        
        # 백업 디렉토리 생성
        backup_date = start_time.strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / backup_type / backup_date
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. 스키마 백업
            schema_file = await self._backup_schema(backup_path)
            backup_info['files'].append(schema_file)
            
            # 2. 테이블 데이터 백업
            for table in backup_info['tables']:
                try:
                    file_path = await self._backup_table(table, backup_path)
                    backup_info['files'].append(file_path)
                except Exception as e:
                    logger.error(f"테이블 백업 실패 ({table}): {e}")
                    backup_info['errors'] = backup_info.get('errors', [])
                    backup_info['errors'].append(f"{table}: {str(e)}")
            
            # 3. 백업 메타데이터 저장
            metadata_file = backup_path / 'backup_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            # 4. 백업 압축
            if backup_type in ['weekly', 'monthly']:
                archive_path = await self._compress_backup(backup_path)
                backup_info['archive'] = str(archive_path)
            
            backup_info['status'] = 'completed'
            backup_info['duration'] = (datetime.now() - start_time).total_seconds()
            backup_info['size_mb'] = self._calculate_backup_size(backup_path)
            
            # Redis에 백업 정보 저장
            await self.redis.set(
                f"backup:{backup_type}:latest",
                backup_info,
                expire=86400
            )
            
            # 데이터베이스에 백업 기록
            await self._record_backup(backup_info)
            
            logger.info(
                f"{backup_type} 백업 완료: {len(backup_info['files'])} 파일, "
                f"{backup_info['size_mb']:.2f} MB"
            )
            
        except Exception as e:
            logger.error(f"백업 실패: {e}")
            backup_info['status'] = 'failed'
            backup_info['error'] = str(e)
            raise
        
        return backup_info
    
    async def _backup_schema(self, backup_path: Path) -> str:
        """스키마 백업"""
        schema_file = backup_path / 'schema.sql'
        
        # pg_dump를 사용한 스키마 백업
        cmd = [
            'pg_dump',
            self.db.connection_string,
            '--schema-only',
            '--no-owner',
            '--no-privileges',
            '-f', str(schema_file)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"스키마 백업 실패: {stderr.decode()}")
        
        return str(schema_file)
    
    async def _backup_table(self, table: str, backup_path: Path) -> str:
        """테이블 데이터 백업"""
        logger.debug(f"테이블 백업 시작: {table}")
        
        # CSV 형식으로 백업
        csv_file = backup_path / f"{table}.csv.gz"
        
        # COPY TO 명령 사용
        copy_query = f"""
            COPY (SELECT * FROM {table}) 
            TO STDOUT WITH CSV HEADER
        """
        
        # 데이터 스트리밍 및 압축
        with gzip.open(csv_file, 'wt') as gz_file:
            async for row in self.db.stream(copy_query):
                gz_file.write(row)
        
        logger.debug(f"테이블 백업 완료: {table}")
        return str(csv_file)
    
    async def _compress_backup(self, backup_path: Path) -> Path:
        """백업 압축"""
        archive_name = f"{backup_path.name}.tar.gz"
        archive_path = backup_path.parent / archive_name
        
        cmd = ['tar', '-czf', str(archive_path), '-C', str(backup_path.parent), backup_path.name]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        # 원본 디렉토리 삭제
        if archive_path.exists():
            import shutil
            shutil.rmtree(backup_path)
        
        return archive_path
    
    def _calculate_backup_size(self, backup_path: Path) -> float:
        """백업 크기 계산 (MB)"""
        total_size = 0
        
        if backup_path.is_file():
            total_size = backup_path.stat().st_size
        else:
            for file_path in backup_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)
    
    async def _record_backup(self, backup_info: Dict[str, Any]):
        """백업 기록 저장"""
        await self.db.execute("""
            INSERT INTO backup_history (
                backup_type, backup_date, status, 
                file_count, size_mb, duration_seconds,
                metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, 
            backup_info['type'],
            datetime.fromisoformat(backup_info['timestamp']),
            backup_info['status'],
            len(backup_info['files']),
            backup_info.get('size_mb', 0),
            backup_info.get('duration', 0),
            json.dumps(backup_info)
        )
    
    async def restore_backup(
        self,
        backup_date: str,
        tables: Optional[List[str]] = None,
        target_db: Optional[str] = None
    ) -> Dict[str, Any]:
        """백업 복원"""
        logger.info(f"백업 복원 시작: {backup_date}")
        
        restore_info = {
            'backup_date': backup_date,
            'tables': tables,
            'status': 'in_progress',
            'restored_tables': []
        }
        
        try:
            # 백업 찾기
            backup_path = self._find_backup(backup_date)
            if not backup_path:
                raise ValueError(f"백업을 찾을 수 없습니다: {backup_date}")
            
            # 백업 메타데이터 읽기
            metadata_file = backup_path / 'backup_metadata.json'
            with open(metadata_file, 'r') as f:
                backup_info = json.load(f)
            
            # 복원할 테이블 결정
            tables_to_restore = tables or backup_info['tables']
            
            # 1. 스키마 복원 (필요시)
            if target_db:
                await self._restore_schema(backup_path, target_db)
            
            # 2. 테이블 데이터 복원
            for table in tables_to_restore:
                try:
                    await self._restore_table(table, backup_path)
                    restore_info['restored_tables'].append(table)
                except Exception as e:
                    logger.error(f"테이블 복원 실패 ({table}): {e}")
                    restore_info['errors'] = restore_info.get('errors', [])
                    restore_info['errors'].append(f"{table}: {str(e)}")
            
            restore_info['status'] = 'completed'
            
            logger.info(
                f"백업 복원 완료: {len(restore_info['restored_tables'])} 테이블"
            )
            
        except Exception as e:
            logger.error(f"복원 실패: {e}")
            restore_info['status'] = 'failed'
            restore_info['error'] = str(e)
            raise
        
        return restore_info
    
    def _find_backup(self, backup_date: str) -> Optional[Path]:
        """백업 파일 찾기"""
        # 각 백업 타입별로 검색
        for backup_type in ['daily', 'weekly', 'monthly']:
            type_dir = self.backup_dir / backup_type
            if not type_dir.exists():
                continue
            
            # 정확한 날짜 매칭
            backup_path = type_dir / backup_date
            if backup_path.exists():
                return backup_path
            
            # 압축 파일 확인
            archive_path = type_dir / f"{backup_date}.tar.gz"
            if archive_path.exists():
                # 압축 해제
                extract_path = type_dir / backup_date
                self._extract_archive(archive_path, extract_path)
                return extract_path
        
        return None
    
    def _extract_archive(self, archive_path: Path, extract_path: Path):
        """압축 해제"""
        cmd = ['tar', '-xzf', str(archive_path), '-C', str(extract_path.parent)]
        subprocess.run(cmd, check=True)
    
    async def _restore_table(self, table: str, backup_path: Path):
        """테이블 데이터 복원"""
        csv_file = backup_path / f"{table}.csv.gz"
        
        if not csv_file.exists():
            raise FileNotFoundError(f"백업 파일을 찾을 수 없습니다: {csv_file}")
        
        # 기존 데이터 백업 (선택적)
        # await self.db.execute(f"CREATE TABLE {table}_backup AS SELECT * FROM {table}")
        
        # 데이터 삭제
        await self.db.execute(f"TRUNCATE TABLE {table}")
        
        # CSV 데이터 로드
        with gzip.open(csv_file, 'rt') as gz_file:
            copy_query = f"""
                COPY {table} FROM STDIN WITH CSV HEADER
            """
            await self.db.copy_from(gz_file, copy_query)
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """오래된 백업 정리"""
        logger.info("오래된 백업 정리 시작")
        
        cleanup_info = {
            'deleted_files': 0,
            'freed_space_mb': 0,
            'errors': []
        }
        
        now = datetime.now()
        
        for backup_type, retention_days in self.retention_days.items():
            type_dir = self.backup_dir / backup_type
            if not type_dir.exists():
                continue
            
            cutoff_date = now - timedelta(days=retention_days)
            
            for backup_item in type_dir.iterdir():
                try:
                    # 백업 날짜 파싱
                    backup_date_str = backup_item.stem.split('.')[0]
                    backup_date = datetime.strptime(backup_date_str, '%Y%m%d_%H%M%S')
                    
                    if backup_date < cutoff_date:
                        # 크기 계산
                        size_mb = self._calculate_backup_size(backup_item)
                        cleanup_info['freed_space_mb'] += size_mb
                        
                        # 삭제
                        if backup_item.is_file():
                            backup_item.unlink()
                        else:
                            import shutil
                            shutil.rmtree(backup_item)
                        
                        cleanup_info['deleted_files'] += 1
                        logger.debug(f"백업 삭제: {backup_item}")
                        
                except Exception as e:
                    logger.error(f"백업 정리 실패 ({backup_item}): {e}")
                    cleanup_info['errors'].append(str(e))
        
        logger.info(
            f"백업 정리 완료: {cleanup_info['deleted_files']} 파일, "
            f"{cleanup_info['freed_space_mb']:.2f} MB 확보"
        )
        
        return cleanup_info
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """백업 목록 조회"""
        backups = []
        
        for backup_type in ['daily', 'weekly', 'monthly']:
            type_dir = self.backup_dir / backup_type
            if not type_dir.exists():
                continue
            
            for backup_item in sorted(type_dir.iterdir(), reverse=True):
                try:
                    # 메타데이터 읽기
                    if backup_item.is_dir():
                        metadata_file = backup_item / 'backup_metadata.json'
                    else:
                        # 압축 파일인 경우 스킵 (간단히 처리)
                        continue
                    
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            info = json.load(f)
                    else:
                        # 기본 정보
                        info = {
                            'type': backup_type,
                            'timestamp': backup_item.stem,
                            'size_mb': self._calculate_backup_size(backup_item)
                        }
                    
                    backups.append(info)
                    
                except Exception as e:
                    logger.error(f"백업 정보 읽기 실패 ({backup_item}): {e}")
        
        return backups
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """백업 통계"""
        stats = {
            'total_backups': 0,
            'total_size_mb': 0,
            'by_type': {},
            'oldest_backup': None,
            'newest_backup': None
        }
        
        for backup_type in ['daily', 'weekly', 'monthly']:
            type_dir = self.backup_dir / backup_type
            if not type_dir.exists():
                continue
            
            type_stats = {
                'count': 0,
                'size_mb': 0
            }
            
            for backup_item in type_dir.iterdir():
                type_stats['count'] += 1
                type_stats['size_mb'] += self._calculate_backup_size(backup_item)
                
                # 날짜 추적
                try:
                    backup_date_str = backup_item.stem.split('.')[0]
                    backup_date = datetime.strptime(backup_date_str, '%Y%m%d_%H%M%S')
                    
                    if not stats['oldest_backup'] or backup_date < stats['oldest_backup']:
                        stats['oldest_backup'] = backup_date
                    
                    if not stats['newest_backup'] or backup_date > stats['newest_backup']:
                        stats['newest_backup'] = backup_date
                        
                except Exception:
                    pass
            
            stats['by_type'][backup_type] = type_stats
            stats['total_backups'] += type_stats['count']
            stats['total_size_mb'] += type_stats['size_mb']
        
        return stats


# 전역 서비스 인스턴스
backup_service_instance: Optional[BackupRestoreService] = None


async def initialize_backup_service(
    db_manager: DatabaseManager,
    redis_manager: RedisManager,
    backup_dir: Optional[str] = None
) -> BackupRestoreService:
    """백업 서비스 초기화"""
    global backup_service_instance
    
    if backup_service_instance is None:
        backup_service_instance = BackupRestoreService(
            db_manager, 
            redis_manager,
            backup_dir or "/data/backups"
        )
    
    return backup_service_instance


async def get_backup_service() -> Optional[BackupRestoreService]:
    """백업 서비스 인스턴스 반환"""
    return backup_service_instance